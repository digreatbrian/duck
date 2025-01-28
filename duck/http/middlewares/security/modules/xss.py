"""Module for testing if XSS is in url"""

import re


def check_xss_in_url(url: str) -> (bool, str):
    """Checks a URL for potential XSS vulnerabilities

    Returns:
          xss_found, message (tuple): Tuple representing if xss found and a message
    """

    # Common XSS patterns
    xss_patterns = [
        r"<[^>]*script[^>]*>",  # Basic script tags
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onmouseover\s*=",
        r"expression\s*\(",  # CSS expressions
        r"vbscript:",
        r"data:",
        r"\(",  # Function calls
    ]

    # Context-aware patterns
    context_patterns = {
        "href": [r"javascript:", r"data:"],
        "src": [r"javascript:", r"data:"],
        "style": [r"expression\s*\("],
    }

    # Analyze URL parameters and fragments
    for pattern in xss_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return (
                True,
                "Potential XSS detected (pattern: {})".format(pattern),
            )

    # Context-aware check in URL
    for tag, patterns in context_patterns.items():
        matches = re.findall(rf"{tag}=([^&]+)", url, re.IGNORECASE)
        for match in matches:
            for pattern in patterns:
                if re.search(pattern, match, re.IGNORECASE):
                    return (
                        True,
                        f"Potential XSS detected in {tag} parameter (pattern: {pattern})",
                    )

    return (False, "No XSS vulnerabilities detected in URL")
