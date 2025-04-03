"""
Module containing commands for creating and managing Duck services using systemd (compatible with linux-based systems only).
"""
import os
import re
import pwd
import click
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
Environment={environment}

[Install]
WantedBy=multi-user.target
"""

class ServiceCommand:
    # systemd service command
    
    @classmethod
    def create_service(cls):
        """Function to create the systemd service for Duck"""
        from duck.settings import SETTINGS
        
        base_dir = SETTINGS["BASE_DIR"]
        exec_start = SETTINGS["SYSTEMD_EXEC_COMMAND"]
        restart = SETTINGS["SYSTEMD_RESTART"]
        environment = SETTINGS["SYSTEMD_ENVIRONMENT"]
        service_dir = SETTINGS["SYSTEMD_SERVICE_DIR"]
        service_name = SETTINGS["SYSTEMD_SERVICE_NAME"]
        user = pwd.getpwuid(os.getuid()).pw_name
        
        service_content = SERVICE_CONTENT.format(
            exec_start=exec_start,
            user=user,
            base_dir=str(base_dir),
            restart=restart,
            environment=os.pathsep.join([f'{key}={value}' for key, value in environment.items()])
        )
        
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
            console.log(f"`{service_name}` service started.", level=console.INFO)
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
            console.log(f"`{service_name}` service stopped.", level=console.INFO)
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
            console.log_raw(result.stdout)  # Directly print the full status output
            
        except subprocess.CalledProcessError as e:
            # If systemctl fails, handle the error gracefully
            console.log(f"Error checking service `{service_name}`: The error occurred while running: `systemctl status {service_name}`. Error details: {e.stderr or 'unavailable'}. Please check if systemd is working properly and the service is installed correctly.", level=console.ERROR)
            return False

        except FileNotFoundError:
            console.log("Error: `systemctl` command not found. Please ensure systemd is installed on your system.", level=console.ERROR)
            
    @classmethod
    def register_subcommands(cls, main_command: click.Command):
        """
        Register the subcommands for the `duck service` command.
        """
        data = {
            "create": {"callback": cls.create_service, "help": "Create the Duck service."},
            "start": {"callback": cls.start_service, "help": "Start the Duck service."},
            "stop": {"callback": cls.stop_service, "help": "Stop the Duck service."},
            "enable": {"callback": cls.enable_service, "help": "Enable the Duck service to start on boot."},
            "disable": {"callback": cls.disable_service, "help": "Disable the Duck service from starting on boot."},
            "status": {"callback": cls.check_service, "help": "Check the status of the Duck service."},
            "reload-systemd": {"callback": cls.reload_systemd, "help": "Reload the systemd."},
        }
        
        for cmd, info in data.items():
            cmd = click.Command(cmd, callback=info["callback"], help=info["help"])
            main_command.add_command(cmd)
