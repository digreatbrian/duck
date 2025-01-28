"""
Slug Utilities Module

This module provides various utilities for generating, manipulating, and validating slugs.
A slug is a URL-friendly string, typically used in website URLs to represent titles or categories.
These functions allow for tasks such as slug creation from text, slug-to-text conversion, validation,
cleaning, and various string manipulations specific to slugs.

Functions include:
- slugify: Converts a string to a URL-friendly slug.
- unslugify: Converts a slug back to a human-readable string.
- is_valid_slug: Checks if a string is a valid slug.
- generate_slug_from_string: Generates a slug from a given string.
- clean_slug: Cleans up a slug to ensure it's properly formatted.
- split_slug: Splits a slug into individual words.
- join_slug: Joins a list of words into a slug.
- truncate_slug: Truncates a slug to a specified maximum length.
- sanitize_slug: Sanitizes a slug by removing invalid characters.

These utilities are useful for web developers handling slugs for SEO, URLs, or other string-related tasks.
"""

import re
import unicodedata


def slugify(text: str, separator: str = "-") -> str:
    """
    Convert a string to a URL-friendly slug.

    Args:
        text (str): The input string to be converted.
        separator (str): The character to replace spaces with (default is "-").

    Returns:
        str: The generated slug.
    """
    text = unicodedata.normalize('NFKD', text)  # Normalize Unicode characters
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^\w\s-]', '', text)  # Remove non-alphanumeric characters except spaces and hyphens
    text = re.sub(r'[\s-]+', separator, text)  # Replace spaces and hyphens with separator
    text = text.strip(separator)  # Remove leading/trailing separator

    return text


def unslugify(slug: str, separator: str = "-") -> str:
    """
    Convert a slug back to a normal string.

    Args:
        slug (str): The slug to be converted.
        separator (str): The separator used in the slug (default is "-").

    Returns:
        str: The original string.
    """
    slug = slug.replace(separator, " ")  # Replace separator with spaces
    slug = re.sub(r'([a-z])([A-Z])', r'\1 \2', slug)  # Add space before uppercase letters
    return slug.capitalize()  # Capitalize the first letter of the string


def is_valid_slug(slug: str, separator: str = "-") -> bool:
    """
    Check if a string is a valid slug.

    Args:
        slug (str): The slug to be checked.
        separator (str): The separator used in the slug (default is "-").

    Returns:
        bool: True if the string is a valid slug, False otherwise.
    """
    pattern = r'^[a-z0-9' + re.escape(separator) + r']+$'  # Allow lowercase letters, numbers, and separator
    return bool(re.match(pattern, slug))


def generate_slug_from_string(text: str, separator: str = "-") -> str:
    """
    Generate a slug from a given string.

    Args:
        text (str): The input string.
        separator (str): The separator to be used in the generated slug (default is "-").

    Returns:
        str: The generated slug.
    """
    return slugify(text, separator)


def clean_slug(slug: str, separator: str = "-") -> str:
    """
    Clean up a slug by ensuring it's lowercase and properly formatted.

    Args:
        slug (str): The slug to clean.
        separator (str): The separator used in the slug (default is "-").

    Returns:
        str: The cleaned slug.
    """
    slug = slug.strip(separator)  # Remove leading/trailing separators
    slug = re.sub(r'[^a-z0-9' + re.escape(separator) + r']', '', slug)  # Remove invalid characters
    return slug.lower()


def split_slug(slug: str, separator: str = "-") -> list:
    """
    Split a slug into individual words.

    Args:
        slug (str): The slug to be split.
        separator (str): The separator used in the slug (default is "-").

    Returns:
        list: The list of words in the slug.
    """
    return slug.split(separator)


def join_slug(words: list, separator: str = "-") -> str:
    """
    Join a list of words into a slug.

    Args:
        words (list): The list of words to be joined.
        separator (str): The separator to use between words (default is "-").

    Returns:
        str: The joined slug.
    """
    return separator.join(words)


def truncate_slug(slug: str, max_length: int, separator: str = "-") -> str:
    """
    Truncate a slug to a specified maximum length.

    Args:
        slug (str): The slug to truncate.
        max_length (int): The maximum allowed length of the slug.
        separator (str): The separator used in the slug (default is "-").

    Returns:
        str: The truncated slug.
    """
    if len(slug) <= max_length:
        return slug
    
    # Truncate the slug and ensure it doesn't cut in the middle of a word
    truncated = slug[:max_length]
    last_separator = truncated.rfind(separator)
    if last_separator != -1:
        return truncated[:last_separator]
    return truncated


def sanitize_slug(slug: str, separator: str = "-") -> str:
    """
    Sanitize a slug to ensure it contains only valid characters.

    Args:
        slug (str): The slug to sanitize.
        separator (str): The separator used in the slug (default is "-").

    Returns:
        str: The sanitized slug.
    """
    slug = re.sub(r'[^a-z0-9' + re.escape(separator) + r']', '', slug)  # Remove invalid characters
    return slug.lower()
