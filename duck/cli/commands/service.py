"""
Module containing commands for creating and managing Duck services using systemd (compatible with linux-based systems only).
"""
import os
import re
import pwd
import click
import time
import subprocess

from datetime import datetime

from duck.logging import console
from duck.utils.path import joinpaths


SERVICE_CONTENT = """
[Unit]
Description=Duck Web Server
After=network.target

[Service]
User={user}
ExecStart={exec_start}
WorkingDirectory={base_dir}
Restart={restart}
{environ_data}

[Install]
WantedBy=multi-user.target
"""

class ServiceCommand:
    # systemd service command
    
    @classmethod
    def create_service(cls, settings: str = None):
        """
        Function to create the systemd service for Duck.
        
        Args:
            settings (str): Customizable comma-separated Duck settings you want to change at runtime without depending on settings.py.
                Example: `key=value, key2=value2`
                
        Notes:
        - The settings argument can only be useful for string value type settings.
        
        Example Usage:
        
        ```bash
        duck service create --settings "systemd_exec_command=duck runserver -p 5000, systemd_restart=always"
        ```
        """
        from duck.settings import SETTINGS
        
        if settings:
            # load the settings
            try:
                for setting in settings.split(','):
                    key_, value = setting.split('=', 1)
                    key, value = key_.strip().upper(), value.strip().strip('"').strip("'")
                    
                    if key not in SETTINGS:
                        console.log(f"Unknown setting `{key_}`, make sure this setting exist within Duck configuration.", level=console.WARNING)
                        return
                        
                    SETTINGS[key] = value
                    
            except (ValueError, TypeError):
                console.log("Error parsing the provided custom runtime settings, make sure they are comma-separated strings in format `--settings 'key=value, key2=value' `", level=console.WARNING)
                return
                
        base_dir = SETTINGS["BASE_DIR"]
        exec_start = SETTINGS["SYSTEMD_EXEC_COMMAND"]
        restart = SETTINGS["SYSTEMD_RESTART"]
        environment = SETTINGS["SYSTEMD_ENVIRONMENT"]
        service_dir = SETTINGS["SYSTEMD_SERVICE_DIR"]
        service_name = SETTINGS["SYSTEMD_SERVICE_NAME"]
        user = pwd.getpwuid(os.getuid()).pw_name
        
        def escape_value(val):
            return val.replace('"', '\\"')
        
        environ_data = '\n'.join([
            f'Environment="{key}={escape_value(value)}"'
            for key, value in environment.items()
        ])
        
        service_content = SERVICE_CONTENT.format(
            exec_start=exec_start,
            user=user,
            base_dir=str(base_dir),
            restart=restart,
            environ_data = environ_data)
        
        # Write the service content to the systemd service file
        service_path = joinpaths(str(service_dir), service_name)
        
        try:
            with open(service_path, 'w') as f:
                f.write(service_content)
            console.log(f"Service file created at {service_path}", level=console.DEBUG)
        except IOError as e:
            console.log(f"Failed to create service file at {service_path}: {e.strerror}. Check file permissions and directory existence.", level=console.ERROR)
            return False
        return True
    
    @classmethod
    def reload_systemd(cls):
        """Method to reload systemd to apply the new service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            console.log("Systemd reloaded to apply new service.", level=console.INFO)
        except FileNotFoundError:
            console.log("Error: `systemctl` command not found. Please ensure systemd is installed on your system.", level=console.ERROR)
        except subprocess.CalledProcessError as e:
            console.log(f"An error occurred while reloading systemd: {e}", level=console.ERROR)
    
    @classmethod
    def enable_service(cls):
        """Function to enable the systemd service to start on boot"""
        from duck.settings import SETTINGS
        
        service_name = SETTINGS["SYSTEMD_SERVICE_NAME"]
        
        try:
            subprocess.run(['sudo', 'systemctl', 'enable', service_name], check=True)
            console.log(f"`{service_name}` service enabled to start on boot.", level=console.INFO)
        except FileNotFoundError:
            console.log("Error: `systemctl` command not found. Please ensure systemd is installed on your system.", level=console.ERROR)
        except subprocess.CalledProcessError as e:
            console.log(f"Error: Failed to enable `{service_name}` service. Check system logs.", level=console.ERROR)
                
    @classmethod
    def start_service(cls):
        """Method to start the systemd service"""
        from duck.settings import SETTINGS
        
        service_name = SETTINGS["SYSTEMD_SERVICE_NAME"]
        
        try:
            subprocess.run(['sudo', 'systemctl', 'start', service_name], check=True)
            console.log(f"Service `{service_name}` started.", level=console.INFO)
            return True
        except FileNotFoundError:
            console.log("Error: `systemctl` command not found. Please ensure systemd is installed on your system.", level=console.ERROR)
        except subprocess.CalledProcessError as e:
            console.log(f"Error: Failed to start `{service_name}` service. Check system logs.", level=console.ERROR)
    
    @classmethod
    def stop_service(cls):
        """Method to stop the systemd service"""
        from duck.settings import SETTINGS
        
        service_name = SETTINGS["SYSTEMD_SERVICE_NAME"]
        
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=True)
            # Stopping again to make sure the service is stopped
            subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=True)
            console.log(f"Service `{service_name}` stopped.", level=console.INFO)
            try:
                cls.check_service()
            except Exception as e:
                console.log("Error: Failed to print Duck service status", level=console.WARNING)
            return True
        except FileNotFoundError:
            console.log("Error: `systemctl` command not found. Please ensure systemd is installed on your system.", level=console.ERROR)
        except subprocess.CalledProcessError as e:
            console.log(f"Error: Failed to stop `{service_name}` service. Check system logs.", level=console.ERROR)
    
    @classmethod
    def disable_service(cls):
        """Method to disable the systemd service from starting on boot"""
        from duck.settings import SETTINGS
        
        service_name = SETTINGS["SYSTEMD_SERVICE_NAME"]
        
        try:
            subprocess.run(['sudo', 'systemctl', 'disable', service_name], check=True)
            console.log(f"`{service_name}` service disabled from boot.", level=console.INFO)
        except FileNotFoundError:
            console.log("Error: `systemctl` command not found. Please ensure systemd is installed on your system.", level=console.ERROR)
        except subprocess.CalledProcessError as e:
            console.log(f"Error: Failed to disable `{service_name}` service. Check system logs.", level=console.ERROR)
    
    @classmethod
    def check_service(cls):
        """Method to check the status of the systemd service and display detailed information."""
        from duck.settings import SETTINGS
        
        service_name = SETTINGS["SYSTEMD_SERVICE_NAME"]
        
        try:
            # Use systemctl to check the service status and capture the output
            result = subprocess.run(
                ['systemctl', 'status', service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )

            # Print the full status information directly
            console.log(f"Status of `{service_name}` service:", level=console.INFO)
            console.log_raw(result.stdout, use_colors=False)  # Directly print the full status output
            
        except subprocess.CalledProcessError as e:
            # If systemctl fails, handle the error gracefully
            console.log(f"Error checking service `{service_name}`: The error occurred while running: `systemctl status {service_name}`. Error details: {e.stderr or 'unavailable'}. Please check if systemd is working properly and the service is installed correctly.", level=console.ERROR)
            return False

        except FileNotFoundError:
            console.log("Error: `systemctl` command not found. Please ensure systemd is installed on your system.", level=console.ERROR)
            
    @classmethod
    def autorun(cls, kill: bool = False, enable: bool = False, disable: bool = False, settings: str = None, show_status: bool = True):
        """
        This automatically creates and runs the **Duck** service at latest changes, you do not need to reload systemd, everything will be done for you.
        
        The status of the service will be printed after if the other steps completed successfully.
        
        Args:
            kill (bool): Whether to kill a running Duck service (if present) before running this new latest service.
            enable (bool): Enables the new service to be started on boot.
            disable (bool): Disables the new service not to be started on boot.
            settings (str): Customizable comma-separated Duck settings you want to change at runtime without depending on settings.py.
                Example: `key=value, key2=value2`
            status (bool): Whether to show status of the service if other steps completed.
        """
        if enable and disable:
            console.log("The parameters `disable` and `enable` cannot be provided together, use one of the parameters.", level=console.ERROR)
            return
        
        if kill:
            console.log("Killing existing Duck service (if present)", level=console.WARNING)
            s = cls.stop_service()
            if not s:
                # Failed to stop service, cannot continue
                return
            else:
                time.sleep(.5)
                
        if cls.create_service(settings=settings) and cls.start_service():
            if enable:
                cls.enable_service()
            
            if disable:
                cls.disable_service()
            
            # Reload systemd and prints the status
            cls.reload_systemd()
            
            if show_status:
                console.log("Sleeping for 1s before status report", level=console.DEBUG)
                time.sleep(1)
                cls.check_service()
    
    @classmethod
    def register_subcommands(cls, main_command: click.Command):
        """
        Register the subcommands for the `duck service` command.
        """
        data = {
            "create": {
                "callback": cls.create_service,
                "params": [
                    click.Option(('-s', "--settings"), default=None, help="Comma separated Duck runtime settings."),
                ],
                "help": "Create the Duck service."
             },
            "autorun": {
                "callback": cls.autorun,
                "params": [
                    click.Option(('-k', "--kill"), is_flag=True, default=False, help="Automatically kill a running Duck service (if present)"),
                    click.Option(("-e", "--enable"), is_flag=True, default=False, help="Enables the new service to be started on boot."),
                    click.Option(("-d", "--disable"), is_flag=True, default=False, help="Disables the new service not to be started on boot."),
                    click.Option(('-s', "--settings"), default=None, help="Comma separated Duck runtime settings."),
                    click.Option(('-st', "--show-status"), default=True, type=bool, help="Whether to show service status only if other steps are completed."),
                ],
                "help": "Automatically create and run the Duck service at the latest changes."
            },
            "start": {
                "callback": cls.start_service,
                "help": "Start the Duck service."
            },
            "stop": {
                "callback": cls.stop_service,
                "help": "Stop the Duck service."
            },
            "enable": {
                "callback": cls.enable_service,
                "help": "Enable the Duck service to start on boot."
            },
            "disable": {
                "callback": cls.disable_service,
                "help": "Disable the Duck service from starting on boot."
            },
            "status": {
                "callback": cls.check_service,
                "help": "Check the status of the Duck service."
            },
            "reload-systemd": {
                "callback": cls.reload_systemd,
                "help": "Reload the systemd."
            },
        }
        
        for cmd, info in data.items():
            cmd = click.Command(cmd, **info)
            main_command.add_command(cmd)
