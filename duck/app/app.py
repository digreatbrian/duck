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
    - `DJANGO_ADDR`: The address and port for the Django server.
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
import os
import sys
import json
import time
import signal
import socket
import threading

import duck.processes as processes
import duck.contrib.reloader.ducksight as reloader

from typing import Optional
from duck.app.microapp import HttpsRedirectMicroApp
from duck.exceptions.all import (
    ApplicationError,
    SettingsError,
    SSLError,
)
from duck.http.core.httpd.servers import (
    HttpServer,
    HttpsServer,
)
from duck.settings import SETTINGS
from duck.settings.loaded import (
    AUTOMATION_DISPATCHER,
    AUTOMATIONS,
)
from duck.utils.timer import (
    Timer,
    TimerThreadPool,
)
from duck.utils import ipc
from duck.utils.path import url_normalize
from duck.utils.port_recorder import PortRecorder
from duck.backend.django import bridge
from duck.logging import logger
from duck.meta import Meta
from duck.setup import setup
from duck.art import display_duck_art
from duck.version import version


def is_ipv6(ip_address: str) -> bool:
    """
    Check if the provided IP address is a valid IPv6 address.
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip_address)
        return True
    except socket.error:
        return False


def is_ipv4(ip_address: str) -> bool:
    """
    Check if the provided IP address is a valid IPv4 address.
    """
    try:
        socket.inet_pton(socket.AF_INET, ip_address)
        return True
    except socket.error:
        return False


def is_domain(name) -> bool:
    """
    Check if the provided name is a valid domain name.
    """
    return all(
        [len(part) <= 63 and part.isalnum() for part in name.split(".")])


class App:
    """Initializes and configures Duck application."""

    DUCK_HOME_DIR: str = os.path.abspath(".")
    """
	Specifies the application's home directory.
	"""

    DJANGO_ADDR: tuple[str, int] = None
    """
	Specifies the host address and port for the Django server. 
	For enhanced security, ensure that uncommon ports are used.
	"""

    DOMAIN: str = None
    """
    Domain for the application used in building the application absolute uri
    """

    DJANGO_SERVER_WAIT_TIME: int = SETTINGS["DJANGO_SERVER_WAIT_TIME"]
    """
	Time in seconds to wait before checking if the Django server is up and running.
	
	This variable is used to periodically verify the server's status during the initial startup or 
	maintenance routines, ensuring that the server is ready to handle incoming requests.
	"""

    __instances__: int = 0

    def __init__(
        self,
        addr: str = "localhost",
        port: int = 8000,
        domain: str = None,
        uses_ipv6: bool = False,
        no_checks: bool = False,
    ):

        if uses_ipv6 and not is_ipv6(addr) and not str(addr).isalnum():
            raise ApplicationError(
                "Argument uses_ipv6=True yet addr provided is not a valid IPV6 ip address."
            )

        if not uses_ipv6 and not is_ipv4(addr) and not str(addr).isalnum():
            raise ApplicationError(
                "Argument addr is not a valid IPV4 ip address.")

        self._restart_success = False  # state on whether last restart operation has been successfull
        self.addr = addr
        self.port = port
        self.uses_ipv6 = uses_ipv6
        self.is_domain_set = True if domain else False
        self.no_checks = no_checks

        # set appropriate domain
        self.domain = domain or addr if not uses_ipv6 else f"[{addr}]"

        if is_ipv4(self.domain) and self.domain.startswith(
                "0"
        ):  # ip "0.x.x.x" not allowed as domain because most browsers cannot resolve this.
            self.domain = "localhost"

        # continue
        self.enable_https: bool = SETTINGS["ENABLE_HTTPS"]
        self.DOMAIN = self.domain
        self.SETTINGS = SETTINGS
        self.DJANGO_ADDR = addr, SETTINGS["DJANGO_BIND_PORT"]
        self.force_https = SETTINGS["FORCE_HTTPS"]
        self.use_django = SETTINGS["USE_DJANGO"]
        self.run_automations = SETTINGS["RUN_AUTOMATIONS"]

        setup()  # setup duck environment and the entire application.

        self.run_checks() if not no_checks else None  # run some checks

        # add app port to used ports
        PortRecorder.add_new_occupied_port(port, f"{self}")

        # vital objects creation
        if SETTINGS["FORCE_HTTPS"]:
            force_https_addr = addr
            force_https_port = SETTINGS["FORCE_HTTPS_BIND_PORT"]

            self.force_https_app = HttpsRedirectMicroApp(
                location_url=self.absolute_uri,
                addr=force_https_addr,
                port=force_https_port,
                enable_https=False,
                parent_app=self,
                no_logs=True,
                uses_ipv6=uses_ipv6,
            )  # create force https app

        if SETTINGS["RUN_AUTOMATIONS"]:
            self.automations_dispatcher = AUTOMATION_DISPATCHER(self)
            for trigger, automation in AUTOMATIONS:
                self.automations_dispatcher.register(
                    trigger, automation)  # register trigger and automation

        if self.enable_https:
            self.server = HttpsServer(
                (addr, port),
                application=self,
                uses_ipv6=uses_ipv6,
            )
        else:
            self.server = HttpServer(
                (addr, port),
                application=self,
                uses_ipv6=uses_ipv6,
            )

        def start_server():
            """Starts Duck application main server."""
            no_logs = False
            domain = self.domain
            self.server.start_server(no_logs, domain)

        def start_django_server():
            """Starts django app server"""
            host = self.DJANGO_ADDR
            self._django_server_process = bridge.start_django_app(
                *host, uses_ipv6=uses_ipv6)

        def start_force_https():
            """Starts app for redirecting non encrypted traffic to main app using https"""
            if self.force_https:
                self.force_https_app.run()

        def start_automations_dispatcher():
            """Starts automations dispatcher for running and managing automations on runtime"""
            if self.run_automations:
                self.automations_dispatcher.start()

        # essential vital threads
        self.duck_server_thread = threading.Thread(target=start_server)
        self.django_server_thread = threading.Thread(
            target=start_django_server)

        # other essentials
        self.force_https_thread = threading.Thread(target=start_force_https)
        self.automations_dispatcher_thread = threading.Thread(
            target=start_automations_dispatcher)

        # set app instances count
        if type(self).__instances__ == 0:
            type(self).__instances__ += 1
        else:
            raise ApplicationError(
                "Cannot create more apps, Only single main application is allowed. "
                "Consider using a MicroApp instead")

    @classmethod
    def instances(cls):
        """
        Returns number of Application instances.
        """
        return cls.__instances__

    @property
    def meta(self) -> dict:
        """
        Get application metadata.
        """
        return Meta.compile()

    @property
    def process_id(self) -> int:
        """
        Returns the application main process ID.
        """
        if not hasattr(self, "_main_process_id"):
            self._main_process_id = os.getpid()
        return self._main_process_id

    @staticmethod
    def check_ssl_credentials():
        """
        This checks for ssl certfile and private key file existence.

        Raises:
            SSLError: Either certfile or private key file is not found.
        """
        certfile_path = SETTINGS["SSL_CERTFILE_LOCATION"]
        private_key_path = SETTINGS["SSL_PRIVATE_KEY_LOCATION"]
        if not os.path.isfile(certfile_path):
            raise SSLError(
                "SSL certfile provided in settings.py not found. You may use command `python3 -m duck ssl-gen` to "
                "generate a new self signed certificate and key pair")

        if not os.path.isfile(private_key_path):
            raise SSLError(
                "SSL private key provided in settings.py not found. You may use command `python3 -m duck ssl-gen` to "
                "generate a new self signed certificate and key pair ")

    def run_checks(self):
        """
        Runs application checks.
        """
        if SETTINGS["ENABLE_HTTPS"]:
            self.check_ssl_credentials()

        # https checks
        if SETTINGS["FORCE_HTTPS"]:
            if not SETTINGS["ENABLE_HTTPS"]:
                raise SettingsError(
                    "FORCE_HTTPS has been set in settings.py, also ensure ENABLE_HTTPS=True"
                )

    @property
    def absolute_uri(self) -> str:
        """
        Returns app absolute URL.
        """
        scheme = "http"
        if self.enable_https:
            scheme = "https"
        uri = f"{scheme}://{self.domain}"
        uri = uri.strip("/").strip("\\")
        if not (self.port == 80 or self.port == 443):
            uri += f":{self.port}"
        return uri

    def build_absolute_uri(self, path: str) -> str | None:
        """
        Builds and returns absolute URL from provided path.
        """
        return url_normalize(self.absolute_uri + "/" + path)

    @property
    def server_up(self) -> bool:
        """
        Checks whether the main application server is up and running.

        Returns:
            bool: True if up else False
        """
        return self.server.running

    @property
    def django_server_up(self) -> bool:
        """
        Checks whether django server to forward requests to has started

        Returns:
            started (bool): True if up else False
        """
        import requests

        try:
            host_addr, port = self.DJANGO_ADDR
            if host_addr.startswith("0") and not self.uses_ipv6:
                # Host 0.0.0.0 not allowed on windows
                host_addr = "127.0.0.1"
            url = (f"http://{host_addr}:{port}/"
                   if not self.uses_ipv6 else f"http://[{host_addr}]:{port}/")
            response = requests.get(
                url=url,
                headers={"Host": SETTINGS["DJANGO_SHARED_SECRET_DOMAIN"]},
                timeout=1,
            )
            good_statuses = [200, 404, 500]
            if not response.status_code in good_statuses:
                # response status is not expected here
                return False
            return True
        except:
            pass
        return False

    @property
    def force_https_app_up(self) -> bool:
        """
        Checks whether force https application is running.

        Returns:
            bool: True if up else False
        """
        return self.force_https_app.server.running

    def start_server(self):
        """
        Starts the app server in new thread.
        """
        self.duck_server_thread.start()

    def start_django_server(self):
        """
        Starts Django server and use Duck as reverse proxy server for django.
        """
        if SETTINGS["USE_DJANGO"]:
            self.django_server_thread.start()

    def start_force_https_app(self):
        """
        Starts force https redirect app.

        Conditions:
                ENABLE_HTTPS = True
                FORCE_HTTPS = True
        """

        def start_force_https_app():
            if self.server_up:
                logger.log(
                    f"Forcing https to all incoming traffic [{SETTINGS['FORCE_HTTPS_BIND_PORT']} -> {self.port}]",
                    level=logger.DEBUG,
                )
                self.force_https_thread.start()

        if SETTINGS["ENABLE_HTTPS"] and SETTINGS["FORCE_HTTPS"]:
            start_force_https_app()

    def start_ducksight_reloader(self):
        """
        Starts the DuckSight Reloader for reloading app on file modifications, deletions, etc.

        Conditions:
            DEBUG = True
            ducksight_reloader_process_alive = False
        """
        # Note: Production server should not be restarted at any point only start duck sight reloader on DEBUG
        if SETTINGS["DEBUG"]:
            self.ducksight_reloader_process = (
                reloader.start_ducksight_reloader_process()
            )  # start ducksight reloader

    def start_automations_dispatcher(self):
        """
        Starts Automations Dispatcher for executing automations during runtime.

        Conditions:
            RUN_AUTOMATIONS = True
        """
        if SETTINGS["RUN_AUTOMATIONS"]:
            self.automations_dispatcher_thread.start()

    def stop_all_servers(
        self,
        stop_force_https_server: bool = True,
        log_to_console: bool = True):
        """
        Stop all running servers, ie. Duck & Django server and also Force Https server if running.

        Args:
            stop_force_https_server (bool): Whether to stop force-https microapp.
            log_to_console (bool): Whether to log to console that `Duck server stopped`.
        """
        self.server.stop_server(log_to_console=log_to_console)
        
        if hasattr(self, "force_https_app"):
            (self.force_https_app.stop()
             if self.force_https_app_up and stop_force_https_server else None)

        if hasattr(self, "django_server_process"):
            # django server has been started
            self.django_server_process.terminate()
            os.kill(self.django_server_process.pid) # ensure django stopped

    def on_pre_stop(self):
        """Event called before final app termination."""
        pass

    def stop(self, log_to_console: bool = True, no_exit=False):
        """
        Stops the application and terminates the whole program.

        Args:
            no_exit (bool): Whether to terminate everything but keep the program running.
            log_to_console (bool): Whether to log to the console that `Duck server stopped`.
        """
        # Cleanup session cache
        try:
            if hasattr(self, "last_request") and self.last_request:
                if (hasattr(self.last_request.SESSION, "session_storage_connector") 
                    and self.last_request.SESSION.session_storage_connector):
                    self.last_request.SESSION.session_storage_connector.close()
        except Exception as e:
            logger.log_raw('\n')
            logger.log(
                f"Error while closing session storage: {e}",
                level=logger.WARNING,
            )

        # Stop all servers
        try:
            self.stop_all_servers(log_to_console=log_to_console)
        except Exception as e:
            logger.log_raw('\n')
            logger.log(f"Error stopping servers: {e}", level=logger.ERROR)

        # Essential threads
        essentials = [
            self.automations_dispatcher_thread,
        ]  # Essential Duck app threads

        def stop_thread(thread):
            """
            Stop a running thread safely.

            Args:
                thread (threading.Thread): The thread to stop.
            """
            if not thread or not thread.is_alive():
                return

            try:
                # Attempt to join the thread with a timeout
                thread.join(timeout=0.5)
            except RuntimeError as e:
                pass

        # Stop all threads in the TimerThreadPool and essential threads
        for thread in TimerThreadPool.all + essentials:
            try:
                stop_thread(thread)
            except Exception as e:
                pass

        # Perform forceful termination if needed
        if not no_exit:
            try:
                # Gracefully terminate threads and processes before exiting
                threading.enumerate()  # Check running threads for debugging
            except Exception:
                pass
            try:
                # Execute a pre stop method before final termination.
                self.on_pre_stop()
            except Exception as e:
                logger.log_exception(e) # Log the exception.
            os._exit(0)  # Force exit (avoids lingering threads/processes)

    def handle_ipc_messages(self):
        """
        Handles incoming IPC messages from the shared file.
        """
        with ipc.get_reader() as reader:
            with ipc.get_writer() as writer:
                writer.write_message("")  # clear ipc shared file

            while True:
                message = reader.read_message().strip()
                if message:
                    if (message.lower() == "bye" or message.lower() == "exit"
                            or message.lower() == "quit"):
                        break
                    else:
                        if message == "prepare-restart" and self.server.running:
                            # This is usually sent by DuckSightReloader before starting a new server instance.
                            self.stop(
                                log_to_console=False,
                                no_exit=True,
                            )  # cleans up server for another server instance bootup.
                time.sleep(1)  # Simulate some delay

    def record_metadata(self):
        """
        Sets or updates the metadata for the app, these changes will
        be globally available to meta.Meta c
        """
        # security reasons not mentioning real servername but 'webserver'
        data = {
                "DUCK_SERVER_NAME": "webserver",
                "DUCK_SERVER_PORT": self.port,
                "DUCK_SERVER_DOMAIN": self.domain,
                "DUCK_SERVER_PROTOCOL":
                    ("https" if self.enable_https else "http"),
                "DUCK_DJANGO_ADDR": self.DJANGO_ADDR,
                "DUCK_USES_IPV6": self.uses_ipv6,
                "DUCK_SERVER_BUFFER": SETTINGS["SERVER_BUFFER"],
                "DUCK_SERVER_POLL": SETTINGS["SERVER_POLL"],
        }
        Meta.update_meta(data)
        
    def signal_handler(self, sig, frame):
        """
        Method to be called on different signals.

        Signals:
                SIGINT (Ctrl-C), SIGTERM (Terminate): Quits the server/application.
        """
        try:
            reloader.stop_ducksight_reloader_process(
            )  # me thod 1 to stop ducksight reloader process if running
        except OSError:
            # filelock errors when changing state using `processes.set_state`
            pass
        if hasattr(self, "ducksight_reloader_process"):
            try:
                # Method 2 to stop ducksight reloader process if running
                self.ducksight_reloader_process.kill()
            except Exception:
                pass
        # check if Duck hasn't printed Duck server stopped meassage
        if "--reload" in sys.argv:
            self.stop(log_to_console=False)
        else:
            self.stop()

    def register_signals(self):
        """
        Register and bind signals to appropriate signal handler.
        """
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def on_app_start(self):
        """
        Event called when application has successfully been started.
        """
        # record main process data
        try:
            processes.set_process_data(
                name="main",
                data={
                    "pid": self.process_id,
                    "start_time": time.time(),
                    "sys_argv": sys.argv,
                    "log_file": (logger.get_current_log_file()
                                 if SETTINGS["LOG_TO_FILE"] else None),
                },
                clear_existing_data=True,
            )
        except json.JSONDecodeError:
            # the file used by duck.processes is corrupted
            pass  # ignore for now, maybe writting is still in progress

        logger.log(
            f"Use Ctrl-C to quit [APP PID: {self.process_id}]",
            level=logger.DEBUG,
            custom_color=logger.Fore.GREEN,
        )

        if SETTINGS["AUTO_RELOAD"] and SETTINGS["DEBUG"]:
            self.start_ducksight_reloader(
            )  # start ducksight reloader if not running

            reloader_pid = None

            try:
                reloader_pid = processes.get_process_data(
                    "ducksight-reloader").get("pid")
            except KeyError:
                # failed ducksight reloader pid
                pass
            logger.log(
                f"DuckSight Reloader watching file changes [PID: {reloader_pid}]",
                level=logger.DEBUG,
                custom_color=logger.Fore.GREEN,
            )

        # continue
        logger.log(
            "Waiting for incoming requests :-) \n",
            level=logger.DEBUG,
            custom_color=logger.Fore.GREEN,
        )
        self.register_signals()  # bind signals to appropriate signal_handler
        self.handle_ipc_messages()

    def needs_reload(self) -> bool:
        """
        Checks if the '--reload' flag is present in the command-line arguments (sys.argv).
        Returns:
            bool: True if flag `--reload` is in sys.argv else False
        """
        if "--reload" in sys.argv:
            return True
        return False

    def reload_if_needed(self):
        """
        Checks if the '--reload' flag is present in the command-line arguments (sys.argv).
        If the flag is found, the application is reloaded or restarted immediately.

        This method is typically used to trigger a reload of the application during runtime
        based on a specific condition (the presence of the '--reload' argument). It is useful
        for scenarios where the application needs to be restarted without manual intervention,
        such as during development or when configurations change.

        If the '--reload' argument is not found, the application continues running normally
        without initiating any reload or restart action.

        Notes:
            - This method calls method `_restart` right away if flag is found.

        Example usage:
            application.reload_if_needed()  # Triggers a restart if '--reload' is in sys.argv
        """
        if self.needs_reload():
            self._restart()
            
    def run(self, print_ansi_art=True):
        """
        Runs the Duck application.

        Notes:
            - If argument --reload is in sys.argv, the server is restarted instead.
        """
        if not SETTINGS["AUTO_RELOAD"]:
            # stop ducksight reloader process if running
            reloader.stop_ducksight_reloader_process()
            if hasattr(self, "ducksight_reloader_process"):
                try:
                    self.ducksight_reloader_process.kill()
                except Exception:
                    pass
        
        # Quickly restarts app immediately if '--reload' is found in sys.argv
        self.reload_if_needed()  
        
        if self.needs_reload():
            # reload flag is present, --reload is found in sys.argv
            # app has already been reloaded
            if self._restart_success:
                return

            # tried to restart but failed
            self.stop(log_to_console=True)
            return
        return self._run(print_ansi_art=print_ansi_art)

    def _restart(self) -> Optional[bool]:
        """
        Super method to re-run the Duck application.

        Notes:
            - This will not stop the current running application (if any)
            - DJANGO_COMMANDS_ON_STARTUP will not be run in this method.
            - self._restart_success will be set to True if restart has been successfull

        Returns:
                bool: True if app restarted successfuly else None
        """
        self._restart_success = False  # reset state
        bold_start = "\033[1m"
        bold_end = "\033[0m"
        duck_start_failure_msg = f"{bold_start}Failed to start Duck server{bold_end}"
        
        # redirect all console output to log file
        if SETTINGS["LOG_TO_FILE"]:
            logger.redirect_console_output()

        logger.log("Reloading server...", level=logger.DEBUG)

        if SETTINGS["RUN_AUTOMATIONS"]:
            logger.log(
                f"Running all automations with {type(self.automations_dispatcher).__name__}",
                level=logger.DEBUG,
            )
            self.start_automations_dispatcher()

        self.start_server()  # start server
        time.sleep(2)

        # vital checks here
        if not self.server_up:
            logger.log(duck_start_failure_msg, level=logger.ERROR)
            self.stop(log_to_console=False)
            return
        else:
            # record application metadata
            self.record_metadata()
        
        if SETTINGS["FORCE_HTTPS"]:
            self.start_force_https_app()
            time.sleep(2)

            # check if force https app was successfully deployed
            # terminate if not
            # checks here
            if not self.force_https_app_up:
                logger.log("HTTPS redirect app failed to start",
                           level=logger.ERROR)
                self.stop(log_to_console=False)

        if SETTINGS["USE_DJANGO"]:
            wait_t = self.DJANGO_SERVER_WAIT_TIME
            logger.log(
                f"Waiting for Django server to start ({wait_t} secs)\n",
                level=logger.DEBUG,
            )
            self.start_django_server()
            time.sleep(self.DJANGO_SERVER_WAIT_TIME)

            # check if django is running
            if not self.django_server_up:
                logger.log(duck_start_failure_msg, level=logger.ERROR)
                self.stop(log_to_console=False)
            else:
                host_url = ("http://"
                            if not self.server.enable_ssl else "https://")
                host, port = self.server.addr

                if host.startswith("0") and not self.uses_ipv6:
                    host = (
                        "127.0.0.1"  # convert host to browser's recognizeable
                    )
                else:
                    if self.uses_ipv6:
                        host = f"[{host}]"
                host_url += f"{host}:{port}"
                logger.log(
                    "Django restarted successfully!",
                    level=logger.DEBUG,
                    custom_color=logger.Fore.GREEN,
                )
                logger.log(
                    f"Duck server restarted on {host_url}",
                    level=logger.DEBUG,
                    custom_color=logger.Fore.GREEN,
                )
        self.on_app_start()
        self._restart_success = True
        return True
    
    def _run(self, print_ansi_art=True):
        """
        Runs the Duck application.
        """
        # Revert ducksight reloader state to dead, because this is our app first run.
        reloader.set_state("dead")  
        
        # app is not in reload state, continue
        bold_start = "\033[1m"
        bold_end = "\033[0m"
        duck_start_failure_msg = f"{bold_start}Failed to start Duck server{bold_end}"

        if print_ansi_art and not SETTINGS["SILENT"]:
            display_duck_art()  # print duck art
            settings_mod = "DUCK_SETTINGS_MODULE"
            settings_mod = os.environ.get(settings_mod, 'settings')
            print(f"{bold_start}VERSION {version}{bold_end}")

        # redirect all console output to log file
        if SETTINGS["LOG_TO_FILE"]:
            logger.redirect_console_output()
        
        # Log the current settings module in use
        settings_mod = "DUCK_SETTINGS_MODULE"
        settings_mod = os.environ.get(settings_mod, 'settings')
        logger.log_raw(f'{bold_start}USING SETTINGS{bold_end} "{settings_mod}" \n')
        
        if not self.is_domain_set:
            logger.log(
                f'WARNING: Domain not set using "{self.domain}" ',
                level=logger.WARNING,
            )

        if SETTINGS["RUN_AUTOMATIONS"]:
            logger.log(
                f"Running all automations with {type(self.automations_dispatcher).__name__}",
                level=logger.DEBUG,
            )
            self.start_automations_dispatcher()

        self.start_server()  # start server

        # log something
        Timer.schedule(
            lambda: logger.log(
                "Waiting 2s to read server state...",
                level=logger.DEBUG),
                0.2,
        )
        time.sleep(2)

        # check if main server was successfully deployed
        # terminate if not
        # checks here
        if not self.server_up:
            logger.log(duck_start_failure_msg, level=logger.ERROR)
            self.stop()
            return
        else:
            # record application metadata
            self.record_metadata()

        if SETTINGS["FORCE_HTTPS"]:
            self.start_force_https_app()
            time.sleep(2)

            # check if force https app was successfully deployed
            # terminate if not
            # checks here
            if not self.force_https_app_up:
                logger.log("HTTPS redirect app failed to start",
                           level=logger.ERROR)
                self.stop()

        if SETTINGS["USE_DJANGO"]:
            logger.log(
                "Requests will be forwarded to Django server",
                level=logger.DEBUG,
            )
            logger.log(
                f"Starting Django server on port [{SETTINGS['DJANGO_BIND_PORT']}]",
                level=logger.DEBUG,
            )

            if SETTINGS["DJANGO_COMMANDS_ON_STARTUP"]:
                try:
                    logger.log_raw("\n")
                    bridge.run_django_app_commands()
                except Exception as e:
                    logger.log(
                        f"Failed to run django commands: {e}\n",
                        level=logger.ERROR,
                    )
                    logger.log_exception(e)
                    self.stop()

            wait_t = self.DJANGO_SERVER_WAIT_TIME
            logger.log(
                f"Waiting for Django server to start ({wait_t} secs)\n",
                level=logger.DEBUG,
            )
            self.start_django_server()
            time.sleep(self.DJANGO_SERVER_WAIT_TIME)

            # check if django is running
            if not self.django_server_up:
                logger.log("Failed to start Django server", level=logger.ERROR)
                self.stop()
            else:
                host_url = ("http://"
                            if not self.server.enable_ssl else "https://")
                host, port = self.server.addr
                if host.startswith("0") and not self.uses_ipv6:
                    host = (
                        "127.0.0.1"  # convert host to browser's recognizeable
                    )
                else:
                    if self.uses_ipv6:
                        host = f"[{host}]"
                host_url += f"{host}:{port}"
                logger.log(
                    "Django started yey, that's good!",
                    level=logger.DEBUG,
                    custom_color=logger.Fore.GREEN,
                )
                logger.log(
                    f"Duck Server listening on {host_url}",
                    level=logger.DEBUG,
                    custom_color=logger.Fore.GREEN,
                )
        self.on_app_start()
