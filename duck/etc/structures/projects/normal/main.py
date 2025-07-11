#!/usr/bin/env python
"""
Main py script for application creation and execution.
"""

from duck.app import App

app = App(port=8000, addr="0.0.0.0", domain="localhost")

if __name__ == "__main__":
    app.run()
