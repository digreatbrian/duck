#!/usr/bin/env python
"""
Main py script for application creation and execution.
"""

from duck.app.app import App

app = App(port=8000, addr="127.0.0.1", domain="localhost")

if __name__ == "__main__":
    app.run()
