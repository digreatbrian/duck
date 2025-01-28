"""
Module containing middleware class for Fixing request headers before reaching to Django server.
"""
from duck.settings import SETTINGS
from duck.http.middlewares import BaseMiddleware
from duck.utils.urlcrack import URL


class DjangoHeaderFixerMiddleware(BaseMiddleware):
    @classmethod
    def process_request(cls, request):
        secret_domain = SETTINGS["DJANGO_SHARED_SECRET_DOMAIN"]
        if not secret_domain:
            return
        host_obj = URL(request.host)
        host_obj.host = secret_domain
        
        # Also set ports to None because Django doesnt support Host with port according to RFC 1034/1035.
        host_obj.port = None
        
        # Headers to modify
        modify_headers = {
            'host': host_obj.to_str(),
        }
        
        if request.referer:
            # Rebuild referer as it is with new hostname
            referer = URL(request.referer)
            referer.host = secret_domain
            referer.port = None
            modify_headers['referer'] = referer.to_str()
        
        if request.origin:
            origin = URL(request.origin)
            origin.host = secret_domain
            origin.port = None
            modify_headers['origin'] = origin.to_str()
        
        # Modify some headers: host, referer and origin
        request.headers.update(modify_headers)
