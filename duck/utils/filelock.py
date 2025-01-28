"""
File lock capabilities module.
"""

import os
import time
import platform


if platform.system() == "Windows":
    import msvcrt
else:
    try:
        import fcntl
    except ImportError:
        fcntl = None


def lock_file(file_descriptor, retries=5, wait=1):
    """
    Lock file when modifying or accessing critical sections to avoid race conditions.
    """
    if platform.system() == "Windows":
        for _ in range(retries):
            try:
                msvcrt.locking(
                    file_descriptor.fileno(),
                    msvcrt.LK_NBLCK,
                    os.path.getsize(file_descriptor.name),
                )
                return
            except OSError:
                time.sleep(wait)
        raise BlockingIOError(
            f"Could not acquire lock after {retries} retries")
    else:
        if not fcntl:
            return
        for _ in range(retries):
            try:
                fcntl.flock(file_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                time.sleep(wait)
        raise BlockingIOError(
            f"Could not acquire lock after {retries} retries")


def unlock_file(file_descriptor):
    """
    Unlock a locked file.
    """
    if platform.system() == "Windows":
        msvcrt.locking(
            file_descriptor.fileno(),
            msvcrt.LK_UNLCK,
            os.path.getsize(file_descriptor.name),
        )
    else:
        fcntl.flock(file_descriptor, fcntl.LOCK_UN)


def open_and_lock(filename, mode="r+"):
    """
    Opens a file and acquires an exclusive lock.

    Args:
        filename: The name of the file to open.
        mode: The file open mode (default is 'r+').

    Returns:
        The opened file object.
    """
    fd = open(filename, mode)
    lock_file(fd)
    return fd
