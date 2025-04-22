"""
Automation to obtain or renew an SSL certificate using Certbot.
This ensures your Duck server maintains a valid HTTPS connection
by automatically handling certificate issuance and renewal.
"""
import os
import re
import time
import subprocess

from duck.exceptions.all import SettingsError
from duck.http.core.handler import ResponseHandler
from duck.automation import Automation
from duck.settings import SETTINGS
from duck.logging import logger
from duck.utils.path import joinpaths


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
            "--config-dir", CERTBOT_ROOT,
            "--work-dir", joinpaths(str(CERTBOT_ROOT), "work"),
            "--logs-dir", joinpaths(str(CERTBOT_ROOT), "logs"),
            "--cert-name", "duck_ssl_cert",
            "-d", domain,
            "--fullchain-path", SSL_CERT_PATH,
            "--key-path", SSL_CERT_KEY_PATH,
            "--agree-tos", "--non-interactive",
            "--email", certbot_email,
            "--staging"
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
                logger.log("CertbotAutoSSL: SSL certificate successfully created or renewed\n", level=logger.DEGUG)
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
    interval=12 * 3600  # every 12 hours
)
