"""
Duck: Advanced Web Server, Framework, and Proxy
===============================================

**Duck** is a new advanced, Python-based **web server**, **framework**, and **proxy** designed 
for seamless integration with **Django**. It simplifies **web development** by providing 
built-in **HTTPS support**, simple **SSL certificate generation**, and powerful 
**customization options**. 

With **Duck**, developers can quickly deploy secure, high-performance applications with minimal 
configuration. Ideal for creating scalable, secure, and customizable **web solutions**, **Duck** 
streamlines the development process while ensuring top-notch security and performance.

Quick Start Example
---------------------------------

To start using Duck, initialize an ``App`` instance with your desired port and address, 
then run the application:

```py
from duck.app import App

app = App(port=5000, addr='127.0.0.1', domain='localhost')

if __name__ == '__main__':
    app.run()
```
"""

from duck.version import version

__author__ = "Brian Musakwa"
__email__ = "digreatbrian@gmail.com"
__version__ = version
