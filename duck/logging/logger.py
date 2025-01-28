"""
Logging module for Duck with console color support using colorama module.

Notes:
	- Whenever DEBUG=True, redirect all console output if LOG_TO_FILE=True but ignore log_to_file argument which may be provided in functions 'log' and 'log_raw'.
"""
import os
import sys
import atexit
import datetime
import logging
import threading
import traceback

from typing import Callable
from colorama import Fore, Style

import duck.processes as processes
from duck.utils.importer import import_module_once
from duck.utils.path import paths_are_same
from duck.ansi import remove_ansi_escape_codes
from duck.settings import SETTINGS

# Info Logging Level
INFO = logging.INFO

# Debug Logging Level
DEBUG = logging.DEBUG

# Warning Logging Level
WARNING = logging.WARNING

# Critical Logging Level
CRITICAL = logging.CRITICAL

# Error Logging Level
ERROR = logging.ERROR

globals = import_module_once("duck.globals")


def get_current_log_file() -> str:
    """
    This function retrieves the current log file in LOGGING_DIR which depends on datetime.

    Returns:
        str: The path to the current log file.

    Raises:
        FileNotFoundError: If the log directory does not exist.
    """
    if "--reload" in sys.argv:
        # this is a reload so lets use latest log file because its a continuation
        try:
            return processes.get_process_data("main").get("log_file")
        except KeyError:
            # failed to retrieve last log file used by the main app.
            pass

    log_file_format = SETTINGS["LOG_FILE_FORMAT"]
    logging_dir = SETTINGS["LOGGING_DIR"]
    current_log_file = os.environ.get("DUCK_CURRENT_LOG_FILE")

    if not os.path.isdir(logging_dir):
        raise FileNotFoundError("Directory to save log files doesn't exist.")

    if current_log_file:
        return current_log_file

    # Format the new log file name with the given LOG_FILE_FORMAT
    now = datetime.datetime.utcnow()
    formatted_time = log_file_format.format(
        day=now.day,
        month=now.month,
        year=now.year,
        hours=now.hour,
        minutes=now.minute,
        seconds=now.second,
    )
    new_log_file = os.path.join(logging_dir, formatted_time + ".log")

    with open(new_log_file, "ab"):
        # Create the new log file.
        pass

    # record current log file in duck.globals
    os.environ["DUCK_CURRENT_LOG_FILE"] = new_log_file
    return new_log_file


def get_current_log_file_fd():
    """
    Get the opened file descriptor for the current log file in bytes append mode.
    """
    filepath = (get_current_log_file()
                )  # refetches the current log file, maybe it has changed.

    if hasattr(globals, "current_log_file_fd"):
        file_fd = globals.current_log_file_fd
        if paths_are_same(file_fd.name, filepath):
            return file_fd
    file_fd = open(filepath, "ab")
    globals.current_log_file_fd = file_fd
    return file_fd


def redirect_console_output():
    """
    Redirects all console output (stdout and stderr) to a log file, i.e current log file.

    This function locks sys.stdout and sys.stderr so that they cannot be modified by another process.

    """
    if not SETTINGS["LOG_TO_FILE"] or SETTINGS["SILENT"]:
        # Do not log to any file if logging is disabled in settings.
        return

    # Redirect stdout and stderr to a file
    file_fd = get_current_log_file_fd()
    # Record default write methods
    default_stdout_write = sys.stdout.write
    default_stderr_write = sys.stderr.write
    # Create a lock for synchronized writing
    write_lock = threading.Lock()

    def stdout_write(data):
        """
        Writes data to both the default stdout and the specified file.

        Args:
            data (str): The data to be written.
        """
        cleaned_data = remove_ansi_escape_codes(
            [data])[0]  # remove ansi escape codes if present
        with write_lock:
            file_fd.write(bytes(cleaned_data, "utf-8"))
            file_fd.flush()  # Ensure data is written to the file immediately
            default_stdout_write(data)

    def stderr_write(data):
        """
        Writes data to both the default stderr and the specified file.

        Args:
            data (str): The data to be written.
        """
        cleaned_data = remove_ansi_escape_codes(
            [data])[0]  # remove ansi escape codes if present
        with write_lock:
            file_fd.write(bytes(cleaned_data, "utf-8"))
            file_fd.flush()  # Ensure data is written to the file immediately
            default_stderr_write(data)

    # Assign new write methods
    sys.stdout.write = stdout_write
    sys.stderr.write = stderr_write


def get_latest_log_file():
    """
    Returns the latest created file in LOGGING_DIR.
    """
    logging_dir = SETTINGS["LOGGING_DIR"]
    if os.path.isdir(logging_dir):
        scan = {i.stat().st_ctime: i for i in os.scandir(logging_dir)}
        return scan.get(sorted(scan)[-1]) if scan else None


def expand_exception(e: Exception) -> str:
    """
    Expands an exception to show the traceback and more information.

    Args:
        e (Exception): The exception to expand.

    Returns:
        str: The expanded exception.
    """
    return "".join(
        traceback.format_exception(type(e), value=e, tb=e.__traceback__))


def handle_exception(func: Callable):
    """
    Decorator that executes a function or callable. If an exception occurs, logs the exception to console and file or both.

    Args:
        func (Callable): The function to be decorated.

    Returns:
        callable: The wrapped function with exception handling.
    """

    def wrapper(*args, **kwargs):
        """
        Wrapper function for the callable provided to the decorator.

        Args:
            *args: Variable length argument list for the callable.
            **kwargs: Arbitrary keyword arguments for the callable.

        Returns:
            Any: The return value of the callable, if no exception occurs.
        """

        try:
            return func(*args, **kwargs)
        except Exception as e:
            exception = f"Exception: {str(e)}"

            if SETTINGS["VERBOSE_LOGGING"]:
                exception = expand_exception(e)

            if not SETTINGS["SILENT"]:
                log_raw(exception)

            if SETTINGS["LOG_TO_FILE"]:
                # Write the expanded exception to a file.
                log_to_file(exception)

    return wrapper


@handle_exception
def log_exception(e: Exception):
    """
    Logs exception to console and file or both.
    """
    raise e


def log_to_file(data: str, end: str = "\n") -> str | bytes:
    """
    This writes data to the log file.

    Args:
        data (str | bytes): Data to write.
        end (str | bytes): The suffix to add to data before writting to file.

    Returns:
         str | bytes: Data that was written
    """
    log_file_fd = get_current_log_file_fd()
    data = data.encode("utf-8") if isinstance(data, str) else data
    data += end.encode("utf-8") if isinstance(end, str) else end
    log_file_fd.write(data)
    log_file_fd.flush()
    return data


def log_raw(
    msg: str,
    level: int = INFO,
    use_colors: bool = True,
    custom_color: str = None,
    end: str = "\n",
):
    """
    Logs a message to console as it is without any modifications.

    Args:
        msg (str): The message to log.
        level (int): The log level of the message.
        use_colors (bool): Whether to log message with some colors, i.e. red for Errors, Yellow for warnings, etc.
        custom_color (string): The custom color to use, .e.g '\x1b[31m'.
        The use colors argument is required to use custom color.
        end (str): The log suffix, defaults to "\n" for newline.
    """
    log_level = level
    std = sys.stdout

    if SETTINGS["SILENT"]:
        if SETTINGS["LOG_TO_FILE"]:
            cleaned_data = remove_ansi_escape_codes(
                [msg])[0]  # remove ansi escape codes if present
            log_to_file(cleaned_data, end=end)
        return

    if log_level == ERROR or log_level == CRITICAL:
        std = sys.stderr
        color = Fore.RED
    elif log_level == WARNING:
        color = Fore.YELLOW
    elif log_level == INFO:
        color = Style.RESET_ALL  # default
    elif log_level == DEBUG:
        color = Fore.CYAN

    if custom_color:
        color = custom_color

    if use_colors:
        colored_msg = f"{color}{msg}{Style.RESET_ALL}"
        print(colored_msg, file=std, end=end)
    else:
        print(msg, file=std, end=end)


def log(
    msg: str,
    prefix: str = "[ * ]",
    level: int = INFO,
    use_colors: bool = True,
    custom_color: str = None,
    end: str = "\n",
):
    """
    Pretty log a message to console.

    Args:
        msg (str): The message to log.
        prefix (str): The prefix to prepend to the message.
        level (int): The log level of the message.
        use_colors (bool): Whether to log message with some colors, ie, red for Errors, Yellow for warnings, etc
        custom_color (string): The custom color to use, .e.g '\x1b[31m'. Arg use_colors is required to use custom color.
        end (str): The log suffix, defaults to "\n" for newline.
    """
    formatted_msg = f"{prefix} {msg}"
    log_level = level
    color = Fore.WHITE  # Default color for normal message
    std = sys.stdout

    if SETTINGS["SILENT"]:
        if SETTINGS["LOG_TO_FILE"]:
            cleaned_data = remove_ansi_escape_codes(
                [msg])[0]  # remove ansi escape codes if present
            log_to_file(cleaned_data, end=end)
        return

    if log_level == ERROR or log_level == CRITICAL:
        std = sys.stderr
        color = Fore.RED
    elif log_level == WARNING:
        color = Fore.YELLOW
    elif log_level == INFO:
        color = Style.RESET_ALL  # default
    elif log_level == DEBUG:
        color = Fore.CYAN

    if custom_color:
        color = custom_color

    if use_colors:
        colored_msg = f"{color}{formatted_msg}{Style.RESET_ALL}"
        print(colored_msg, file=std, end=end)
    else:
        print(msg, file=std, end=end)


try:
    if SETTINGS["LOG_TO_FILE"]:
        atexit.register(
            get_current_log_file_fd().close)  # close log file at exit.
except Exception:
    pass
