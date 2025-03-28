"""
Extraction Utilities Module

This module provides various utilities to extract specific types of information from a given text.
These utilities can be used for extracting URLs, email addresses, phone numbers, hashtags, mentions,
and other patterns that are commonly needed in text processing tasks such as web scraping, form validation,
or text analysis.

Functions include:
- `extract_urls`: Extracts all URLs from a given text.
- `extract_emails`: Extracts all email addresses from a given text.
- `extract_phone_numbers`: Extracts all phone numbers from a given text.
- `extract_hashtags`: Extracts all hashtags from a given text.
- `extract_mentions`: Extracts all mentions (usernames) from a given text.
- extract_dates: Extracts all date-like patterns from a given text.
- `extract_currency`: Extracts all currency values from a given text.
- `extract_ips`: Extracts all IP addresses from a given text.
- `extract_social_handles`: Extracts social media handles (like Twitter, Instagram) from a given text.
- `extract_hex_colors`: Extracts all hex color codes from a given text.
- `extract_skus`: Extracts all product SKUs (Stock Keeping Units) from a given text.
"""

import re
from typing import List


def extract_urls(text: str) -> List[str]:
    """
    Extracts all URLs from the provided text.
    """
    url_pattern = r'https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,6}(?:/[\w/-]*)*'
    return re.findall(url_pattern, text)


def extract_emails(text: str) -> List[str]:
    """
    Extracts all email addresses from the provided text.
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zAZ]{2,}'
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extracts all phone numbers from the provided text.
    """
    phone_pattern = r'\+??\d{1,4}?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}'
    return re.findall(phone_pattern, text)


def extract_hashtags(text: str) -> List[str]:
    """
    Extracts all hashtags from the provided text.
    """
    hashtag_pattern = r'#\w+'
    return re.findall(hashtag_pattern, text)


def extract_mentions(text: str) -> List[str]:
    """
    Extracts all mentions (usernames) from the provided text.
    """
    mention_pattern = r'@\w+'
    return re.findall(mention_pattern, text)


def extract_dates(text: str) -> List[str]:
    """
    Extracts all date-like patterns from the provided text.
    """
    date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b'
    return re.findall(date_pattern, text)


def extract_currency(text: str) -> List[str]:
    """
    Extracts all currency values from the provided text.
    """
    currency_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s?\b(?:USD|EUR|GBP|INR)\b'
    return re.findall(currency_pattern, text)


def extract_ips(text: str) -> List[str]:
    """
    Extracts all IP addresses (IPv4) from the provided text.

    Args:
        text (str): The input string to extract IP addresses from.

    Returns:
        list: A list of extracted IP addresses.
    """
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    return re.findall(ip_pattern, text)


def extract_social_handles(text: str) -> List[str]:
    """
    Extracts social media handles from the provided text (e.g., @username).

    Args:
        text (str): The input string to extract social media handles from.

    Returns:
        list: A list of extracted social media handles.
    """
    social_pattern = r'@[\w]+'
    return re.findall(social_pattern, text)


def extract_hex_colors(text: str) -> List[str]:
    """
    Extracts all hex color codes from the provided text.

    Args:
        text (str): The input string to extract hex color codes from.

    Returns:
        list: A list of extracted hex color codes.
    """
    hex_color_pattern = r'#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}'
    return re.findall(hex_color_pattern, text)


def extract_skus(text: str) -> List[str]:
    """
    Extracts all product SKUs (Stock Keeping Units) from the provided text.

    Args:
        text (str): The input string to extract SKUs from.

    Returns:
        list: A list of extracted SKUs.
    """
    sku_pattern = r'[A-Za-z0-9]{8,12}'
    return re.findall(sku_pattern, text)
