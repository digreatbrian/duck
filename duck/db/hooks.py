"""
Database connection lifecycle hooks for Duck or Django views.

This module provides explicit, manually-invoked hooks to manage the database
connection lifecycle, mirroring Django's behavior. These are especially useful
in views, background tasks, or custom frameworks where automatic connection
cleanup may not apply or fine-grained control is required.

Supports both synchronous and asynchronous execution contexts.
"""

from django.core.exceptions import ImproperlyConfigured
from duck.contrib.sync import convert_to_async_if_needed


def close_old_connections():
    """
    Close any unusable or obsolete database connections.

    This function safely closes any DB connections that are:
    - broken,
    - timed out (exceeded CONN_MAX_AGE),
    - or associated with outdated threads or processes.

    Should be called at the start and end of a request or task, mimicking
    Django's `request_started` and `request_finished` behavior.
    """
    try:
        from django.db import connections
    
        for conn in connections.all(initialized_only=True):
            conn.close_if_unusable_or_obsolete()
    except (ImproperlyConfigured, KeyError):
        # User not using Django DB models, keyerror is raised when importing Django settings
        pass


def view_wrapper(handler):
    """
    Wraps a synchronous view or handler with DB connection lifecycle cleanup.

    Ensures `close_old_connections()` is called both before and after
    the view is executed.

    Args:
        handler (Callable): The synchronous view or function to wrap.

    Returns:
        Callable: A wrapped view that handles DB connection cleanup.
    """
    def wrapped(*args, **kwargs):
        close_old_connections()  # Before request
        try:
            return handler(*args, **kwargs)
        finally:
            close_old_connections()  # After request
    return wrapped


def async_view_wrapper(handler):
    """
    Wraps an asynchronous view or handler with DB connection lifecycle cleanup.

    Ensures `close_old_connections()` is called both before and after
    the view is executed, using `convert_to_async_if_needed()` to avoid
    blocking the event loop.

    Args:
        handler (Callable): The async view or function to wrap.

    Returns:
        Awaitable: A wrapped coroutine with DB connection cleanup.
    """
    close = convert_to_async_if_needed(close_old_connections, thread_sensitive=False)

    async def wrapped(*args, **kwargs):
        await close()  # Before request
        try:
            return await handler(*args, **kwargs)
        finally:
            await close()  # After request

    return wrapped
