"""
Test cases for Duck webserver.
"""

import os
import random
import shutil
import subprocess
import time
import unittest
import warnings
from typing import Any, Optional

import requests


class TestBaseServer(unittest.TestCase):
    """
    Base test class for testing the Duck server.

    Notes:
        - A single server instance is shared across all subclasses unless a new instance is explicitly requested.
    """

    PROJECT_NAME: str = "testproject"
    SERVER_START_DELAY: int = 4
    PORT_RANGE: tuple[int, int] = (8000, 9000)

    server_started: bool = False  # Shared flag for all subclasses
    _server_addr: Optional[str] = None
    _server_port: Optional[int] = None

    force_new_instance: bool = (
        False  # Subclasses can override this to start a new server instance
    )

    settings = {
        "silent": True,
        "django_silent": True,
        "log_to_file": False,
        "auto_reload": False,
        "force_https": False,
        "enable_https": False,
        "use_django": False,
    }

    @property
    def server_addr(self) -> str:
        """Returns the server's IP address or hostname."""
        if not self._server_addr:
            raise AttributeError(
                "Server not started yet! Call `start_server` first.")
        return self._server_addr

    @property
    def server_port(self) -> int:
        """Returns the server's port."""
        if not self._server_port:
            raise AttributeError(
                "Server not started yet! Call `start_server` first.")
        return self._server_port

    @property
    def project_dir(self) -> str:
        return self.PROJECT_NAME

    def prepare_project(self) -> None:
        """Clears and sets up the test project directory."""
        if os.path.isdir(self.project_dir):
            shutil.rmtree(self.project_dir)
        os.makedirs(self.project_dir, exist_ok=True)

    def create_settings_file(self, settings: dict[str, Any]) -> None:
        """
        Creates a settings file with provided custom settings.

        Args:
            settings: Dictionary containing settings to write to the file (keys are case insensitive).
        """
        if not settings:
            return

        settings_file = os.path.join(self.project_dir, "settings.py")
        mode = "w" if os.path.isfile(settings_file) else "x"

        try:
            with open(settings_file, mode) as file:
                file.write(
                    f'"""\nAuto-generated settings for test cases.\n"""\n')
                for key, value in settings.items():
                    file.write(f"{key.upper()} = {value}\n")
        except Exception as e:
            raise IOError(f"Error creating settings file: {e}")

    def set_settings_file(self) -> None:
        """Sets the environment variable for the settings module."""
        os.environ["DUCK_SETTINGS_MODULE"] = (
            f'{self.project_dir.replace("/", ".").strip(".")}.settings')

    def _start_server(self, settings: Optional[dict[str, Any]] = None) -> None:
        """
        Starts the Duck server.

        Args:
            settings: Optional settings to use for the server.
        """
        self._server_port = random.randint(*self.PORT_RANGE)
        self._server_addr = "127.0.0.1"

        if settings:
            self.create_settings_file(settings)
        self.set_settings_file()
        subprocess.Popen(
            [
                "python",
                "-m",
                "duck",
                "runserver",
                "-p",
                str(self._server_port),
                "-a",
                self._server_addr,
            ],
            start_new_session=False,
        )
        time.sleep(self.SERVER_START_DELAY)
        TestBaseServer.server_started = True
        TestBaseServer._server_addr = self._server_addr
        TestBaseServer._server_port = self._server_port

    def start_server(self) -> None:
        """
        Initializes and starts the server.

        Notes:
            - If `force_new_instance` is True, starts a new server even if one is already running.
        """
        if not self.force_new_instance and TestBaseServer.server_started:
            self._server_addr = TestBaseServer._server_addr
            self._server_port = TestBaseServer._server_port
        else:
            self._start_server(self.settings)

    def test_server_start(self) -> None:
        """Tests if the server has started successfully."""
        if not self.server_started:
            try:
                url = f"http://{self.server_addr}:{self.server_port}"
                response = requests.get(url)
                response.raise_for_status()
                self.server_started = True
            except requests.RequestException:
                self.server_started = False
        self.assertTrue(self.server_started)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def setUp(self) -> None:
        """Runs before every test."""
        warnings.simplefilter(
            "ignore",
            ResourceWarning)  # Suppress ResourceWarnings specifically
        self.prepare_project()
        self.start_server()


if __name__ == "__main__":
    unittest.main()
