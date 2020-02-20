import queue
import os
from typing import List, Tuple, Optional, Iterator, Set

from sqlalchemy.exc import OperationalError
from loguru import logger

from .threadsafe_gen import scantree_check_
from .utils import dir_checker, Err, get_error_paths, get_latest_date
from .utils import Threads, insert_db, check_exist_link
from .parser import parse_slip


kill_ = False


def main_single_table(
    rootdir: str,
    years: Tuple[str],
    thread_count: int = 4,
    months: Optional[List[str]] = None,
    filter_ctime: bool = False,
) -> None:
    """
    Iterates through all files in rootdir and it's subdirectories,
    parses valid for addition files and adds content to database.

    Parameters
    ----------
    rootdir
        Path to root directory for search.
    years
        Filter subdirectories, skipping all years except stated in years tuple.
    thread_count
        Number of threads for concurrency.
    months
        Filter subdirectories, skipping all months except stated in months tuple.
        If set left aside or set to None - no filtering for months is performed.
    filter_ctime
        Flag to filter files for os.stat().st_ctime or not.

    Return
    ------
    None
        Adds all results to database, returns nothing.

    """
    # Counters.
    counter_add = counter_error = 0
    counter = []
    c = 0
    q_dicts = queue.Queue()  # Queue with parsed dicts to process and add commit.
    stopper: List[str] = []  # List where workers puts something when generator quits.
    t: List[dict] = []  # Temporary list of dicts to create Slips and insert to db.
    global kill_  # Workers check this every tick and dies when kill_ is True.

    thread_count = min(thread_count, 8)
    gen = scantree_check_(rootdir, dir_checker, years, months)
    # Creating error log.
    path_to_logs = os.path.join(os.path.dirname(__file__), 'logs')
    err = Err(path_to_logs)
    logger.info('Get error paths.')
    paths = get_error_paths(err.path)
    latest_date = get_latest_date() if filter_ctime else None

    try:
        worker_args = (
            gen,
            stopper,
            counter,
            paths,
            filter_ctime,
            latest_date,
            q_dicts,
        )
        threads = Threads(worker, thread_count, args=worker_args)
        threads.start()

        logger.info(f'Start running through directories.')
        while len(stopper) < thread_count:
            t, counter_add, counter_error = \
                t_loop(q_dicts, counter_add, counter_error, err)
            # Commit new entries to DB.
            # May be in a thread?
            try:
                insert_db(t)
            except OperationalError:
                logger.critical('DB is broken.')
                break
            c += len(counter)
            counter.clear()
            s = f'Ran {c:10d}\t' \
                f'Added {counter_add:10d}\t' \
                f'Errors: {counter_error:10d}'
            logger.info(s)
        else:
            logger.critical('Stop in stopper')
    except (KeyboardInterrupt, OperationalError) as e:
        logger.critical(e)

    kill_ = True
    threads.join()
    logger.info('Threads joint.')


def t_loop(
    q_dicts: queue.Queue,
    counter_add: int,
    counter_error: int,
    err: Err,
) -> Tuple[List[dict], int, int]:
    """
    The key loop of main thread in this module.
    Gets dictionaries from the queue and after several checks appends it
    to resulting list together with appropriate model.  Resulting list length
    is not more than 100 to reduce number of DB commits.
    Also takes counters as arguments and returns as part of a tuple.

    Parameters
    ----------
    q_dicts
        Queue populated by workerks in other threads with results from parser.
    counter_add
        Counter for added records.
    counter_error
        Counter for records with regexp errrors.
    err:
        Any object with .write() method, that accepts multiple arguments.
        All regexp errors and paths are written there.

    Returns
    -------
    Tuple[List[Tuple[Base, dict]], int, int]
        Returns :obj:`tuple` of :obj:`list` and two counters (:obj:`int`).
        List contains dictionary for instantiation of models.Slip.

    """
    t = []
    while len(t) < 100:
        # Add results to t from queue in a cycle, break if empty.
        try:
            res = q_dicts.get(timeout=10)
        except queue.Empty:
            break
        error = res.pop('error', None)
        path = res['file_link']
        if not error:
            res.pop('operation_num')
            t.append(res)
            counter_add += 1
        else:
            err.write(path, error)
            counter_error += 1
            logger.debug(f'{path}, {error}')
        q_dicts.task_done()
    return t, counter_add, counter_error


@logger.catch
def worker(
    gen: Iterator[os.DirEntry],
    stopper: List[str],
    counter: list,
    error_paths: Set[str],
    filter_ctime: bool,
    latest_date: Optional[float],
    q_dicts: queue.Queue,
    time_margin: float = 100000.0
) -> None:
    """
    Worker for multithreading.  Gets new path from gen, checks it,
    parses it if all checks passed and puts result in the queue.

    Parameters
    ----------
    gen
        Generator/iterator to pull new os.DirEntries from.
    stopper
        External list to keep track of alive threads.
        Every worker adds an item when encounters an error.
    counter
        External list, to which every worker adds 1 for every checked entry.
    error_paths
        Set of file paths from error logs.
    filter_ctime
        Flag to check creation time of entries.
    latest_date
        Timestamp to check creation time against.
    q_dicts
        Queue for results.
    time_margin
        Maximum time difference between ctime and latest_date, in seconds.

    Returns
    -------
    None
        Returns nothing, puts result to the queue.

    """
    if filter_ctime and not latest_date:
        raise ValueError('If filter_dates is set to True - provide latest_date.')
    global kill_
    while not kill_:
        try:
            entry = next(gen)
        except StopIteration:
            # When generator gets empty, go out of loop
            # and increase stopper counter.
            stopper.append('Stop')
            logger.info('StopIteration')
            break
        except FileNotFoundError as e:
            # Shit happens, mon.
            logger.warning(e)
            continue
        except OSError as e:
            # This is the end.
            logger.warning(e)
            break
        pth = entry.path
        counter.append(1)
        if not entry.name.endswith('pdf'):
            continue
        if pth.count('\\') < 5 or pth in error_paths:
            logger.debug(f'bad path {pth}')
            # Bad path or path is in error logs.
            continue
        if filter_ctime:
            diff = latest_date - entry.stat().st_ctime
            if diff < time_margin:
                logger.debug(f'slip is earlier than needed {pth}')
                continue
        # Check DB if pth is in DB, and if not - process it.
        try:
            path_in_db = check_exist_link(pth)
        except Exception:
            logger.critical('DB is broken.')
            stopper.append('Stop')
            break
        if not path_in_db:
            q_dicts.put(parse_slip(pth))
