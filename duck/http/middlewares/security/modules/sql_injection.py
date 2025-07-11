import re
from urllib.parse import urlparse, parse_qs

# Pre-compile whitelist pattern and combined SQLi pattern at module load for optimal performance
WHITELIST_PATTERN = re.compile(r"^[^<>&\"\\]+$")

SQLI_PATTERN = re.compile(
    r"\b(?:SELECT|UPDATE|INSERT|DELETE|DROP|ALTER|UNION|WHERE|GROUP BY|HAVING|ORDER BY|AND|OR|NOT|LIKE|IN|BETWEEN)\b"
    r"|[;=\\\-]"
    r"|'\s*\w+\s*'"
    r'|"\s*\w+\s*"'
    r"|\b(?:admin|password|table_name|column_name)\b",
    re.IGNORECASE
)


def is_safe_url(url: str) -> bool:
    """
    Fast check if all parameter values in URL are safe based on a whitelist.
    Returns True if all parameters are safe, False otherwise.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    # Use generator and short-circuit on first unsafe value
    return all(
        WHITELIST_PATTERN.fullmatch(val)
        for values in params.values()
        for val in values
    )


def check_sql_injection_in_url(url: str) -> bool:
    """
    Ultra-fast SQL injection check in URL string.
    Returns True if potential SQLi detected, else False.
    """
    # Whitelist check first (fast path)
    if is_safe_url(url):
        return False
    # Single pre-compiled regex for fast matching (slow path)
    return bool(SQLI_PATTERN.search(url))
