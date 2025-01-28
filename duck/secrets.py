"""
Provides utilities for generating and managing secure secrets and tokens for Duck applications.

This module generates and manages various secrets, including URL-safe tokens, ASCII-based secrets, 
and randomized domain names. The secrets are stored in environment variables to ensure they 
remain accessible and secure throughout the application lifecycle.

Main Components:
- `generate_secret()`: Generates a URL-safe, cryptographically secure token.
- `generate_ascii_secret()`: Generates a secure ASCII-only token for specific cases.
- `generate_random_domain()`: Provides a randomized domain name for secure communication.

Environment Variables:
- `DXS`: Stores a URL-safe token, generated if not already set.
- `RXS`: Stores an ASCII-based token, generated if not already set, used in secret headers.
- `DXSD`: Stores a randomized domain name, generated if not already set.

These environment variables are intended to enhance security by obfuscating sensitive values. 
When variables are not set initially, secure values are generated and assigned to them dynamically.
"""

import hashlib
import os
import random
import string

from duck.utils.rand_domain import generate_random_domain


def generate_ascii_secret(length=16):
    letters = (string.ascii_letters
               )  # Contains both lowercase and uppercase letters
    token = "".join(random.choice(letters) for _ in range(length))
    return token


def generate_secret() -> str:
    """
    Generates a secure random URL-safe token.

    Returns:
        str: A URL-safe token for use as a secret.
    """
    randstr = str(random.random())
    return hashlib.md5(randstr.encode("utf-8")).hexdigest()


# Check if the environment variable 'DXS' is set, if not, generate a new secret
if not os.environ.get("DXS"):
    # Use a variable name that doesn't make sense for improved security
    DUCK_SECRET = os.environ["DXS"] = generate_secret()
else:
    DUCK_SECRET = os.environ["DXS"]

# Check if the environment variable 'RXS' is set, if not, generate a new secret
if not os.environ.get("RXS"):
    # Use a variable name that doesn't make sense for improved security
    RAND_SECRET = os.environ["RXS"] = (
        generate_ascii_secret()
    )  # leave this to be ascii only, will be used to contruct secret headers
else:
    RAND_SECRET = os.environ["RXS"]

# Check if the environment variable 'DXSD' is set, if not, generate a new secret
if not os.environ.get("DXSD"):
    # Use a variable name that doesn't make sense for improved security
    SECRET_DOMAIN = os.environ["DXSD"] = generate_random_domain()
else:
    SECRET_DOMAIN = os.environ["DXSD"]
