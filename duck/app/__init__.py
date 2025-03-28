"""
Module for creating and running base applications using Duck framework.

This module provides the core application classes, `App` and `MicroApp`, for setting up and running a Duck-based web application. It supports various features including HTTP and HTTPS servers, Django server integration, automation dispatching, SSL management, and more. The application can be configured to handle incoming requests, enforce HTTPS, and run various background processes such as a file reloader and automation scripts.

Key Features:
- **HTTP/HTTPS Server**: Configures and starts an HTTP or HTTPS server based on application settings.
- **Django Integration**: Can forward requests to a Django server, with support for custom commands on startup.
- **SSL Management**: Checks and manages SSL certificates for secure communication.
- **Force HTTPS**: Redirects all HTTP traffic to HTTPS when enabled.
- **Automations**: Supports running automations during runtime.
- **Ducksight Reloader**: Watches for file changes in the application for dynamic reloading (in DEBUG mode).
- **Port Management**: Ensures that application ports are not used by other applications.
- **Signal Handling**: Gracefully handles termination signals (e.g., Ctrl-C) to stop the application.

"""

from duck.app.app import App
from duck.app.microapp import MicroApp

__all__ = ["App", "MicroApp"]
