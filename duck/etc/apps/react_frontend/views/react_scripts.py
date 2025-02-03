"""
Module containing mediafiles view.
"""

import os

from duck.settings import SETTINGS
from duck.utils.path import (
    joinpaths,
)
from duck.contrib.responses import (
    template_response,
    simple_response,
)
from duck.utils.urlcrack import URL
from duck.http.response import FileResponse, HttpBadRequestResponse
from ..safescript import uncipher_script
    

def react_scripts_view(request):
    """
    React scripts view for serving react scripts defined in settings.py
    """
    from duck.cli.commands.collectscripts import CollectScriptsCommand
    
    query = request.QUERY["URL_QUERY"]
    if "href" in query:
        script = query["href"][0]
        
        try:
            # uncipher script to ensure script path is readable if the script is a local filesystem path.
            script = uncipher_script(script)
        except Exception:
            script = None
        
        if script:
            # Script is provided e.g /react/scripts?href=http://some.site.com/some-script.js
            script_path = CollectScriptsCommand.to_destination_local_path(script)
            
            if not os.path.isfile(script_path):
                if SETTINGS["DEBUG"]:
                    body = """<p>The provided script could not be resolved.
                    Consider using command `duck collectscripts` to collect and serve this script.</p>"""
                    return template_response(HttpBadRequestResponse, body=body)
                return simple_response(HttpBadRequestResponse)
            else:
                return FileResponse(filepath=script_path)
    if SETTINGS["DEBUG"]:
          return template_response(HttpBadRequestResponse, body="The required URL query parameter 'href' is invalid or missing. Please ensure the 'href' parameter is included in the request and contains a valid value")
    return simple_response(HttpBadRequestResponse)
