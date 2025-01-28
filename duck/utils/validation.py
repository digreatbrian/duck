"""
Validation Utilities Module

This module provides a set of validation functions to check various types of data commonly used in web development
and application processing, such as strings, email addresses, passwords, IP addresses, credit cards, and more.

Functions include:
- validate_email: Validates email address format.
- validate_phone: Validates phone number format.
- validate_url: Validates URL format.
- validate_username: Validates username format.
- validate_ip_address: Validates IP address (supports both IPv4 and IPv6).
- validate_hex_color: Validates a hex color code.
- validate_credit_card_type: Checks if the credit card belongs to a certain type (e.g., Visa, MasterCard).
- validate_json: Validates if a string is a valid JSON.
- validate_hexadecimal: Validates if the string is a valid hexadecimal number.
- validate_base64: Validates if the string is a valid Base64 encoded string.
- validate_password_strength: Validates if a password meets security requirements.
- validate_time: Validates if a time string is in HH:MM format.
"""

import re
import json
import base64
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validates the format of an email address.
    
    Args:
        email (str): The email address to validate.
    
    Returns:
        bool: True if the email address is valid, False otherwise.
    """
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validates the format of a phone number (supports international formats).
    
    Args:
        phone (str): The phone number to validate.
    
    Returns:
        bool: True if the phone number is valid, False otherwise.
    """
    phone_pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(phone_pattern, phone))


def validate_url(url: str) -> bool:
    """
    Validates the format of a URL.
    
    Args:
        url (str): The URL to validate.
    
    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    url_pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    return bool(re.match(url_pattern, url))


def validate_username(username: str) -> bool:
    """
    Validates if the username is alphanumeric and contains only letters, numbers, and underscores.
    The length should be between 3 to 20 characters.
    
    Args:
        username (str): The username to validate.
    
    Returns:
        bool: True if the username is valid, False otherwise.
    """
    username_pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(username_pattern, username))


def validate_ip_address(ip_address: str) -> bool:
    """
    Validates whether the provided IP address is a valid IPv4 or IPv6 address.
    
    Args:
        ip_address (str): The IP address to validate.
    
    Returns:
        bool: True if the IP address is valid, False otherwise.
    """
    # Check for IPv4
    ipv4_pattern = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                   r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                   r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                   r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    # Check for IPv6
    ipv6_pattern = r'([0-9a-fA-F]{1,4}:){7}([0-9a-fA-F]{1,4})$'

    return bool(re.match(ipv4_pattern, ip_address)) or bool(re.match(ipv6_pattern, ip_address))


def validate_hex_color(color: str) -> bool:
    """
    Validates if the provided string is a valid hex color code.
    
    Args:
        color (str): The color string to validate.
    
    Returns:
        bool: True if the color is a valid hex color code, False otherwise.
    """
    hex_color_pattern = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
    return bool(re.match(hex_color_pattern, color))


def validate_credit_card(card_number: str) -> bool:
    """
    Validates whether the provided credit card number is valid using the Luhn algorithm.
    
    Args:
        card_number (str): The credit card number to validate.

    Returns:
        bool: True if the credit card number is valid, False otherwise.
    """
    # Remove spaces or dashes
    card_number = re.sub(r'[-\s]', '', card_number)
    
    # Validate the card number length
    if not re.match(r'^\d{13,19}$', card_number):
        return False
    
    total = 0
    reverse_digits = card_number[::-1]
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    return total % 10 == 0


def validate_credit_card_type(card_number: str) -> Optional[str]:
    """
    Validates the credit card type based on the number provided.
    Supported card types include: Visa, MasterCard, American Express, Discover.
    
    Args:
        card_number (str): The credit card number to validate.
    
    Returns:
        str: The type of the credit card (e.g., 'Visa', 'MasterCard', etc.), or None if invalid.
    """
    card_number = re.sub(r'\D', '', card_number)  # Remove non-digit characters
    
    # Check for valid card numbers (Luhn algorithm and card type patterns)
    if validate_credit_card(card_number):
        if re.match(r'^4[0-9]{12}(?:[0-9]{3})?$', card_number):  # Visa
            return 'Visa'
        elif re.match(r'^5[1-5][0-9]{14}$', card_number):  # MasterCard
            return 'MasterCard'
        elif re.match(r'^3[47][0-9]{13}$', card_number):  # American Express
            return 'American Express'
        elif re.match(r'^6(?:011|5[0-9]{2})[0-9]{12}$', card_number):  # Discover
            return 'Discover'
    return None


def validate_json(data: str) -> bool:
    """
    Validates whether a string is a valid JSON formatted string.
    
    Args:
        data (str): The string to validate.
    
    Returns:
        bool: True if the string is valid JSON, False otherwise.
    """
    try:
        json.loads(data)
        return True
    except ValueError:
        return False


def validate_hexadecimal(text: str) -> bool:
    """
    Validates if the string is a valid hexadecimal number.
    
    Args:
        text (str): The string to validate.
    
    Returns:
        bool: True if the string is a valid hexadecimal number, False otherwise.
    """
    hex_pattern = r'^[0-9a-fA-F]+$'
    return bool(re.match(hex_pattern, text))


def validate_base64(text: str) -> bool:
    """
    Validates whether the provided string is a valid Base64 encoded string.
    
    Args:
        text (str): The string to validate.
    
    Returns:
        bool: True if the string is valid Base64, False otherwise.
    """
    try:
        base64.b64decode(text, validate=True)
        return True
    except (base64.binascii.Error, ValueError):
        return False


def validate_password_strength(password: str) -> bool:
    """
    Validates the strength of a password. The password must:
    - Be at least 8 characters long.
    - Contain at least one lowercase letter.
    - Contain at least one uppercase letter.
    - Contain at least one number.
    - Contain at least one special character (e.g., !, @, #, $, etc.).
    
    Args:
        password (str): The password to validate.
    
    Returns:
        bool: True if the password meets the strength requirements, False otherwise.
    """
    password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+])[A-Za-z\d!@#$%^&*()_+]{8,}$'
    return bool(re.match(password_pattern, password))


def validate_time(time_str: str) -> bool:
    """
    Validates if the provided time string is in HH:MM format.
    
    Args:
        time_str (str): The time string to validate.
    
    Returns:
        bool: True if the time string is valid, False otherwise.
    """
    time_pattern = r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$'
    return bool(re.match(time_pattern, time_str))
