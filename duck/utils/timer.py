"""
Timer Utility module for scheduling callables.
"""

import threading
import time


class TimerThreadPool:
    all: list = []
    """List of all threads added through the use of any Timer class"""


class Timer:
    """
    Timer Utility for callables scheduling.
    """

    all_threads: list[threading.Thread] = []
    """List of all alive or dead threads scheduled"""

    @classmethod
    def _schedule_interval(cls, function: callable, seconds: int):
        while True:
            time.sleep(seconds)
            function()

    @classmethod
    def _schedule(cls, function: callable, seconds: int):
        time.sleep(seconds)
        function()

    @classmethod
    def schedule(cls, function: callable, seconds: int):
        th = threading.Thread(target=cls._schedule, args=[function, seconds])
        th.start()
        cls.all_threads.append(th)
        TimerThreadPool.all.append(th)

    @classmethod
    def schedule_interval(cls, function: callable, seconds: int):
        th = threading.Thread(target=cls._schedule_interval,
                              args=[function, seconds])
        th.start()
        cls.all_threads.append(th)
        TimerThreadPool.all.append(th)


class OverlappingTimer:
    """
    This Timer Utility stops all running threads scheduled with the use of this class and then runs the new schedule in a new thread.

    NOTE: This only share threads from an initialized object.
    """

    def __init__(self):
        self.all_threads: list[threading.Thread] = (
            [])  # List of all threads scheduled

    def get_running_thread(self):
        """
        Get the latest thread that was created when using any of the methods (schedule or schedule_interval)

        WARNING: If the latest thread is done running, None will be returned
        """
        if not self.all_threads:
            return None
        last_thread = self.all_threads[-1]
        return last_thread if last_thread.is_alive() else None

    @staticmethod
    def _schedule_interval(function: callable, seconds: int) -> None:
        while True:
            time.sleep(seconds)
            function()

    @staticmethod
    def _schedule(function: callable, seconds: int) -> None:
        time.sleep(seconds)
        function()

    def schedule(self, function: callable, seconds: int):
        th = threading.Thread(target=self._schedule, args=[function, seconds])

        # stop all threads that were created by using schedule method
        for thread in self.all_threads:
            if thread.is_alive():
                try:
                    thread._stop()
                except Exception:
                    try:
                        thread.join()
                    except Exception:
                        pass
        th.start()
        self.all_threads.append(th)
        TimerThreadPool.all.append(th)

    def schedule_interval(self, function: callable, seconds: int):
        th = threading.Thread(target=self._schedule_interval,
                              args=[function, seconds])
        # stop all threads that were created by using schedule_interval method
        for thread in self.all_threads:
            if thread.is_alive():
                try:
                    thread._stop()
                except Exception:
                    try:
                        thread.join()
                    except Exception:
                        pass
        th.start()
        self.all_threads.append(th)
        TimerThreadPool.all.append(th)


class SharedOverlappingTimer:
    """
    This Timer Utility stop all running threads scheduled with the use of this class and then runs the new schedule in a new thread

    NOTE: This shares all threads from this class
    """

    all_threads: list[threading.Thread] = []
    """List of all threads scheduled"""

    def get_running_thread(self):
        """
        Get the latest thread that was created when using any of the methods (schedule or schedule_interval)

        WARNING: If the latest thread is done running, None will be returned
        """
        if not self.all_threads:
            return None
        last_thread = self.all_threads[-1]
        return last_thread if last_thread.is_alive() else None

    @staticmethod
    def _schedule_interval(function: callable, seconds: int) -> None:
        while True:
            time.sleep(seconds)
            function()

    @staticmethod
    def _schedule(function: callable, seconds: int) -> None:
        time.sleep(seconds)
        function()

    def schedule(self, function: callable, seconds: int):
        th = threading.Thread(target=self._schedule, args=[function, seconds])

        # stop all threads that were created by using schedule method
        for thread in self.all_threads:
            if thread.is_alive():
                try:
                    thread._stop()
                except Exception:
                    try:
                        thread.join()
                    except Exception:
                        pass
        th.start()
        type(self).all_threads.append(th)
        TimerThreadPool.all.append(th)

    def schedule_interval(self, function: callable, seconds: int):
        th = threading.Thread(target=self._schedule_interval,
                              args=[function, seconds])
        # stop all threads that were created by using schedule_interval method
        for thread in self.all_threads:
            if thread.is_alive():
                try:
                    thread._stop()
                except Exception:
                    try:
                        thread.join()
                    except Exception:
                        pass
        th.start()
        type(self).all_threads.append(th)
        TimerThreadPool.all.append(th)
