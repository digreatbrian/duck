"""
Module containing RequestHandlingExecutor which handles execution of async coroutines and threaded tasks efficiently.
"""

import asyncio
import threading
import concurrent.futures

from typing import Optional, Union, Callable, Coroutine, Any
from collections import deque
from duck.utils.importer import x_import


def trio_execute(task, event_loop):
    """Execute a coroutine using Trio with the provided event loop."""
    try:
        import trio
        if event_loop is None:
            raise ValueError("Trio requires an event loop.")
        trio.run(task)
    except ImportError:
        raise ImportError("Trio library not found. Install with 'pip install trio'.")


def curio_execute(task, event_loop):
    """Execute a coroutine using Curio with the provided event loop."""
    try:
        import curio
        if event_loop is None:
            raise ValueError("Curio requires an event loop.")
        curio.run(task)
    except ImportError:
        raise ImportError("Curio library not found. Install with 'pip install curio'.")


def asyncio_execute(task, event_loop):
    """Execute an asyncio coroutine with a thread-safe event loop."""
    if event_loop is None or event_loop.is_closed():
        raise ValueError("Asyncio requires an active event loop.")
    
    future = asyncio.run_coroutine_threadsafe(task(), event_loop)
    return future.result()  # Wait for result safely


class RequestHandlingExecutor:
    """Handles execution of async coroutines and threaded tasks efficiently."""
    
    def __init__(
        self,
        async_executor: Optional[Union[str, Callable]] = None,
        thread_executor: Optional[Union[str, Callable]] = None,
        max_workers: int = 50,  # Limits number of concurrent threads
    ):
        """
        Initialize RequestHandlingExecutor.

        Args:
            async_executor (Optional[Union[str, Callable]]): Function or import path for async execution.
            thread_executor (Optional[Union[str, Callable]]): Function or import path for thread execution.
            max_workers (int): Max threads for ThreadPoolExecutor.
        """
        self.async_executor = x_import(async_executor) if isinstance(async_executor, str) else async_executor
        self.thread_executor = x_import(thread_executor) if isinstance(thread_executor, str) else thread_executor

        assert callable(self.async_executor) or self.async_executor is None, "Async executor must be callable or None."
        assert callable(self.thread_executor) or self.thread_executor is None, "Thread executor must be callable or None."

        # Start the asyncio event loop in a background thread
        self._asyncio_loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_asyncio_loop, daemon=True)
        self._loop_thread.start()

        # Thread pool for CPU-bound tasks
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

        # Deque for handling async tasks
        self._task_queue = deque()
        self._task_queue_lock = threading.Lock()

        # Start task consumer
        self._asyncio_loop.call_soon_threadsafe(asyncio.create_task, self._task_consumer())

    def _run_asyncio_loop(self):
        """Run the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self._asyncio_loop)
        self._asyncio_loop.run_forever()

    async def _task_consumer(self):
        """Async consumer to process tasks from the queue."""
        while True:
            task = None
            with self._task_queue_lock:
                if self._task_queue:
                    task = self._task_queue.popleft()
            if task:
                await task()
            await asyncio.sleep(0.01)  # Yield control to the event loop

    def on_thread_task_complete(self, future):
         try:
             future.result()
         except Exception as e:
             if hasattr(future, 'name'):
                 e.args = (f"{e.args[0]}: [{future.name}]", )
             raise e # reraise error, it will be handled
        
    def execute(self, task: Union[Callable, Coroutine]):
        """
        Execute a task using threads or async execution.
        - Async tasks are added to a queue for non-blocking execution.
        - CPU-bound tasks run in a thread pool.
        """
        if isinstance(task, threading.Thread):
            # Handle CPU-bound tasks via thread pool
            if self.thread_executor:
                self.thread_executor(task)
            else:
                future = self._thread_pool.submit(task.run)  # Optimized thread execution
                future.name = task.name
                future.add_done_callback(self.on_thread_task_complete)
        else:
            # Handle async tasks by adding them to the asyncio queue
            if self.async_executor:
                # If async_executor is provided, use it to execute
                if self.async_executor == trio_execute:
                    self._asyncio_loop.call_soon_threadsafe(trio_execute, task, self._asyncio_loop)
                elif self.async_executor == curio_execute:
                    self._asyncio_loop.call_soon_threadsafe(curio_execute, task, self._asyncio_loop)
                else:
                    self._asyncio_loop.call_soon_threadsafe(self.async_executor, task)
            else:
                # Add task directly to asyncio queue for non-blocking execution
                with self._task_queue_lock:
                    self._task_queue.append(task)
