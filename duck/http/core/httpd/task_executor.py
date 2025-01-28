"""
Module containing the classes for executing request handling threads or coroutines.

Notes:
    The method 'execute' will be called every time a request has been accepted ready to be handled.
"""
import asyncio
import threading

from typing import (
    Optional, Union,
    Callable, Coroutine,
)
from duck.utils.importer import x_import


def trio_execute(task):
    """
    Execute a coroutine using trio.
    """
    try:
        import trio
        trio.run(task)
    except ImportError:
        raise ImportError("Trio library could not be resolved, ensure trio is installed or install it using 'pip install trio' ")


def curio_execute(task):
    """
    Execute a coroutine using curio library.
    """
    try:
        import curio
        curio.run(task)
    except ImportError:
        raise ImportError("Curio library could not be resolved, ensure curio is installed or install it using 'pip install curio' ")


class RequestHandlingExecutor:
    def  __init__(self, async_executor: Optional[Union[str, Callable]] = None, thread_executor: Optional[Union[str, Callable]] = None):
        """
        Initialize the RequestHandlingExecutor class.
        
        Args:
            async_executor (Optional[Union[str, Callable]]): The callable or string representing an importable object responsible for executing asynchronous coroutines.
            thread_executor (Optional[Union[str, Callable]]): The callable or string representing an importable object responsible for executing threads.
        """
        if isinstance(async_executor, str):
            async_executor = x_import(async_executor)
        
        if isinstance(thread_executor, str):
             thread_executor = x_import(thread_executor)
        
        assert callable(async_executor) or async_executor is None, "The async executor should be a callable responsible for executing asynchronous tasks (or None)."
        assert callable(thread_executor) or thread_executor is None, "The thread executor should be a callable responsible for executing threads (or None)."
        
        self.async_executor = async_executor
        self.thread_executor = thread_executor
    
    def execute(self, task: Union[threading.Thread, Coroutine]):
        """
        Entry method for executing request handling tasks (threads or coroutines.)
        """
        if isinstance(task, threading.Thread):
            if self.thread_executor:
                self.thread_executor(task)
            else:
                task.start() # fallback to execute thread manually
        else:
            if self.async_executor:
                self.async_executor(task)
            else:
                asyncio.run(task()) # fallback to execute task using asyncio
