"""
Certbot Webroot Blueprint

This module defines a blueprint for serving Certbot ACME challenge verification files.
It supports the Let's Encrypt webroot approach for SSL certificate issuance and renewal.

To function correctly, ensure the `CERTBOT_ROOT` setting is defined in your `settings.py` file.
This should point to the directory where Certbot writes its verification files (typically `.well-known/acme-challenge`).

References:
- Let's Encrypt: https://letsencrypt.org
- Certbot Webroot Plugin: https://eff.org/certbot
"""

import os

from duck.settings import SETTINGS
from duck.exceptions.all import SettingsError
from duck.http.response import FileResponse
from duck.utils.path import normalize_url_path, joinpaths
from duck.shortcuts import not_found404


if "CERTBOT_ROOT" not in SETTINGS:
    raise SettingsError(
        "Missing 'CERTBOT_ROOT' in settings. "
        "Please define the 'CERTBOT_ROOT' variable in your settings.py configuration file. "
        "It is required for SSL certificate management."
    )

# Normalize the path for compatibility across operating systems
CERTBOT_ROOT = str(SETTINGS["CERTBOT_ROOT"])


def webroot_view(request):
    """
    Serve ACME verification files for Certbot.

    This view responds to incoming HTTP requests for files located under the
    `.well-known/acme-challenge` path as required by Certbot when using the webroot plugin.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        FileResponse: If the requested file exists in CERTBOT_ROOT.
        Response: 404 Not Found if the file does not exist.
    """
    file_path = joinpaths(CERTBOT_ROOT, request.path)
    
    if not os.path.isfile(file_path):
        return not_found404(body=f"<p>Nothing matches the provided URI: {request.path}</p>")

    return FileResponse(file_path)
