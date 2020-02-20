from threading import Lock
import os
from typing import Union, Iterator, Generator


class ThreadsafeIter:
    """
    Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.

    Parameters
    ----------
    it
        Iterator or generator to be guarded from race conditions.

    """
    def __init__(self, it: Union[Iterator, Generator]):
        self.it = it
        self.lock = Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return self.it.__next__()


def threadsafe_generator(gen: Generator):
    """
    A decorator that takes a generator function and makes it thread-safe.

    Parameters
    ----------
    gen
        Generator to be guarded from race conditions.

    Returns
    -------
    ThreadsafeIter
        Same generator, but now with serialized call to next() method.

    """
    def g(*args, **kwargs):
        return ThreadsafeIter(gen(*args, **kwargs))
    return g


@threadsafe_generator
def scantree_check_(path: str, chck: callable, *args, **kwargs):
    """
    Recursively yields DirEntry objects for given directory.
    Also checks all sub-directories with chck function, called with *args and **kwargs.

    Parameters
    ----------
    path
        Root path where to start searching for files.
    chck
        Function for checking subdirectory names.
    *args
        Additional arguments to pass in chck.

    Yields
    ------
    os.DirEntry
        Next file in path directory or it's subdirectories.

    """
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            if chck(entry.name, *args):
                yield from scantree_check_(entry.path, chck, *args, **kwargs)
        else:
            yield entry
