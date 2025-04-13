"""
This module provides the `Meta` class, which extends the functionality of `os.environ` to store application metadata of various data types.

`os.environ` traditionally only supports string values. The `Meta` class overcomes this limitation by encoding data types within the environment variables, allowing storage and retrieval of integers, floats, dictionaries, lists, tuples, sets, and booleans.

Example:

```py
from duck.meta import Meta

Meta.set_metadata("config", {"debug": True, "port": 8080})
Meta.set_metadata("message", "Hello, world!")
Meta.set_metadata("pi", 3.14159)

print(Meta.compile())  # Outputs: {'config': {'debug': True, 'port': 8080}, 'message': 'Hello, world!', 'pi': 3.14159}
print(Meta.get_metadata("message"))  # Outputs: Hello, world!
print(Meta.get_metadata("config")['port']) # Outputs: 8080
```

Supported Data Types:

- `int`
- `str`
- `float`
- `dict`
- `tuple`
- `list`
- `set`
- `bool`

Classes:

- `Meta`: Manages application metadata in environment variables.
- `MetaError`: Custom exception for metadata-related errors.
"""

import os
import ast
from typing import Any

class MetaError(Exception):
    """
    Raised when an error occurs during metadata operations.
    """

class Meta:
    """
    Manages application metadata by storing and retrieving data in `os.environ` with type encoding.

    Class Attributes:
        meta_keys (list): A list of keys for metadata that has been set using `set_metadata`.
    """

    meta_keys: list = []
    """
    A list of keys for metadata that has been set using `set_metadata`.
    """
    
    exceptional_keys: list = [
        "DUCK_SERVER_DOMAIN",
        "DUCK_SERVER_ADDR",
        "DUCK_DJANGO_ADDR",
    ]
    """
    List of keys that are allowed to include `:` or `;` in their values thereby bypassing MetaError when 
    using `set_metadata`.
    """
    
    @classmethod
    def compile(cls) -> dict:
        """
        Retrieves all metadata stored using `set_metadata` and returns it as a dictionary.

        Returns:
            dict: A dictionary containing all stored metadata.
        """
        meta = {}
        for var in cls.meta_keys:
            meta[var] = cls.get_metadata(var)
        return meta

    @classmethod
    def get_absolute_server_url(cls) -> str:
        """
        Constructs and returns the absolute server URL based on metadata stored for domain, port, and protocol.

        Raises:
            MetaError: If any of the required server configuration variables (DUCK_SERVER_DOMAIN, DUCK_SERVER_PORT, DUCK_SERVER_PROTOCOL, DUCK_USES_IPV6) are not set.

        Returns:
            str: The absolute server URL.
        """
        domain = cls.get_metadata("DUCK_SERVER_DOMAIN", None)
        port = cls.get_metadata("DUCK_SERVER_PORT", None)
        protocol = cls.get_metadata("DUCK_SERVER_PROTOCOL", None)
        uses_ipv6 = cls.get_metadata("DUCK_USES_IPV6", None)

        if domain is None:
            raise MetaError("Variable DUCK_SERVER_DOMAIN not set.")
        
        if port is None:
            # Port is optional
            pass
            
        if protocol is None:
            raise MetaError("Variable DUCK_SERVER_PROTOCOL not set.")
        
        if uses_ipv6 is None:
            raise MetaError("Variable DUCK_USES_IPV6 not set.")

        return f"{protocol}://{domain}:{port}" if port else f"{protocol}://{domain}"

    @classmethod
    def update_meta(cls, data: dict):
        """
        Updates the metadata with the provided dictionary.

        Args:
            data (dict): A dictionary containing metadata to update.

        Raises:
            MetaError: If the provided data is not a dictionary.
        """
        if not isinstance(data, dict):
            raise MetaError(f"Data should be a dict, not '{type(data)}'")

        for var, value in data.items():
            cls.set_metadata(var, value)

    @classmethod
    def get_metadata(cls, key: str, default_value: Any = None) -> Any:
        """
        Retrieves the metadata value for the given key, converting it to the appropriate data type.

        Args:
            key (str): The key for the metadata.
            default_value (Any, optional): The value to return if the key does not exist. Defaults to None.

        Raises:
            MetaError: If the stored value is in an incorrect format or uses an unsupported type.

        Returns:
            Any: The metadata value, converted to its original data type.
        """
        value = os.environ.get(key)

        if value is None:
            return default_value

        type_converters = {
            "int": int,
            "str": str,
            "float": float,
            "dict": ast.literal_eval,
            "tuple": ast.literal_eval,
            "list": ast.literal_eval,
            "set": ast.literal_eval,
            "bool": ast.literal_eval,
        }

        if value.count("@") != 1:
            raise MetaError(
                'Value for provided key should contain exactly one "@" to separate value and type.'
            )

        value, _type = value.split("@", 1)
        _type = type_converters.get(_type.strip())

        if _type:
            return _type(value)
        else:
            raise MetaError(f"Unsupported type: {_type.strip()}")

    @classmethod
    def set_metadata(cls, key: str, value: Any):
        """
        Stores metadata in `os.environ` by encoding the data type along with the value.

        Args:
            key (str): The key for the metadata.
            value (Any): The value to store.

        Raises:
            MetaError: If the value is of an unsupported data type or contains disallowed characters.
        """
        if not isinstance(value, (str, int, float, dict, set, list, tuple, bool)):
            raise MetaError(f"Cannot set metadata for '{key}' with value of unsupported type: {type(value)}")

        var_type = str(type(value)).split(" ")[1].strip(">").strip("'")
        str_value = str(value)

        if "@" in str_value:
            raise MetaError(f'Value for "{key}" should not contain "@".')

        if ";" in str_value or (":" in str_value and var_type != "dict"):
            if key not in cls.exceptional_keys:
                # Only raise if key is not DUCK_SERVER_DOMAIN/DUCK_SERVER_ADDR as this may be an ipv6 address
                raise MetaError(f"Multiple value separators (';' or ':') are not supported for \"{key}\" except in a dictionary.")

        os.environ[key] = f"{str_value}@{var_type}"
        if key not in cls.meta_keys:
          cls.meta_keys.append(key)
