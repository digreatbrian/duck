"""
Test cases for Duck routes and middleware behavior.

This module ensures that default server routes and middleware responses 
conform to expected HTTP status codes and security standards.
"""

import unittest
import requests

from duck.tests.test_server import TestBaseServer


class TestBaseRoutes(TestBaseServer):
    """
    Test class for verifying default routes on the Duck server
    before any user-defined routes are registered.
    """

    def test_root_url(self):
        """
        Test that the root URL ("/") returns a 200 OK status.

        This ensures the base route is properly registered and reachable.
        """
        response = requests.get(f"{self.base_url}/", verify=False)
        self.assertEqual(response.status_code, 200)

    def test_about_url(self):
        """
        Test that the "/about" route returns a 200 OK response.

        Verifies static informational routes are accessible by default.
        """
        response = requests.get(f"{self.base_url}/about", verify=False)
        self.assertEqual(response.status_code, 200)

    def test_contact_url(self):
        """
        Test that the "/contact" route returns a 200 OK response.

        Ensures all default informational routes are properly served.
        """
        response = requests.get(f"{self.base_url}/contact", verify=False)
        self.assertEqual(response.status_code, 200)


class TestMiddlewareResponses(TestBaseRoutes):
    """
    Test class for validating server-side middleware behavior,
    including error handling, CSRF protection, and input sanitization.
    """
    
    def test_not_found(self):
        """
        Test that the server returns a 404 status for unknown paths.

        This ensures that HttpNotFoundMiddleware is correctly handling
        routes that are not explicitly defined.
        """
        response = requests.get(f"{self.base_url}/abcdefg", verify=False)
        self.assertEqual(response.status_code, 404)

    def test_csrf_protection(self):
        """
        Test that unsafe methods (POST, PUT, DELETE) are blocked without CSRF token.

        This validates that CSRFMiddleware is enforcing protection on modifying requests
        that lack proper authorization headers or tokens.
        """
        for method in [requests.post, requests.put, requests.delete]:
            with self.subTest(method=method.__name__):
                response = method(self.base_url, data={"username": "admin", "password": "admin1234"}, verify=False)
                self.assertEqual(response.status_code, 403)

    def test_url_attacks(self):
        """
        Test server's protection against common URL-based attacks.

        Includes:
        - SQL injection-style malformed paths
        - Command injection attempts
        - XSS injection via query parameters

        Ensures input validation middleware (e.g., HttpSanitizationMiddleware) 
        correctly blocks suspicious or malformed requests.
        """
        attack_paths = [
            "/[--]/hello/world",  # Simulated SQL injection
            "/hello/world;echo foo&",  # Simulated command injection
            "/hello/world/?q=<script>console.log('hello')</script>"  # XSS vector
        ]

        for path in attack_paths:
            with self.subTest(path=path):
                response = requests.get(self.base_url + path, verify=False)
                self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
 