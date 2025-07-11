"""
Sync + Asynchronous helper tools.

This module provides utility functions to convert between synchronous and asynchronous 
functions using asgiref's sync_to_async and async_to_sync, with optional LRU caching 
to improve performance in high-frequency conversion scenarios.
"""

from typing import Callable, Any
from functools import lru_cache
from asyncio import iscoroutine
from asgiref.sync import (
    sync_to_async as _sync_to_async,
    async_to_sync as _async_to_sync,
    iscoroutinefunction,
    SyncToAsync,
    AsyncToSync,
)


__all__ = [
    "iscoroutine",
    "iscoroutinefunction",
    "sync_to_async",
    "async_to_sync",
    "convert_to_async_if_needed",
    "convert_to_sync_if_needed",
]


@lru_cache(maxsize=256)
def sync_to_async(func: Callable, thread_sensitive: bool = True) -> Callable:
    """
    Converts a synchronous function into an asynchronous one, with optional LRU caching.

    Args:
        func (Callable): The synchronous function to convert.
        thread_sensitive (bool): Whether to run the function in a thread sensitive context.
            Default is True, which means the function will run in the same thread if called 
            from a sync context (useful for thread-local storage).

    Returns:
        Callable: An asynchronous version of the input function.
    """
    return _sync_to_async(func, thread_sensitive=thread_sensitive)


@lru_cache(maxsize=256)
def async_to_sync(func: Callable) -> Callable:
    """
    Converts an asynchronous function into a synchronous one, with optional LRU caching.

    Args:
        func (Callable): The asynchronous function to convert.

    Returns:
        Callable: A synchronous version of the input async function.
    """
    return _async_to_sync(func)


def convert_to_async_if_needed(func: Callable, thread_sensitive: bool = True) -> Callable:
    """
    Automatically converts a function to asynchronous if it's synchronous,
    or returns it unchanged if it's already a coroutine function.

    Args:
        func (Callable): The function to convert if needed.
        thread_sensitive (bool): Whether to run the function in a thread sensitive context.
            Default is True, which means the function will run in the same thread if called 
            from a sync context (useful for thread-local storage) only if needed.

    Returns:
        Callable: An async function if `func` was sync, otherwise the original.
    """
    if iscoroutinefunction(func) or isinstance(func, SyncToAsync):
        return func
    func = sync_to_async(func, thread_sensitive=thread_sensitive)
    return func


def convert_to_sync_if_needed(func: Callable) -> Callable:
    """
    Automatically converts a coroutine function to synchronous if it's asynchronous,
    or returns it unchanged if it's already a non-coroutine function.

    Args:
        func (Callable): The function to convert if needed.
        
    Returns:
        Callable: A sync function if `func` was async, otherwise the original.
    """
    if not iscoroutinefunction(func) or isinstance(func, AsyncToSync):
        return func
    return async_to_sync(func)
