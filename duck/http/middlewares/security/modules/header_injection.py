import re
from urllib.parse import urlparse

# Pre-compile regexes for maximum speed
CRLF_RE = re.compile(r"[\r\n]")

COOKIE_FORMAT_RE = re.compile(r"^[a-zA-Z0-9_-]+=[\w.-]+$")

SCRIPT_TAG_RE = re.compile(r"<[^>]*script[^>]*>", re.IGNORECASE)

CACHE_POISON_RE = re.compile(r"no-cache|no-store|must-revalidate", re.IGNORECASE)


def check_header_injection(headers: dict):
    """
    Ultra-fast detection of header injection, session fixation, XSS, open redirect, and cache poisoning attacks.

    Returns:
        (result, attack_type): Tuple (bool, str) indicating if an attack is found and its type.
    """
    # Cache Host netloc to avoid repeated parsing
    host_url = headers.get("Host", "")
    host_netloc = urlparse(host_url).netloc if host_url else ""

    for header, value in headers.items():
        # Fastest path: CRLF
        if CRLF_RE.search(value):
            return True, "CRLF Injection (Response Splitting)"

        # Fast path: Set-Cookie
        if header == "Set-Cookie":
            if ";" in value:
                return True, "Potential Session Fixation (Multiple Cookies)"
            if not COOKIE_FORMAT_RE.fullmatch(value):
                return True, "Potential Session Fixation (Invalid Cookie Format)"

        # Fast path: XSS
        if SCRIPT_TAG_RE.search(value):
            return True, "Potential XSS (Script Tag Detected)"

        # Fast path: Open Redirect
        if header == "Location":
            parsed_url = urlparse(value)
            # Only parse Host once for efficiency, and compare netlocs
            if not parsed_url.netloc or parsed_url.netloc != host_netloc:
                return True, "Potential Open Redirect (External URL)"

        # Fast path: Cache Poisoning
        if header in {"Cache-Control", "Pragma", "Expires"}:
            if CACHE_POISON_RE.search(value):
                return True, "Potential Cache Poisoning (Anti-Caching Headers)"

    return False, None
