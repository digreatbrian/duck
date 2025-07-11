"""
Network helper utilily tools.
"""
import socket


def is_ipv6(ip_address: str) -> bool:
    """
    Check if the provided IP address is a valid IPv6 address.
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip_address)
        return True
    except socket.error:
        return False


def is_ipv4(ip_address: str) -> bool:
    """
    Check if the provided IP address is a valid IPv4 address.
    """
    try:
        socket.inet_pton(socket.AF_INET, ip_address)
        return True
    except socket.error:
        return False


def is_domain(name) -> bool:
    """
    Check if the provided name is a valid domain name.
    """
    return all(
        [len(part) <= 63 and part.isalnum() for part in name.split(".")])
