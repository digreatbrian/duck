"""
Module for testing for URL `XSS`.
"""

import re
from urllib.parse import urlparse, parse_qs

# Pre-compile regex patterns for efficiency
XSS_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"<[^>]*script[^>]*>",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
    r"onmouseover\s*=",
    r"expression\s*\(",
    r"vbscript:",
    r"data:",
    # Removed r"\(" due to high false positive risk
]]

CONTEXT_PATTERNS = {
    "href": [re.compile(r"javascript:", re.IGNORECASE), re.compile(r"data:", re.IGNORECASE)],
    "src": [re.compile(r"javascript:", re.IGNORECASE), re.compile(r"data:", re.IGNORECASE)],
    "style": [re.compile(r"expression\s*\(", re.IGNORECASE)],
}


def check_xss_in_url(url: str) -> (bool, str):
    """Checks a URL for potential XSS vulnerabilities (optimized)."""

    # Check whole URL for patterns
    for pattern in XSS_PATTERNS:
        if pattern.search(url):
            return True, f"Potential XSS detected (pattern: {pattern.pattern})"

    # Parse URL for parameter-specific context-aware checks
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    for tag, patterns in CONTEXT_PATTERNS.items():
        values = params.get(tag, [])
        for value in values:
            for pattern in patterns:
                if pattern.search(value):
                    return True, f"Potential XSS detected in {tag} parameter (pattern: {pattern.pattern})"

    return False, "No XSS vulnerabilities detected in URL"
