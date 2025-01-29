"""
Module containing main command class.
"""

from duck.logging import console
from duck.version import server_version


EXAMPLES = """
Examples:
    python -m duck runserver -a 127.0.0.1 -p 8000
    python -m duck makeproject myproject -d ./projects
    python -m duck ssl-gen
    python -m duck django migrate
    python -m duck collectstatic
    python -m duck collectscripts
"""

class MainCommand:
    # main command
        
    @classmethod
    def main(cls, action=None):
        if action == "version":
            console.log_raw(server_version)
        else:
            parser.print_help()
            console.log_raw(EXAMPLES)
