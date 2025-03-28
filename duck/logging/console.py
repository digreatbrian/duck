"""
Console Logging Module - Log messages to console only!

This module provides utility functions to log messages to the console in a 
customizable format. It supports raw logging (plain messages) and formatted 
logging with prefixes, log levels, and optional colored output.

Features:
- Log messages with predefined log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- Support for colored output using ANSI escape codes.
- Customizable prefixes and colors for better message clarity.
- Automatically directs error-level logs to `stderr` and others to `stdout`.

Dependencies:
- Requires the `colorama` library for colored console output.

Constants:
- CRITICAL (int): Log level for critical messages.
- ERROR (int): Log level for error messages.
- WARNING (int): Log level for warning messages.
- INFO (int): Log level for informational messages.
- DEBUG (int): Log level for debug messages.

Functions:
- log_raw(msg, level, use_colors, custom_color): Logs a plain message.
- log(msg, prefix, level, use_colors, custom_color): Logs a formatted message with a prefix.

Example Usage:

```py
log("This is an info message.", level=INFO)
log("This is a warning!", level=WARNING)
log("This is an error!", level=ERROR)
log_raw("Raw debug message", level=DEBUG, use_colors=True, custom_color=Fore.MAGENTA)
```
"""

import sys

from colorama import Fore, Style

# Define log level constants
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10


def log_raw(
    msg: str,
    level: int = INFO,
    use_colors: bool = True,
    custom_color: str = None,
    end: str = "\n"):
    """
    Logs a raw message to the console without any modifications or prefixes.
    
    Args:
        msg (str): The message to log.
        level (int): The log level of the message (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
        use_colors (bool): Whether to apply color formatting to the message.
        custom_color (str): A custom ANSI color code for the message.
            Requires `use_colors` to be `True`.
        end (str): The log suffix, defaults to `"\n"` for newline.
    """
    std = sys.stderr if level in {ERROR, CRITICAL} else sys.stdout
    color = Style.RESET_ALL  # Default: no color

    # Determine color based on log level
    if level == ERROR or level == CRITICAL:
        color = Fore.RED
    elif level == WARNING:
        color = Fore.YELLOW
    elif level == DEBUG:
        color = Fore.CYAN

    # Apply custom color if provided
    if custom_color:
        color = custom_color

    # Print the message with or without color
    if use_colors:
        print(f"{color}{msg}{Style.RESET_ALL}", file=std, end=end)
    else:
        print(msg, file=std, end=end)


def log(
    msg: str,
    prefix: str = "[ * ]",
    level: int = INFO,
    use_colors: bool = True,
    custom_color: str = None,
    end: str = "\n"):
    """
    Logs a formatted message to the console with a prefix and optional colors.
    
    Args:
        msg (str): The message to log.
        prefix (str): A prefix to prepend to the message, e.g., '[ * ]', 'INFO', 'ERROR'.
        level (int): The log level of the message (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
        use_colors (bool): Whether to apply color formatting to the message.
        custom_color (str): A custom ANSI color code for the message.
            Requires `use_colors` to be `True`.
        end (str): The log suffix, defaults to `"\n"` for newline.
    """
    formatted_msg = f"{prefix} {msg}"
    std = sys.stderr if level in {ERROR, CRITICAL} else sys.stdout
    color = Style.RESET_ALL  # Default: no color

    # Determine color based on log level
    if level == ERROR or level == CRITICAL:
        color = Fore.RED
    elif level == WARNING:
        color = Fore.YELLOW
    elif level == DEBUG:
        color = Fore.CYAN

    # Apply custom color if provided
    if custom_color:
        color = custom_color

    # Print the message with or without color
    if use_colors:
        print(f"{color}{formatted_msg}{Style.RESET_ALL}", file=std, end=end)
    else:
        print(formatted_msg, file=std, end=end)
