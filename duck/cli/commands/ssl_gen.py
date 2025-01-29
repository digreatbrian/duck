"""
Module containing ssl-gen command class.
"""
import os
import sys

from duck.logging import console


class SSLGenCommand:
    # ssl-gen command
    
    @classmethod
    def setup(cls):
        # Setup before command execution
        os.environ.setdefault("DUCK_SETTINGS_MODULE", "duck.etc.structures.projects.testing.settings")
    
    @classmethod
    def main(cls):
        cls.setup()
        cls.ssl_gen()
     
    @classmethod
    def ssl_gen(cls):
        from duck.utils.ssl import generate_server_cert
        try:
            generate_server_cert()
        except Exception as e:
            console.log(f"Error: {str(e)}", level=console.ERROR)
            sys.exit(2)
