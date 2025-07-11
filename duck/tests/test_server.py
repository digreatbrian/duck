"""
Minimal test base for Duck webserver using external BASE_URL.
"""
import os
import time
import atexit
import urllib3
import unittest
import threading
import requests
import warnings
import random

from typing import Any, Dict


def set_settings(settings):
    from duck.meta import Meta
    
    os.environ.setdefault("DUCK_SETTINGS_MODULE", "duck.etc.structures.testing.settings")
    Meta.set_metadata('DUCK_EXTRA_SETTINGS', settings)
    

class TestBaseServer(unittest.TestCase):
    """
    Base class for Duck server tests using a predefined BASE_URL.
    """
    settings: Dict[str, Any] = {
        "silent": True,
        "django_silent": True,
        "log_to_file": False,
        "auto_reload": False,
        "force_https": False,
        "enable_https": False,
        "use_django": False,
    }
    
    _app = None
    
    @property
    def app(self):
        from duck.app import App
        from duck.settings import SETTINGS
        
        app = type(self)._app
        
        if not app:
            type(self)._app = app = App(
                addr="localhost",
                port=random.randint(8000, 9000),
                uses_ipv6=False,
                domain="localhost",
                disable_signal_handler=False,
                disable_ipc_handler=True,
            )
        return app
         
    @property
    def base_url(self) -> str:
        return self.app.absolute_uri
        
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
        
        def wait_for_server():
            while not self.app.started:
                time.sleep(.001)
                
        if not self.app.started:
            self.app.run()
            

# Set dynamic testing settings
set_settings(TestBaseServer.settings)


if __name__ == "__main__":
    unittest.main()
