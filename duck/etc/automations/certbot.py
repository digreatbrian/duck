"""
Automation to obtain or renew an SSL certificate using Certbot.
This ensures your Duck server maintains a valid HTTPS connection
by automatically handling certificate issuance and renewal.
"""
import os
import subprocess

from duck.exceptions.all import SettingsError
from duck.automation import Automation
from duck.settings import SETTINGS
from duck.logging import logger


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

    def execute(self):
        certbot_root = SETTINGS["CERTBOT_ROOT"]
        certbot_email = SETTINGS["CERTBOT_EMAIL"]
        certbot_executable = SETTINGS.get("CERTBOT_EXECUTABLE", "certbot")
        app = self.get_running_app()
        domain = app.domain
        
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

        # Construct Certbot command
        certbot_command = [
            certbot_executable, "certonly", "--webroot",
            "--webroot-path", certbot_root,
            "--cert-name", "duck_ssl_cert",
            "-d", domain,
            "--fullchain-path", SSL_CERT_PATH,
            "--key-path", SSL_CERT_KEY_PATH,
            "--agree-tos", "--non-interactive",
            "--email", certbot_email
        ]
        try:
            result = subprocess.run(
                certbot_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                logger.log("CertbotAutoSSL: SSL certificate successfully created or renewed", level=logger.INFO)
            else:
                logger.log(f"CertbotAutoSSL: Certbot failed with exit code {result.returncode}", level=logger.WARNING)
                logger.log(f"CertbotAutoSSL: STDERR: {result.stderr.strip()}", level=logger.DEBUG)

        except FileNotFoundError:
            logger.log("CertbotAutoSSL: Certbot not found. Make sure it's installed and available in PATH", level=logger.WARNING)
            logger.log("CertbotAutoSSL: Try setting CERTBOT_EXECUTABLE in settings.py", level=logger.WARNING)
            
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
