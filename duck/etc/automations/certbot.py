"""
Automation to obtain or renew an SSL certificate using Certbot.
This ensures your Duck server maintains a valid HTTPS connection
by automatically handling certificate issuance and renewal.
"""
import os
import re
import time
import subprocess
import configparser

from duck.exceptions.all import SettingsError
from duck.http.core.handler import ResponseHandler
from duck.automation import Automation
from duck.settings import SETTINGS
from duck.logging import logger
from duck.utils.path import joinpaths
from duck.utils.filelock import (
    unlock_file,
    open_and_lock,
)


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
            logger.log("CertbotAutoSSL: FORCE_HTTPS is disabled, this is strictly required", level=logger.WARNING)
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
            extract_config_values("/etc/letsencrypt/renewal/example.com.conf", "fullchain", "privkey")
            => { "fullchain": "/etc/letsencrypt/live/example.com/fullchain.pem",
                 "privkey": "/etc/letsencrypt/live/example.com/privkey.pem" }
        """
        values = {key: None for key in args}
    
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
        certbot_root = SETTINGS["CERTBOT_ROOT"]
        config_path = joinpaths(str(certbot_root), f"renewal/{self.certname}.conf")
        config = self.extract_config_values(config_path, "fullchain", "privkey")
        
        if SETTINGS["DEBUG"]:
            # Only log in Debug mode
            logger.log("CertbotAutoSSL: Copying Certificate Credentials", level=logger.DEBUG)
        
        fullchain_path = config.get("fullchain")
        key_path = config.get("privkey")
        
        cert_data = None
        key_data = None
        
        if SETTINGS["DEBUG"]:
            # Only log in Debug mode
            logger.log("CertbotAutoSSL: Reading Fullchain and Private key credentials", level=logger.DEBUG)
        
        with (
            open_and_lock(fullchain_path, "r") as cert_file,
            open_and_lock(key_path, "r") as key_file
        ):
            cert_data = cert_file.read()
            key_data = key_file.read()
            
            # Unlock file descriptors
            unlock_file(cert_file)
            unlock_file(key_file)
        
        if SETTINGS["DEBUG"]:
            # Only log in Debug mode
            logger.log(f"CertbotAutoSSL: Writing SSL credentials to {certbot_root}", level=logger.DEBUG)
        
        with (
            open_and_lock(SSL_CERT_PATH, "w") as cert_file,
            open_and_lock(SSL_CERT_KEY_PATH, "w") as key_file
        ):
            cert_file.write(cert_data)
            
            if SETTINGS["DEBUG"]:
                logger.log(f"CertbotAutoSSL: Wrote SSL fullchain credential to {SSL_CERT_PATH}", level=logger.DEBUG)
            
            key_file.write(key_data)
            
            # Unlock all files immediately after writing to last file
            unlock_file(cert_file)
            unlock_file(key_file)
            
            if SETTINGS["DEBUG"]:
                logger.log(f"CertbotAutoSSL: Wrote SSL private key credential to {SSL_CERT_KEY_PATH}", level=logger.DEBUG)
                
        logger.log(f"CertbotAutoSSL: Wrote SSL credentials successfully", level=logger.DEBUG)

    def execute(self):
        certbot_root = SETTINGS["CERTBOT_ROOT"]
        certbot_email = SETTINGS["CERTBOT_EMAIL"]
        certbot_executable = SETTINGS.get("CERTBOT_EXECUTABLE", "certbot")
        certbot_extra_args = SETTINGS.get("CERTBOT_EXTRA_ARGS", [])
        
        app = self.get_running_app()
        domain = app.domain
        
        if hasattr(app, "force_https_app"):
            https_redirect_app = app.force_https_app
            
            # Patch https redirect micro app
            self.patch_microapp(https_redirect_app)
        
        if not os.path.isdir(certbot_root):
            os.makedirs(certbot_root, exist_ok=True) # create certbot root if not directory exists
            
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
            
        logger.log(
            "CertbotAutoSSL: App has been started, executing `certbot`...",
            level=logger.DEBUG,
        )
        
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
                logger.log("CertbotAutoSSL: SSL certificate successfully created or renewed\n", level=logger.DEBUG)
                self.on_cert_success()
            else:
                logger.log(f"CertbotAutoSSL: Certbot failed with exit code {result.returncode}", level=logger.WARNING)
                logger.log(f"CertbotAutoSSL: STDERR: \n{result.stderr.strip()}\n", level=logger.WARNING)

        except FileNotFoundError:
            logger.log("CertbotAutoSSL: Certbot not found. Make sure it's installed and available in PATH", level=logger.WARNING)
            logger.log("CertbotAutoSSL: Try configuring `CERTBOT_EXECUTABLE` in settings.py if installed\n", level=logger.WARNING)
            
        except Exception as e:
            logger.log(f"CertbotAutoSSL: Unexpected error: {str(e)}", level=logger.WARNING)


# Instantiate the automation
CertbotAutoSSL = BaseCertbotAutoSSL(
    name="Duck SSL Auto Renew",
    description="Automatically creates or renews Let's Encrypt SSL certificates using Certbot",
    start_time="immediate",
    schedules=-1,
    interval= 30 * 24 * 3600  # every 30 days
)

