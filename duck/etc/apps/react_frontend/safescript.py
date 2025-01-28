"""
Module containing functions for ciphering a deciphering scripts for security reasons.

How it works:
    - If script is a local filesystem path, the script will be ciphered and only remote scripts
    in form 'https://some.site.com/script.js' will remain unciphered.
"""

from duck.utils.encrypt import compress_and_encode, decode_and_decompress
from duck.utils.path import is_absolute_url


def cipher_script(script: str):
    """
    This ciphers script which is a local file to avoid exposing the 
    project space path i.e. Sending link in this form '/scripts?href=c://myproject/scripts/react/some.react.script.js' may
    pose a threat to the system.
        
    Returns:
         str: If script is a remote script:
                    - The unciphered script.
                Else:
                    - The script compressed and encoded with zlib and base64.
    """
    if is_absolute_url(script):
         return script
    else:
         return compress_and_encode(script)


def uncipher_script(script: str):
    """
    This unciphers a script to be readable.
        
    Returns:
         str: If script is a remote script:
                    - The script as it is.
                Else:
                    - The unciphered script.
    """
    if is_absolute_url(script):
        return script
    return decode_and_decompress(script)
