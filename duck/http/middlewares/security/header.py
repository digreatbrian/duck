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
    Validate a hostname according to RFC 1034/1035 and properly handle IPv4/IPv6 addresses.
    Returns a tuple (is_valid, message).
    """
    # Define the regular expression for a valid hostname label
    hostname_regex = re.compile(
        r"^(?!-)[A-Z\d-]{1,63}(?<!-)$",  # Matches individual labels
        re.IGNORECASE
    )
    
    # Maximum length for a valid hostname (including dots)
    MAX_HOSTNAME_LENGTH = 253
    
    if not host:
        return False, "Hostname is empty"
        
    # Check if the host is an IP address (IPv4 or IPv6)
    try:
        ip = ipaddress.ip_address(host.strip("[]"))  # Remove square brackets for IPv6
        if ip.version == 4:
            return True, "Valid IPv4 address."
        elif ip.version == 6:
            return True, "Valid IPv6 address."
    except ValueError:
        pass  # Not an IP address, continue to validate as a hostname

    # Check total hostname length
    if len(host) > MAX_HOSTNAME_LENGTH:
        return False, f"Hostname exceeds the maximum length of {MAX_HOSTNAME_LENGTH} characters."

    # Split the hostname into labels
    labels = host.split(".")

    # Ensure no empty labels (e.g., "example..com")
    if any(label == "" for label in labels):
        return False, "Hostname contains empty labels (e.g., consecutive dots)."

    # Validate each label against the regex
    for label in labels:
        if not hostname_regex.match(label):
            return False, f"Invalid label '{label}' in hostname. Labels must be 1-63 characters and cannot start or end with a hyphen."

    # If all checks pass, the hostname is valid
    return True, "Hostname is valid."


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
            return cls.request_bad
            
        for allowed_host in cls.allowed_hosts:
            print(f"pattern {allowed_host}: {host} = ", process_wildcards(allowed_host, [host]))
            if process_wildcards(allowed_host, [host]):
                # host is allowed
                return cls.request_ok
        
        request.host_error_msg = f"Disallowed host, you may need to add {host} in ALLOWED_HOSTS"
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
