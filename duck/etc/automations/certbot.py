"""
Automation to obtain or renew an SSL certificate using Certbot.
This ensures your Duck server maintains a valid HTTPS connection
by automatically handling certificate issuance and renewal.
"""
import re
import os
import time
import subprocess
import configparser

from duck.exceptions.all import SettingsError
from duck.http.core.handler import ResponseHandler
from duck.automation import Automation
from duck.settings import SETTINGS
from duck.logging import logger
from duck.utils.path import joinpaths
from duck.utils.filelock import (unlock_file, open_and_lock)


# Fetch SSL certificate and key paths from the settings.
SSL_CERT_PATH = SETTINGS["SSL_CERTFILE_LOCATION"]

SSL_CERT_KEY_PATH = SETTINGS["SSL_PRIVATE_KEY_LOCATION"]

# Validate required Certbot configuration in settings
if "CERTBOT_ROOT" not in SETTINGS:
    raise SettingsError(
        "Missing 'CERTBOT_ROOT' in settings. "
        "This path is required for Certbot to store challenge files used during domain validation."
    )

if "CERTBOT_EMAIL" not in SETTINGS:
    raise SettingsError(
        "Missing 'CERTBOT_EMAIL' in settings. "
        "This email is used by Certbot for important notices and recovery purposes."
    )


class BaseCertbotAutoSSL(Automation):
    """
    Automation class to handle automatic SSL generation and renewal
    using the Certbot CLI with the webroot plugin.
    """
    
    certname: str = "duckcert"
    """
    The certificate name.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.certbot_root = SETTINGS["CERTBOT_ROOT"]
        self.config_path = joinpaths(str(self.certbot_root), f"renewal/{self.certname}.conf")
        self.config = self.extract_config_values(self.config_path, "fullchain", "privkey")
        self.key_path = self.config.get("privkey", None)
        self.fullchain_path = self.config.get("fullchain", None)
        self.latest_cert_signature = self.get_file_signature(self.fullchain_path) if self.fullchain_path is not None else None
        self.latest_cert_key_signature = self.get_file_signature(self.key_path) if self.key_path is not None else None
            
    @staticmethod
    def get_file_signature(path):
        """
        Returns the file signature else None if file doesn't exist.
        """
        if not os.path.isfile(path):
            return
        stats = os.stat(path)
        return (stats.st_mtime, stats.st_ino)
    
    def patch_microapp(self, microapp):
        """
        Applies patches to microapp view method so that route `certbot`acme challenge files
        will not be redirected to `HTTPS` but rather be handled directly.
        
        Notes:
        - Only useful if `ENABLE_HTTPS=True`.
        """
        default_view = microapp.view
        
        def wrapped_view(request, request_processor):
            """
            Micro application `view` method patched with new functionality.
            """
            route = "/.well-known/.*"
            pattern = re.compile(route)
            
            if pattern.fullmatch(request.path):
                # This is an acme verification challenge path
                response = request_processor.get_response(request)
                response.payload_obj.http_version = "HTTP/1.1" # http may be set to HTTP/2
                return response
            else:
                return default_view(request, request_processor)
        
        # Apply view mathod patch
        microapp.view = wrapped_view
        
    def on_start(self):
        if SETTINGS["ENABLE_HTTPS"] and not SETTINGS["FORCE_HTTPS"]:
            logger.log("CertbotAutoSSL: `FORCE_HTTPS` disabled in settings", level=logger.WARNING)
            self.disable_execution = True
            
    def extract_config_values(self, config_path: str, *args):
        """
        Extracts specified key-value pairs from a Certbot `.conf` configuration file.
        
        Args:
            config_path (str): 
                Path to the Certbot configuration file. This is typically in the form 
                `{certbot_root}/renewal/{certname}.conf`.
            
            *args (str): 
                One or more configuration keys to extract (e.g., "fullchain", "privkey").
        
        Returns:
            dict: A dictionary containing the requested keys and their corresponding values.
                  If a key is not found, its value will be None.
        
        Example:
        
        ```py
        
        config = extract_config_values("/etc/letsencrypt/renewal/example.com.conf", "fullchain", "privkey")
        
        # Output:
        # {
        #     "fullchain": "/etc/letsencrypt/live/example.com/fullchain.pem",
        #     "privkey": "/etc/letsencrypt/live/example.com/privkey.pem"
        # }
        ```
        """
        values = {key: None for key in args}
        
        if not os.path.isfile(config_path):
            return values
        
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                for key in args:
                    if line.startswith(key):
                        _, value = line.split("=", 1)
                        values[key] = value.strip()
                        break  # Avoid rechecking other keys for this line
    
                if all(values[k] is not None for k in args):
                    break  # Stop early if all values found
    
        return values
    
    @logger.handle_exception
    def on_cert_success(self):
        """
        Event called on successful certbot command, i.e. successful certificate generation or renewal.
        """
        cert_data = None
        key_data = None
        
        if self.latest_cert_signature is not None:
            current_cert_signature = self.get_file_signature(self.fullchain_path)
            
            if self.latest_cert_signature != current_cert_signature:
                # New certificate has been generated by certbot
                
                with open_and_lock(self.fullchain_path, "r") as cert_file:
                    cert_data = cert_file.read()
                    
                    # Unlock file descriptor
                    unlock_file(cert_file)
                
                with open_and_lock(SSL_CERT_PATH, "w") as cert_file:
                    cert_file.write(cert_data)
                    
                    # Unlock file immediately after writing
                    unlock_file(cert_file)
                
                if SETTINGS["DEBUG"]:
                    logger.log(f"CertbotAutoSSL: Wrote SSL fullchain credential to {SSL_CERT_PATH}", level=logger.DEBUG)
            
        if self.latest_cert_key_signature is not None:
            current_cert_key_signature = self.get_file_signature(self.key_path)
            
            if self.latest_cert_key_signature != current_cert_key_signature:
                # New private key has been generated by certbot
                
                with open_and_lock(self.key_path, "r") as key_file:
                    key_data = key_file.read()
                    
                    # Unlock file descriptor
                    unlock_file(key_file)
                
                with open_and_lock(SSL_CERT_PATH, "w") as key_file:
                    key_file.write(key_data)
                    
                    # Unlock file immediately after writing
                    unlock_file(key_file)
                
                if SETTINGS["DEBUG"]:
                    logger.log(f"CertbotAutoSSL: Wrote SSL private key credential to {SSL_CERT_KEY_PATH}", level=logger.DEBUG)
          
        if cert_data or key_data:
             logger.log("CertbotAutoSSL: SSL credentials updated\n", level=logger.DEBUG)
        
        self.config = self.extract_config_values(self.config_path, "fullchain", "privkey")
        self.key_path = self.config.get("privkey", None)
        self.fullchain_path = self.config.get("fullchain", None)
        self.latest_cert_signature = self.get_file_signature(self.fullchain_path) if self.fullchain_path is not None else None
        self.latest_cert_key_signature = self.get_file_signature(self.key_path) if self.key_path is not None else None
        
    def execute(self):
        certbot_root = SETTINGS["CERTBOT_ROOT"]
        certbot_email = SETTINGS["CERTBOT_EMAIL"]
        certbot_executable = SETTINGS.get("CERTBOT_EXECUTABLE", "certbot")
        certbot_extra_args = SETTINGS.get("CERTBOT_EXTRA_ARGS", [])
        
        app = self.get_running_app()
        domain = app.domain
        called_before = False
        
        if hasattr(self, "_called_before"):
            # This method has been called before
            called_before = True
        else:
            self._called_before = True
            
        if hasattr(app, "force_https_app"):
            https_redirect_app = app.force_https_app
            
            # Patch https redirect micro app
            self.patch_microapp(https_redirect_app)
        
        if not os.path.isdir(certbot_root):
            os.makedirs(certbot_root, exist_ok=True) # create certbot root if not directory exists
            
        if not called_before:
            logger.log("CertbotAutoSSL: Running Certbot for SSL renewal", level=logger.DEBUG)
        
        # Ensure domain is set
        if not app.is_domain_set:
            logger.log(
                "CertbotAutoSSL: Domain not set, set using the -d flag",
                level=logger.WARNING
            )
            self.disable_execution = True
            return
         
        while not app.started:
            time.sleep(.5) # wait for app to start
            
        if not called_before:
            logger.log(
                "CertbotAutoSSL: App has been started, executing `certbot`",
                level=logger.DEBUG,
            )
        
        else:
            logger.log("CertbotAutoSSL: Executing `certbot`", level=logger.DEBUG)
        
        # Construct Certbot command
        certbot_command = [
            certbot_executable, "certonly",
            "--webroot", "--webroot-path", certbot_root,
            "--config-dir", certbot_root,
            "--work-dir", joinpaths(str(certbot_root), "work"),
            "--logs-dir", joinpaths(str(certbot_root), "logs"),
            "--cert-name", self.certname,
            "-d", domain,
            "-d", f"www.{domain}",
            "--fullchain-path", SSL_CERT_PATH,
            "--key-path", SSL_CERT_KEY_PATH,
            "--agree-tos", "--non-interactive",
            "--email", certbot_email,
        ]
        
        certbot_command.extend(certbot_extra_args) if certbot_extra_args else None
        
        try:
            result = subprocess.run(
                certbot_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                self.on_cert_success()
            
            else:
                
                if SETTINGS['DEBUG']:
                    logger.log(f"CertbotAutoSSL: Certbot failed with exit code {result.returncode}", level=logger.WARNING)
                    logger.log(f"CertbotAutoSSL: STDERR: \n{result.stderr.strip()}\n", level=logger.WARNING)
                else:
                    logger.log(f"CertbotAutoSSL: Certbot failed with exit code {result.returncode}\n", level=logger.WARNING)
                  
        except FileNotFoundError:
            self.disable_execution = True
            
            if SETTINGS['DEBUG']:
                logger.log("CertbotAutoSSL: Certbot not found. Make sure it's installed and available in PATH", level=logger.WARNING)
                logger.log("CertbotAutoSSL: Try configuring `CERTBOT_EXECUTABLE` if installed\n", level=logger.WARNING)
            else:
                logger.log("CertbotAutoSSL: Certbot not found. Make sure it's installed and available in PATH\n", level=logger.WARNING)
                
        except Exception as e:
            self.disable_execution = True
            logger.log(f"CertbotAutoSSL: Unexpected error: {str(e)}\n", level=logger.WARNING)


# Instantiate the automation
CertbotAutoSSL = BaseCertbotAutoSSL(
    name="Duck SSL Auto Renew",
    description="Automatically creates or renews Let's Encrypt SSL certificates using Certbot",
    start_time="immediate",
    schedules=-1,
    interval= 30 * 3600  # every 30 minutes
)
