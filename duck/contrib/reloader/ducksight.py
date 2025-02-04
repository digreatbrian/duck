"""
Duck's own reloader module.
"""
import os
import time
import signal
import fnmatch
import platform
import traceback
import subprocess
import multiprocessing

import duck.processes as processes

from threading import Timer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from duck.settings import SETTINGS
from duck.utils import ipc
from duck.utils.filelock import open_and_lock
from duck.utils.path import joinpaths
from duck.logging import logger


# Define the base directory for the application
BASE_DIR = str(SETTINGS["BASE_DIR"]).rstrip("/")
PYTHON_PATH = str(SETTINGS["PYTHON_PATH"])


def set_state(state: str) -> str:
    """
    Set the state of the DuckSightReloader in a file.

    Args:
        state (str): The new state, either 'alive' or 'dead'.

    Returns:
        str: Path to the state file.

    Raises:
        TypeError: If the provided state is not 'alive' or 'dead'.
    """
    state_file = joinpaths(BASE_DIR, ".ducksight-state")

    if state not in {"alive", "dead"}:
        raise TypeError("State should be one of ['alive', 'dead']")

    mode = "w" if os.path.isfile(state_file) else "x"

    with open_and_lock(state_file, mode) as fd:
        fd.write(state)

    return state_file


def get_state() -> str:
    """
    Retrieve the state of the DuckSightReloader from the state file.

    Returns:
        str: Current state of the reloader ('dead' or 'alive').
    """
    state_file = joinpaths(BASE_DIR, ".ducksight-state")

    if not os.path.isfile(state_file):
        return "dead"

    with open_and_lock(state_file) as fd:
        return fd.read()


def _cleanup_current_webserver() -> list:
    """
    Cleans up the current Duck server if running. (Useful before server restart as new process is spawned on same address and port.)

    Returns:
        data (dict): The current Duck application server process data.

    Raises:
        RuntimeError: If there was a failure in retrieving the process data respective file.
    """
    data = None
    try:
        data = processes.get_process_data("main")
        server_sys_argv = data.get("sys_argv")
        if not server_sys_argv:
            raise RuntimeError(
                "Failed to retrieve Duck application process sys.argv, ensure the app is running."
            )
    except KeyError:
        raise RuntimeError(
            "Failed to retrieve Duck application process data, ensure the app is running."
        )
    try:
        with ipc.get_writer() as writer:
            writer.write_message(
                "prepare-restart"
            )  # send message to main application process for cleanup
    finally:
        time.sleep(1)  # wait a second for server to finish cleanup
    return data


def _restart_webserver():
    """
    Restart the webserver by terminating the current process and re-executing the command.
    """
    server_data = _cleanup_current_webserver() # cleanup the current running server
    server_sys_argv = server_data.get("sys_argv")  # sys.argv for the cleaned webserver

    def get_server_command() -> list:
        """
        Builds and returns the command to start a new Duck webserver instance, using arguments from the current instance.
        """
        if (server_sys_argv[0].endswith(".py") and not "runserver" in server_sys_argv):
            # server was started directly from py file
            cmd = [
                PYTHON_PATH,
                "-m",
                "duck",
                "runserver",
                "--file",
                server_sys_argv[0],
                "--reload",
            ]
        else:
            # server was started through terminal
            cmd = server_sys_argv[:]
            if "--reload" not in cmd:
                cmd.extend(["--reload"])
        return cmd

    # continue to re-start server again
    cmd = get_server_command()
    p = subprocess.run(cmd)  # replace the current process


def restart_webserver():
    """
    Restart the webserver gracefully, logging any errors during the process.
    """
    try:
        _restart_webserver()
    except Exception as e:
        logger.log_raw("".join(
            traceback.format_exception(type(e), e, e.__traceback__)))


def _start_reloader():
    reloader = DuckSightReloader(BASE_DIR)
    reloader.run()


def start_ducksight_reloader_process():
    """
    Start the DuckSightReloader in a new background process.

    Behavior:
        - If there is another instance of DuckSightReloader process running, there will be an attempt to stop that process.

    Returns:
        multiprocess.Process: The process object for the reloader.
    """
    process = multiprocessing.Process(target=_start_reloader, daemon=False)
    process.start()
    processes.set_process_data("ducksight-reloader", {
        "pid": process.pid,
        "start_time": time.time()
    })
    return process


def stop_ducksight_reloader_process():
    """
    Stop the DuckSightReloader process by setting its state to 'dead'.
    """
    set_state("dead")


def is_process_running(pid: int) -> bool:
    """
    Checks if process is running.
    """
    try:
        # Sending signal 0 to the process ID
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def ducksight_reloader_process_alive() -> bool:
    """
    Check if the DuckSightReloader process is running.

    Returns:
        bool: True if the process is running, False otherwise.
    """
    state = get_state() == "alive"
    try:
        pid = processes.get_process_data("ducksight-reloader").get("pid")
        # check if process is running
        live_result = is_process_running(pid)
        if live_result == state:
            return state
        else:
            set_state("alive" if live_result else "dead")
            return live_result
    except KeyError:
        pass


class DuckSightReloader:
    """
    Observes local file changes and triggers a server restart when necessary.

    Args:
        watch_dir (str): The directory to monitor for changes.
    """

    def __init__(self, watch_dir: str):
        timeout = SETTINGS.get("AUTO_RELOAD_POLL", 1.0)

        if platform.system() == "Windows":
            timeout = max(timeout,
                          2.0)  # Minimum timeout for stability on Windows

        self.observer = Observer(timeout=timeout)
        self.watch_dir = watch_dir

    def run(self):
        """
        Start the file observer and handle events until interrupted.
        """
        try:
            # Stop any other running reloader process
            set_state("dead")  # first method to trigger a stop

            try:
                # second method to kill old reloader process if still running.
                current_pid = os.getpid()
                old_pid = processes.get_process_data("ducksight-reloader").get(
                    "pid")
                if not old_pid == current_pid:
                    os.kill(old_pid, signal.SIGKILL)
            except (KeyError, ProcessLookupError):
                pass
            finally:
                # wait for old reloader process to terminate if running.
                time.sleep(1)

            event_handler = Handler()
            self.observer.schedule(event_handler,
                                   self.watch_dir,
                                   recursive=True)
            self.observer.start()
            set_state("alive")

            while get_state() == "alive":
                time.sleep(0.1)
        except KeyboardInterrupt:
            set_state("dead")
        finally:
            set_state("dead")
            self.observer.stop()
            if self.observer.is_alive():
                self.observer.join()


class Handler(FileSystemEventHandler):
    """
    Event handler to respond to file changes by restarting the server.

    Listens for modifications, creations, deletions, and moves of `.py` files.
    """

    def __init__(self, debounce_interval=1.0):
        """
        Initialize the file event handler with a debounce mechanism.

        Args:
            debounce_interval (float): The time (in seconds) to wait before restarting the server.
        """
        super().__init__()
        self.debounce_interval = debounce_interval
        self.restart_timer = None
        self.latest_event = None
        self.restarting = False

    def on_any_event(self, event):
        # Only process relevant events for `.py` files
        watch_files = SETTINGS["AUTO_RELOAD_WATCH_FILES"]
        src_file = str(event.src_path)
        file_allowed = False

        for pattern in watch_files:
            if fnmatch.fnmatch(src_file, pattern):
                file_allowed = True
                break

        if event.is_directory or not file_allowed:
            # ignore file, we dont need to watch for any of its changes.
            return

        if event.event_type not in {"created", "modified", "deleted", "moved"}:
            return  # Ignore unwanted events

        # Store the latest event details
        self.latest_event = event

        # Cancel any pending restart timers
        if self.restart_timer:
            self.restart_timer.cancel()

        # Schedule a new restart with a delay
        self.restart_timer = Timer(self.debounce_interval,
                                   self._trigger_restart)
        self.restart_timer.start()

    def _trigger_restart(self):
        """
        Perform the server restart and log the specific file change event.
        """
        if self.restarting:
            return  # Prevent overlapping restarts

        if self.latest_event:
            self.restarting = True
            action = self.latest_event.event_type
            if action == "moved":
                src_path = self.latest_event.src_path
                dest_path = getattr(self.latest_event, "dest_path", "unknown")
                logger.log_raw(
                    f"\nFile {src_path} was moved to {dest_path}, reloading...",
                    custom_color=logger.Fore.YELLOW,
                )
            else:
                file_path = self.latest_event.src_path
                logger.log_raw(
                    f"\nFile {file_path} was {action}, reloading...",
                    custom_color=logger.Fore.YELLOW,
                )
            restart_webserver()
            self.restarting = False
            self.latest_event = None  # Clear the latest event after handling


if __name__ == "__main__":
    multiprocessing.freeze_support()
