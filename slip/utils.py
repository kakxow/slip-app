from typing import Tuple, Optional, Set, List
import re
import os
from datetime import datetime
from threading import Thread
from functools import partial
from time import time

from loguru import logger
import sqlalchemy.sql.functions as func

from db import Slip, try_query, check_exist, SessionCM


check_exist_link = partial(check_exist, Slip, 'file_link')


def dir_checker(
    s: str,
    years: Tuple[str],
    months: Optional[Tuple[str]] = None
) -> bool:
    """
    Checks if s is in years + months tuple or if it's a SAP code.
    You can define months to check explicitly, providing tuple months.

    Parameters
    ----------
    s
        String to check against years and month :obj:`tuple`.
    years
        Tuple of years in format '%Y'.
    months
        Optional tuple of month numbers in format '%m'.  If not set defaults to
        all months.

    Returns
    -------
    bool
        True if check is passed, False otherwise.

    Raises
    ------
    AttributeError
        If s is not :obj:`str`.
    TypeError
        If type(s) doesn't support len() function.

    """
    # Generate month numbers as formatted strings '##'.
    months = tuple(months) or tuple([f'{x:02}' for x in range(1, 13)])
    m_y = months + tuple(years)
    sap_code_pattern = r'^(([A-Z]\d{3})|([A-Z]{2}\d{2}))$'

    return (s in m_y) or re.match(sap_code_pattern, s, re.I)


def get_error_paths(err_log_path: str) -> Set[str]:
    """
    Collects paths for all files that caused an error during previous runs.

    Parameters
    ----------
    err_log_path
        Path to directory with logs.

    Returns
    -------
    Set[str]
        :obj:`set` of paths as :obj:`str`.

    Examples
    --------
    >>> get_error_paths('C:/Max/slip/slip/logs')
    set('//Msk-vm-slip/SLIP/BK01/2019/11/...', ...)

    """
    err_paths = {row.split()[0] for entry in os.scandir(err_log_path)
                 for row in open(entry.path)}
    return err_paths


def insert_db(dict_list: List[dict]):
    """
    Insert new slips to DB, using dicts from dict_list to create slips.

    Parameters
    ----------
    dict_list
        List of dicts, used to instantiate Slip.

    Returns
    -------
    None
        Only works with DB, nothing is returned.

    Raises
    ------
    OperationalError
        If DB is not available or busy for too long.

    """
    start = time()
    with SessionCM as session:
        slips = [Slip(**d) for d in dict_list]
        operation = session.bulk_save_objects(slips)
        try_query(session.commit, logger.warning)
    logger.debug(f'added in {time() - start} seconds.')


class Err:
    """
    Class for logging paths and error messages for files, that caused  an error
    during processing - opening, convertion to txt or regexp parsing.
    Generates name for new file using current timestamp,
    but doesn't create a file before first Err.write() call.

    Parameters
    ----------
    path
        Path for directory for creating error logs.

    """
    def __init__(self, path: str):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.path = path
        self.err_log_path = fr'{self.path}\errlog_{ts}.log'

    def write(self, *args: str):
        """
        Writes new line in a file, consisting of *args joined by one space.

        Parameters
        ----------
        *args
            Multiple :obj:`str` arguments to be written in a file.

        Returns
        -------
        None

        Examples
        --------
        >>> path = 'new_dir'
        >>> err = Err(path)
        >>> err.write(path, 'new log here!', 'yay!')
        $ ls /new_dir
        errlog_2019-12-13_09-58-35.log
        $ cat /new_dir/errlog_2019-12-13_09-58-35.log
        new_dir new log here! yay!

        """
        with open(self.err_log_path, 'a') as f:
            f.write(f'{" ".join(map(str, args))}\n')


def get_latest_date() -> float:
    """
    Finds latest addition to the DB

    Returns
    -------
        Timestamp for latest addition to DB.

    """
    with SessionCM as session:
        max_date = session.query(func.max(Slip.date)).scalar()
        return datetime.combine(max_date, datetime.min.time()).timestamp()


class Threads:
    """
    Class for manipulating multiple identical threads at once.
    On init creates several worker threads and saves them in internal state.

    Parameters
    ----------
    wrkr
        Function to be executed in a thread.
    thread_count
        Ammount of threads created.

    Returns
    -------
    None
        Thread's list is saved in internal "private" variable.

    """
    def __init__(self, wrkr: callable, thread_count: int = 8, **kwargs):
        self._threads = [Thread(target=wrkr, **kwargs) for i in range(thread_count)]

    def start(self):
        """
        Starts all threads created on init.

        Returns
            None

        Examples
        --------
        >>> threads = Threads(worker, 5, args=(1,2,3,))
        >>> threads.start()
        """
        for thread in self._threads:
            thread.start()

    def join(self, timeout: float = None):
        """
        Wait for all threads to stop working and join them.

        Parameters
        ----------
        timeout
            Timeout set to wait for threads to join.

        Returns
        -------
        None

        """
        for thread in self._threads:
            thread.join(timeout)
