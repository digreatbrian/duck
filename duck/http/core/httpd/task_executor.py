"""
Module containing RequestHandlingExecutor which handles execution of async coroutines and threaded tasks efficiently.
"""
import os
import psutil
import asyncio
import platform
import threading
import concurrent.futures

from typing import (
    Optional,
    Union,
    Callable,
    Coroutine,
    Any,
)
from collections import deque

from duck.contrib.sync import (
    iscoroutine,
    iscoroutinefunction,
)
from duck.settings import SETTINGS


def get_max_workers() -> int:
    """
    Dynamically calculate a safe max_workers value for ThreadPoolExecutor,
    based on CPU count, available memory, stack size, and current system usage.
    Works cross-platform (Linux, Windows, macOS). No root required.

    Returns:
        int: Suggested max_workers value (min 8, max 2000)
    """

    # --- System info ---
    cpu_count = os.cpu_count() or 1

    try:
        total_memory = psutil.virtual_memory().total
        used_memory = psutil.virtual_memory().used
        available_memory = psutil.virtual_memory().available
    except Exception:
        total_memory = 4 * 1024**3  # fallback to 4 GB
        available_memory = total_memory * 0.5  # fallback to 50% available

    try:
        all_threads = sum(p.num_threads() for p in psutil.process_iter())
    except Exception:
        all_threads = 500  # fallback if counting fails

    # --- Estimate stack size ---
    try:
        if platform.system() == "Windows":
            stack_size = 1 * 1024 * 1024  # 1 MB
        else:
            import resource
            stack_size = resource.getrlimit(resource.RLIMIT_STACK)[0]
            if stack_size <= 0 or stack_size > 1024**3:
                stack_size = 8 * 1024 * 1024  # fallback
    except Exception:
        stack_size = 8 * 1024 * 1024  # fallback

    # --- Limits ---
    # 1. CPU limit
    cpu_limit = cpu_count * 4

    # 2. Memory limit (use only portion of available RAM)
    mem_limit = int(available_memory * 0.75 / stack_size)

    # 3. Adjust for running threads (leave room)
    thread_adjustment = max(0, 2000 - all_threads)

    # --- Final decision ---
    max_workers = min(cpu_limit, mem_limit, thread_adjustment, 2000)
    return max(8, max_workers)


class RequestHandlingExecutor:
    """
    Handles execution of async coroutines and threaded tasks efficiently.
    """
    
    def __init__(
        self,
        max_workers: int = None,  # Limits number of concurrent threads
    ):
        """
        Initialize RequestHandlingExecutor.

        Args:
            max_workers (int): Max threads for ThreadPoolExecutor. If None, the number will be dynamically calculated.
        """
        # Thread pool for CPU-bound tasks
        self.max_workers = max_workers or get_max_workers()
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(self.max_workers)
        
        if SETTINGS['ASYNC_HANDLING']:
            # Deque for handling async tasks
            self._task_queue = deque()
            self._task_queue_lock = threading.Lock()
            
            def start_async(task_consumer):
                loop = asyncio.new_event_loop()
                loop.run_until_complete(task_consumer)
                
            # Start the asynchronous runner in a background thread
            self._async_thread = threading.Thread(target=start_async, args=([self._task_consumer()]))
            self._async_thread.start()
            
    async def _task_consumer(self):
        """
        Async consumer to process tasks from the queue.
        """
        while True:
            task = None
            await asyncio.sleep(0.000001) # Yield control to event loop.
            with self._task_queue_lock:
                if self._task_queue:
                    task = self._task_queue.popleft()
            if task:
                if iscoroutinefunction(task):
                    await task()
                elif iscoroutine(task):
                    await task
                else:
                    raise TypeError("Task must be a coroutine or coroutine function")
                    
    def on_thread_task_complete(self, future):
         try:
             future.result()
         except Exception as e:
             if hasattr(future, 'name'):
                 if not e.args:
                     e.args = ((),)
                 e.args = (f"{e.args[0]}: [{future.name}]", )
             raise e # reraise error, it will be handled
        
    def execute(self, task: Union[Callable, Coroutine]):
        """
        Execute a task using threads or async execution.
        - Async tasks are added to a queue for non-blocking execution.
        - CPU-bound tasks run in a thread pool.
        
        Args:
            task (Union[Callable, Coroutine]): This accepts any callable, coroutine or coroutine function. If
            coroutine function is parsed, it should accept no arguments.
        """
        if iscoroutinefunction(task) or iscoroutine(task):
            # Handle async tasks by adding them to the queue
            # Add task directly to asyncio queue for non-blocking execution
            with self._task_queue_lock:
                self._task_queue.append(task)
        
        else:
            # Handle CPU-bound tasks via thread pool
            try:
                future = self._thread_pool.submit(task)  # Optimized thread execution
            except RuntimeError as e:
                if "cannot schedule new futures after interpreter shutdown" in str(e):
                    raise RuntimeError(f"{e}. This maybe caused when `disable_ipc_handler` is set to True for the main application instance.") from e
            future.name = getattr(task, 'name', repr(task))
            future.add_done_callback(self.on_thread_task_complete)
        