"""
Module containing middleware classes for inspecting urls for various attacks like XSS and SQL Injection.
"""

from duck.http.middlewares import BaseMiddleware
from duck.http.middlewares.security.modules.command_injection import (
    check_command_injection_in_url,
)
from duck.http.middlewares.security.modules.sql_injection import (
    check_sql_injection_in_url,
)
from duck.http.middlewares.security.modules.xss import check_xss_in_url
from duck.http.response import HttpBadRequestResponse
from duck.settings import SETTINGS
from duck.shortcuts import simple_response, template_response
from duck.utils.path import is_good_url_path


class URLSecurityMiddleware(BaseMiddleware):
    """
    URLSecurityMiddleware class checking URL correctness.
    """

    debug_message: str = "URLSecurityMiddleware: Malformed URL"

    @classmethod
    def get_error_response(cls, request):
        if SETTINGS["DEBUG"]:
            body = "<p>URL is Invalid or Malformed.</p>"
            response = template_response(HttpBadRequestResponse, body=body)
        else:
            body = None
            response = simple_response(HttpBadRequestResponse, body=body)
        return response
        
    @classmethod
    def process_request(cls, request):
        url_path_ok = is_good_url_path(request.path)
        if url_path_ok:
            return cls.request_ok
        return cls.request_bad


class XSSMiddleware(BaseMiddleware):
    """
    XSSMiddleware class mitigating against XSS attacks.
    """

    debug_message: str = "XSSMiddleware: Potential url xss"

    @classmethod
    def get_error_response(cls, request):
        if SETTINGS["DEBUG"]:
            body = "<p>URL contains Potential XSS Attack Signature.</p>"
            if hasattr(request, "url_xss_attack"):
                body = f"<p>{request.url_xss_attack}</p>"
            response = template_response(HttpBadRequestResponse, body=body)
        else:
            body = None
            response = simple_response(HttpBadRequestResponse, body=body)
        return response

    @classmethod
    def process_request(cls, request):
        # check for xss in url
        url = request.fullpath
        xss_found, msg = check_xss_in_url(url)
        if xss_found:
            request.url_xss_attack = msg
            return cls.request_bad
        return cls.request_ok


class SQLInjectionMiddleware(BaseMiddleware):
    """
    SQLInjectionMiddleware class mitigating against SQL injection attacks.
    """

    debug_message: str = "SQLInjectionMiddleware: Potential URL sql injection"

    @classmethod
    def get_error_response(cls, request):
        if SETTINGS["DEBUG"]:
            body = "<p>URL contains Potential SQL Injection.</p>"
            response = template_response(HttpBadRequestResponse, body=body)
        else:
            body = None
            response = simple_response(HttpBadRequestResponse, body=body)
        return response

    @classmethod
    def process_request(cls, request):
        # check for sql injection in url
        url = request.fullpath
        if not check_sql_injection_in_url(url):
            return cls.request_ok
        return cls.request_bad


class CommandInjectionMiddleware(BaseMiddleware):
    """
    CommandInjectionMiddleware class mitigating against command injection attacks.
    """

    debug_message: str = (
        "CommandInjectionMiddleware: Potential URL command injection")

    @classmethod
    def get_error_response(cls, request):
        if SETTINGS["DEBUG"]:
            body = "<p>URL contains Potential Command Injection.</p>"
            response = template_response(HttpBadRequestResponse, body=body)
        else:
            body = None
            response = simple_response(HttpBadRequestResponse, body=body)
        return response

    @classmethod
    def process_request(cls, request):
        # check for command injection in url
        url = request.fullpath
        if not check_command_injection_in_url(url.split(
                "?", 1)[0]) and not check_command_injection_in_url(
                    url.replace("&", "")):
            return cls.request_ok
        return cls.request_bad
