"""
Test cases for Duck routes.
"""

import unittest

import requests
from duck.tests.test_server import TestBaseServer


class TestBaseRoutes(TestBaseServer):
    """
    Test class for testing Duck default before creating user custom routes.
    """

    def test_root_url(self):
        """
        Test cases on root url response.
        """
        url = f"http://{self.server_addr}:{self.server_port}/"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)  # check status_code

    def test_about_url(self):
        """
        Test cases on about url response.
        """
        url = f"http://{self.server_addr}:{self.server_port}/about"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)  # check status

    def test_contact_url(self):
        """
        Test cases on contact url response.
        """
        url = f"http://{self.server_addr}:{self.server_port}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)  # check status


class TestMiddlewareResponses(TestBaseRoutes):
    """
    Test different responses from Duck server based on different constructed requests.
    """

    def test_not_found(self):
        """
        Tests whether the processing middleware HttpNotFoundMiddleware is working.
        """
        url = f"http://{self.server_addr}:{self.server_port}/abcdefg"
        response = requests.get(url)
        self.assertEqual(response.status_code, 404)  # check status

    def test_csrf_protection(self):
        """
        Tests if CSRF protection if working according to CSRFMiddleware.
        """
        url = f"http://{self.server_addr}:{self.server_port}"
        response = requests.post(url,
                                 data={
                                     "username": "admin",
                                     "password": "admin1234"
                                 })

        self.assertEqual(response.status_code, 403)  # check status

        response = requests.put(url,
                                data={
                                    "username": "admin",
                                    "password": "admin1234"
                                })
        self.assertEqual(response.status_code, 403)  # check status

        response = requests.delete(url,
                                   data={
                                       "username": "admin",
                                       "password": "admin1234"
                                   })
        self.assertEqual(response.status_code, 403)  # check status

    def test_url_attacks(self):
        """
        Tests for protection against url attacks like SQL injection, Command Injection and XSS.
        """
        url = f"http://{self.server_addr}:{self.server_port}"
        sql_uri = url + "/[--]/hello/world"
        command_uri = url + "/hello/world;echo foo"
        xss_uri = (
            url
            + '/hello/world/?q=<script>console.log("hello world")</script>')

        response = requests.get(sql_uri)
        self.assertEqual(response.status_code, 400)

        response = requests.get(command_uri)
        self.assertEqual(response.status_code, 400)

        response = requests.get(xss_uri)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
