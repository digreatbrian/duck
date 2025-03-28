"""
Module for generating unique identifiers (IDs) for errors and exceptions.
"""
import hashlib
import traceback


def get_error_id(exc_type, exc_value, exc_traceback):
    """Generate a deterministic 6-digit error ID (000000-999999) based on exception details."""
    error_data = f"{exc_type.__name__}|{exc_value}|{''.join(traceback.format_tb(exc_traceback))}"
    hash_value = int(hashlib.md5(error_data.encode()).hexdigest(), 16)  # Convert hash to int
    return f"{hash_value % 1000000:06d}"  # Ensure it's exactly 6 digits with leading zeros
