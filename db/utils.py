from typing import Union, List, Tuple, Callable
from contextlib import contextmanager
from time import sleep
import random

from sqlalchemy.exc import OperationalError
import sqlalchemy.orm as orm

from .db import Base, Session


def try_query(
    query: Callable,
    logger: Callable = None,
    tries: int = 60,
    sleep_time: float = 1.0
) -> Union[bool, None, List[Tuple[str]]]:
    """
    Tries to execute query until no OperatinalError is raised or tries exceeded.
    Logs failure with provided logger, otherwise prints to stdout.

    Parameters
    ----------
    query
        SQLAlchemy Query() with method (scalar, fetch_all etc) to execute.
    logger
        Logger to log errors with.
    tries
        Number of tries before giving up.
    sleep_time
        Delay between tries.

    Returns
    -------
    Union[bool, None, List[Tuple[str]], str]
        Returns query result, depends on the query.

    Raises
    ------
    OperationalError
        If DB is not available or busy for too long.

    """
    err_counter = 0
    for err_counter in range(60):
        try:
            result = query()
        except OperationalError:
            sleep(random.uniform(0, sleep_time))
        else:
            break
    else:
        if logger:
            try:
                logger('DB timeout.')
            except TypeError:
                print('DB timeout.')
        raise
    return result


class SessionContextManager:
    """
    Class for using sessions as context manager.  Takes sessionmaker as
    parameter on init, returns session on enter and closes session on exit.

    Parameters
    ----------
    sess
        SQLAlchemy sessionmaker object.

    """
    def __init__(self, sess: orm.sessionmaker):
        self._sess = sess

    def __enter__(self) -> orm.Session:
        """
        Creates new session with passed sessionmaker on enter.

        Returns:
        orm.Session
            Session object to use in queries and other sqlalchemy activities.

        """
        self._s = self._sess()
        return self._s

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Closes session on exit.

        Parameters
        ----------
        exc_type
            Type of exception, that caused to exit with-statement early.
        exc_value
            Value of exception, that caused to exit with-statement early.
        traceback
            traceback of exception, that caused to exit with-statement early.

        Returns
        -------
        None

        """
        self._s.close()


@contextmanager
def session_manager(sess: orm.sessionmaker) -> orm.Session:
    """
    Context manager for SQLAlchemy sessions.

    Parameters
    ----------
    sess
        SQLAlchemy.orm sessionmaker

    Returns
    -------
    SQLAlchemy.orm.Session
        New session to work with DB, defined with sessionmaker.

    """
    session = sess()
    try:
        yield session
    finally:
        session.close()


def check_exist(
    model: Base,
    column_name: str,
    value: str,
    logger: Callable = None,
) -> bool:
    """
    Checks if value exists in a column column_name in a table for model
    in DB with Session.

    Parameters
    ----------
    model
        Model/table object to search for value.
    logger
        Logger if needed.
    column_name
        Name of the column in model/table.
    value
        Value to search for in column column_name

    Returns
    -------
    bool
        True if value exists in model.column_name, False otherwise.

    """
    session = Session()
    column = getattr(model, column_name)
    q = session.query(column).filter(column == value).scalar
    res = try_query(q, logger, tries=200)
    session.close()
    # Should explicitly delete session to not cause any problems when threading.
    del session
    return res
