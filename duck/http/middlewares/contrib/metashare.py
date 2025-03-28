"""
Module containing middleware for sharing request META as headers.

Notes:
- These headers generated from META will be a unique header starting with a secure string prefix.
"""
import ast

from typing import Dict

from duck.secrets import RAND_SECRET
from duck.http.middlewares import BaseMiddleware
from duck.utils.encrypt import (
    compress_and_encode,
    decode_and_decompress,
)


class MetaShareMiddleware(BaseMiddleware):
    """
    This middleware compiles request.META and inject everything as headers, but each header key will be 
    startwith certain secure string prefix so that it is easy to identify as data that is meant to be shared.
    
    ``` {note}
    If there is a key in `request.META` which startswith the `secure_string_prefix`,
    the key will be skipped as this assumes that this middleware has already been used on
    `request.META` to come up with the key with the `secure_string_prefix`.
    ```
    
    """
    @classmethod
    def resolve_meta_from_headers(cls, headers: Dict) -> Dict:
        """
        Extracts and resolves custom META information from HTTP headers.
    
        This method processes HTTP headers prefixed with a specific secret identifier, 
        decodes and decompresses their values, and updates the `META` attribute of the 
        `request` object with the resolved metadata. Headers are expected to follow the 
        format `<compressed_and_encoded_data>@<type>`, where `<type>` is the data type 
        (e.g., int, str, dict, etc.) to which the value should be converted.
    
        Args:
            headers: The HTTP headers to be resolved.
    
        Workflow:
        1. Retrieves a secret prefix derived from the first 8 characters of the `RAND_SECRET` 
               variable to identify custom headers (e.g., `X-<secret>-<key>`).
        2. Iterates through request headers:
             - If a header matches the prefix, it is processed:
                 - Decodes, decompresses, and converts the value to its original type using 
                      predefined converters (e.g., `int`, `dict`, `bool`, etc.).
                    
        Returns:
             Dict: The dictionary with the new meta (keys converted to uppercase)
    
        Notes:
        - Custom headers must follow the format `<compressed_and_encoded_data>@<type>`.
        - Headers already processed by the middleware are skipped.
        - The `ast.literal_eval` function is used to convert string representations of complex data 
           types (e.g., dict, list, tuple), which may pose a security risk if untrusted 
           data is passed.
        - Errors during processing (e.g., incorrect header format) are silently ignored.
    
        Example:
        
        ```py
        headers = {
            "X-Abcdef12-User-Id": "eJwL8Q0BA...@int",  # Encoded and compressed integer
            "X-Abcdef12-Settings": "eJwL...@dict",       # Encoded and compressed dictionary
        }
            
        cls.resolve_meta_from_headers(headers)
            
        print(request.META)
        # Outputs: {
        #     "USER_ID": 123,
        #     "SETTINGS": {"theme": "dark", "language": "en"}
        # }
        ```
        
        Warnings:
        - Using `eval` can lead to security vulnerabilities if headers contain untrusted data.
        - Ensure that only trusted data is processed by this method to mitigate risks.
        """
        meta = {}
        secret = RAND_SECRET[:8].title()
        match_header_prefix = f"X-{secret}-"
        
        # Type converters for converting data to correct datatype
        type_converters = {
            "int": int,
            "str": str,
            "float": float,
            "dict": ast.literal_eval,  # Using eval to convert string to dict
            "tuple": ast.literal_eval,  # Using eval to convert string to tuple
            "list": ast.literal_eval,  # Using eval to convert string to list
            "set": ast.literal_eval,  # Using eval to convert string to set
            "bool": ast.literal_eval,  # Using eval to convert string to bool
        }
        for header, value in headers.items():
            if header.startswith(match_header_prefix):
                try:
                    value, value_type = value.split("@")
                    value = decode_and_decompress(value)
                    
                    # Convert value to appropriate type 
                    converter = type_converters.get(value_type, eval)
                    value = converter(value)
                    
                    # Create and set meta item
                    key = header.split(match_header_prefix, 1)[-1].replace("-", "_").upper()
                    meta[key] = value
                
                except Exception:
                    # Ignore errors.
                    pass
        return meta
    
    @classmethod
    def compile_meta_to_headers(cls, meta: Dict):
        """
        Converts meta to  ensure headers that can be sent to a server and be decoded right back to the 
        appropriate data type.
        
        Args:
            meta (Dict): The meta dictionary.
        
        Returns:
            Dict: The new headers.
        
        Workflow:
        
        1. Convert meta to something like this:
             
             ```py
             {
                 f"X-{secret}-{meta_key}": "{new_value}@{value_type}"
              }
             ```
             
        2. The secret is the first 8 characters from RAND_SECRET and meta_key is the value converted to 
             titlecase and '_' converted to '-'.
        3. The new_value is the compressed and encoded value, lastly, value_type is the 
             data type (as a string) before the value converted to string e.g:
             
             ```py
             {
                  "X-Fjsu6dj3-Http-Host": "eJwL8Q0BA...@str",
             }
             ```
        """
        # Only use 8 bits of secret to construct a header
        secret = RAND_SECRET[:8].title()
        headers = {}
        
        for key, value in meta.items():
            header = f'X-{secret}-{key.replace("_", "-").title()}'
            value_type = str(type(value)).split(" ")[1].strip(">").strip("'")
            
            if key.startswith("X-{secret}-"):
                # Skip if the meta key already matches the prefix
                continue
            value = str(value) # convert value to string
            value = compress_and_encode(value) + f"@{value_type}"
            headers[header] = value
        return headers
        
    @classmethod
    def process_request(cls, request):
        meta_headers = cls.compile_meta_to_headers(request.META)
        request.headers.update(headers)
