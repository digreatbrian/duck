"""
Module for safer comparison of sensitive information without having to worry about timing attacks
"""

import hmac


def constant_time_compare(str_a: str, str_b: str):
    """
    This is a constant time comparison function with a sense of avoiding timing attacks, meaning,
    nomatter how short or long the 2 strings are, the time of comparing any kind of string is
    the same (constant), hence tackling timing attacks.
    """
    assert isinstance(str_a, str) and isinstance(
        str_b, str), "Only strings are allowed for both the arguments"
    return hmac.compare_digest(str_a, str_b)
