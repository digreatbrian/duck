"""
Automation for reloading server ssl context on ssl certfile/keyfile change.
"""
import os
import time

from duck.automation import Automation
from duck.logging import logger
from duck.settings import SETTINGS


SSL_CERT_PATH = SETTINGS["SSL_CERTFILE_LOCATION"]

SSL_CERT_KEY_PATH = SETTINGS["SSL_PRIVATE_KEY_LOCATION"]


class BaseDuckSSLWatch(Automation):
    # Automate reloading ssl certificate
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.latest_cert_signature = self.get_file_signature(SSL_CERT_PATH)
        self.latest_cert_key_signature = self.get_file_signature(SSL_CERT_KEY_PATH)
        self.logged_automation_start = False
        self.ssl_sock = None
            
    @staticmethod
    def get_file_signature(path):
        """
        Returns the file signature.
        """
        stats = os.stat(path)
        return (stats.st_mtime, stats.st_ino)

    def on_start(self):
        if not self.logged_automation_start:
            
            if not SETTINGS["ENABLE_HTTPS"]:
                logger.log("DuckSSLWatch: ENABLE_HTTPS is disabled, automation is not going to be run", level=logger.WARNING)
                self.disable_execution = True
            else:
                logger.log("DuckSSLWatch: Watching SSL file changes", level=logger.DEBUG)
            
            self.logged_automation_start = True
                
    def reload_server_certfile(self):
        """
        Reloads server ssl certfile context.
        """
        logger.log("DuckSSLWatch: Server SSL certfile changed, reloading ssl context...", level=logger.WARNING)
        self.ssl_sock.context.load_cert_chain(certfile=SSL_CERT_PATH, keyfile=SSL_CERT_KEY_PATH)
        
    def reload_server_keyfile(self):
        """
        Reloads server ssl cert key context.
        """
        logger.log("DuckSSLWatch: Server SSL keyfile changed, reloading ssl context...", level=logger.WARNING)
        self.ssl_sock.context.load_cert_chain(certfile=SSL_CERT_PATH, keyfile=SSL_CERT_KEY_PATH)
        
    def execute(self):
        """Executes the automation"""
        current_cert_signature = self.get_file_signature(SSL_CERT_PATH)
        current_cert_key_signature = self.get_file_signature(SSL_CERT_KEY_PATH)
        
        if not self.ssl_sock:
            app = self.get_running_app()
            self.ssl_sock = app.server.sock
        
        if current_cert_signature != self.latest_cert_signature:
            # Reload the server ssl certfile context and set the latest cert signature
            self.reload_server_certfile()
            self.latest_cert_signature = current_cert_signature
        
        if current_cert_key_signature != self.latest_cert_key_signature:
            # Reload the server ssl keyfile context and set the latest cert key signature
            self.reload_server_keyfile()
            self.latest_cert_key_signature = current_cert_key_signature


# Instantiate the custom automation with the specified parameters
# This automation is automatically started in new thread
DuckSSLWatch = BaseDuckSSLWatch(
    name="Duck SSL Watch Automation",
    description="Automation for reloading server ssl certificate context",
    start_time="immediate",
    schedules=-1,
    interval=0.5,  # Runs every 0.5 seconds
)
