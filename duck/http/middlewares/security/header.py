"""
Module for header middlewares.
"""
import re
import ipaddress

from duck.contrib.responses import simple_response, template_response
from duck.http.middlewares import BaseMiddleware
from duck.http.middlewares.security.modules.header_injection import (
    check_header_injection,
)
from duck.http.response import HttpBadRequestResponse, HttpForbiddenRequestResponse
from duck.settings import SETTINGS
from duck.utils.wildcard import process_wildcards


def is_valid_host(host):
    """
    Validate a hostname or IP address, optionally with a port (e.g., 'example.com:8000').
    Returns a tuple (is_valid, message).
    """

    if not host:
        return False, "Hostname is empty"

    # Split host and optional port
    if ':' in host and host.count(':') == 1:
        host, port = host.split(':', 1)
        if not port.isdigit() or not (0 < int(port) < 65536):
            return False, f"Invalid port number '{port}'. Port must be an integer between 1 and 65535."
    elif ':' in host:
        # Possibly an IPv6 address with port — strip brackets and port
        if host.startswith('['):
            try:
                addr, port = host.rsplit(']:', 1)
                ip = ipaddress.ip_address(addr.strip('[]'))
                if not port.isdigit() or not (0 < int(port) < 65536):
                    return False, f"Invalid port '{port}' on IPv6 address."
                return True, f"Valid IPv6 address with port."
            except Exception:
                return False, "Malformed IPv6 address with port."

    # Now validate pure hostname or IP
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
        return True, f"Valid IP address (IPv{ip.version})."
    except ValueError:
        pass  # Not an IP address

    # Validate as hostname
    hostname_regex = re.compile(r"^(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    MAX_HOSTNAME_LENGTH = 253

    if len(host) > MAX_HOSTNAME_LENGTH:
        return False, f"Hostname exceeds the maximum length of {MAX_HOSTNAME_LENGTH} characters."

    labels = host.split(".")
    if any(label == "" for label in labels):
        return False, "Hostname contains empty labels (e.g., consecutive dots)."

    for label in labels:
        if not hostname_regex.match(label):
            return False, f"Invalid label '{label}' in hostname."

    return True, "Valid hostname."


class HostMiddleware(BaseMiddleware):
    """
    Host Middleware class mitigating against requests from
     unknown sources and other host header issues.
    """

    allowed_hosts = SETTINGS["ALLOWED_HOSTS"]

    debug_message: str = "HostMiddleware: Host invalid/unrecognized"

    @classmethod
    def get_error_response(cls, request):
        host = request.headers.get("host")

        if SETTINGS["DEBUG"]:
            body = f"<p>Host invalid/unrecognized</p>"
            
            if hasattr(request, "host_error_msg"):
                if request.host_error_msg:
                    body = f"<p>{request.host_error_msg}</p>"
            response = template_response(HttpForbiddenRequestResponse, body=body)
        else:
            body = None
            response = simple_response(HttpForbiddenRequestResponse)
        return response
    
    @classmethod
    def process_request(cls, request):
        host = request.get_header("host", "").strip()
        valid, reason = is_valid_host(host)
        
        if not valid:
            request.host_error_msg = reason
            cls.debug_message = "HostMiddleware: Host invalid: %s"%(host)
            return cls.request_bad
            
        for allowed_host in cls.allowed_hosts:
            if "]:" in host:
                _host = host.rsplit("]:", 1)[0]
            else:
                _host = host.split(':', 1)[0] if host.count(':') == 1 else host
            
            if process_wildcards(allowed_host, [_host]):
                # host is allowed
                return cls.request_ok
        
        request.host_error_msg = f"Disallowed host, you may need to add {host} in ALLOWED_HOSTS"
        cls.debug_message = "HostMiddleware: Host invalid/unrecognized: %s"%(host)
        return cls.request_bad


class HeaderInjectionMiddleware(BaseMiddleware):
    """
    HeaderInjectionMiddleware class mitigating against various
    header injection attacks like `Potential Session Fixation` (Multiple Cookies),
    `XSS` (Script Tag Detected), `Potential Open Redirect` (External URL),
    `Potential Cache Poisoning` (Anti-Caching Headers).
    """

    debug_message: str = (
        "HeaderInjectionMiddleware: Potential header injection")

    @classmethod
    def get_error_response(cls, request):
        if SETTINGS["DEBUG"]:
            if hasattr(request, "attack_type"):
                body = f"<p>{attack_type.title()}</p>"
            response = template_response(HttpBadRequestResponse, body=body)
        else:
            body = None
            response = simple_response(HttpBadRequestResponse, body=body)

        return response

    @classmethod
    def process_request(cls, request):
        headers = request.headers
        result, attack_type = check_header_injection(headers)
        request.attack_type = attack_type
        if result:
            # potential header injection attack
            return cls.request_bad
        return cls.request_ok
