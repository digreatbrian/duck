"""
Module for creating and running base applications using Duck framework.

This module provides the core application class, `App`, for setting up and running a Duck-based web application. It supports various features including HTTP and HTTPS servers, Django server integration, automation dispatching, SSL management, and more. The application can be configured to handle incoming requests, enforce HTTPS, and run various background processes such as a file reloader and automation scripts.

Key Features:
- **HTTP/HTTPS Server**: Configures and starts an HTTP or HTTPS server based on application settings.
- **Django Integration**: Can forward requests to a Django server, with support for custom commands on startup.
- **SSL Management**: Checks and manages SSL certificates for secure communication.
- **Force HTTPS**: Redirects all HTTP traffic to HTTPS when enabled.
- **Automations**: Supports running automations during runtime.
- **File Reloader**: Watches for file changes in the application for dynamic reloading (in DEBUG mode).
- **Port Management**: Ensures that application ports are not used by other applications.
- **Signal Handling**: Gracefully handles termination signals (e.g., Ctrl-C) to stop the application.

Attributes:
    - `DUCK_HOME_DIR`: The application's home directory.
    - `DJANGO_HOST`: The address and port for the Django server.
    - `DOMAIN`: The domain name for the application.
    - `DJANGO_SERVER_WAIT_TIME`: The time to wait for the Django server to start.
    - `server_up`: Whether the main application server is running.
    - `django_server_up`: Whether the Django server is running and responsive.

Methods:
    - `run()`: Starts the application and its associated services.
    - `stop()`: Stops the application and terminates the program.
    - `restart()`: Restarts the application.
    - `start_server()`: Starts the main application server.
    - `start_django_server()`: Starts the Django server and uses Duck as a reverse proxy.
    - `start_force_https_app()`: Starts the HTTPS redirection server.
    - `start_ducksight_reloader()`: Starts the file watcher for dynamic reloading.
    - `start_automations_dispatcher()`: Starts the automation dispatcher.
    - `register_signals()`: Registers the signal handler for appropriate signals.
    - `on_app_start()`: Event called when the application setup is complete.
    
The `App` class is intended for creating a primary application instance, and it ensures that only a single instance of the application is allowed to run at a time. For running smaller microservices or apps, the `MicroApp` class should be used instead.

Exceptions handled:
    - `ApplicationError`: Raised if more than one application instance is created.
    - `SettingsError`: Raised if there are misconfigurations in the application settings.
    - `SSLError`: Raised if SSL certificate or private key is missing or invalid.
"""

from duck.app.app import App
from duck.app.microapp import MicroApp

__all__ = ["App", "MicroApp"]
