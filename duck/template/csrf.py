"""
Extension module for  CSRF utilities.
"""
from duck.http.middlewares.security.csrf import (
    get_csrf_token,
    add_new_csrf_cookie,
)


__all__ = ["get_csrf_token", "add_new_csrf_cookie"]
