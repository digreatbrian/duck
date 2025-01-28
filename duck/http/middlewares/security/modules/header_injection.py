import re
from urllib.parse import urlparse


def check_header_injection(headers: dict):
    """Checks if there is a potential header injection attack in headers

    Returns:
        result, attack_type: Tuple respresenting result if an attack found alongside the attack type
    """
    for header, value in headers.items():
        if re.search(r"[\r\n]", value):  # CRLF
            return True, "CRLF Injection (Response Splitting)"

        # Improved session fixation check
        if header == "Set-Cookie":
            if ";" in value:  # Multiple cookie attributes
                return True, "Potential Session Fixation (Multiple Cookies)"
            if not re.match(r"^[a-zA-Z0-9_-]+=[\w.-]+$",
                            value):  # Invalid cookie format
                return (
                    True,
                    "Potential Session Fixation (Invalid Cookie Format)",
                )

        # Improved XSS check using a more comprehensive regex
        if re.search(
                r"<[^>]*script[^>]*>", value,
                re.IGNORECASE):  # Looks for script tags with any attributes
            return True, "Potential XSS (Script Tag Detected)"

        # Improved open redirect check
        if header == "Location":
            parsed_url = urlparse(value)
            if (not parsed_url.netloc or parsed_url.netloc != urlparse(
                    headers.get("Host", "")).netloc):
                return True, "Potential Open Redirect (External URL)"

        # Check for cache poisoning (simplified)
        if header in ["Cache-Control", "Pragma", "Expires"]:
            if re.search(r"no-cache|no-store|must-revalidate", value,
                         re.IGNORECASE):
                return True, "Potential Cache Poisoning (Anti-Caching Headers)"

    return False, None
