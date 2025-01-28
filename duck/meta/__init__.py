"""
This provides the functionality of storing application metadata as environment variables.

List of allowed data types for metadata values:
    - int
    - str
    - float
    - dict
    - tuple
    - list
    - set
    - bool
"""
import ast
import os
from typing import Any


class MetaError(Exception):
    """
    Raised on Meta related errors
    """


class Meta:
    """
    Meta class to store metadata for the application and so much more in os.environ
    """

    @classmethod
    def compile(cls) -> dict:
        """Compile application metadata

        Returns:
            meta (dict): Dictionary with application metadata
        """
        # the metadata should be stored in environ in format env=value@type
        variables = [
            "DUCK_SERVER_NAME",
            "DUCK_SERVER_DOMAIN",
            "DUCK_SERVER_PORT",
            "DUCK_SERVER_PROTOCOL",
            "DUCK_SERVER_POLL",
            "DUCK_SERVER_BUFFER",
            "DUCK_DJANGO_ADDR",
            "DUCK_USES_IPV6",
        ]
        meta = {}
        for var in variables:
            val = cls.get_metadata(var)
            meta[var] = val
        return meta

    @classmethod
    def get_absolute_server_url(cls) -> str:
        """
        Get the absolute server URL.
        """
        meta = cls.compile()
        domain = meta.get("DUCK_SERVER_DOMAIN", None)
        port = meta.get("DUCK_SERVER_PORT", None)
        protocol = meta.get("DUCK_SERVER_PROTOCOL", None)
        uses_ipv6 = meta.get("DUCK_USES_IPV6", None)

        if domain == None:
            raise MetaError(
                "Variable DUCK_SERVER_DOMAIN not set, consider setting it using method set_metadata or ensure the main application is running."
            )

        if port == None:
            raise MetaError(
                "Variable DUCK_SERVER_PORT not set, consider setting it using method set_metadata or ensure the main application is running."
            )

        if protocol == None:
            raise MetaError(
                "Variable DUCK_SERVER_PROTOCOL not set, consider setting it using method set_metadata or ensure the main application is running."
            )

        if uses_ipv6 == None:
            raise MetaError(
                "Variable DUCK_USES_IPV6 not set, consider setting it using method set_metadata or ensure the main application is running."
            )

        root_url = f"{protocol}://{domain}:{port}"
        return root_url

    @classmethod
    def update_meta(cls, data: dict):
        """Update the metadata"""
        if not isinstance(data, dict):
            raise MetaError(f"Data should be a dict not '{type(data)}'")

        for var, val in data.items():
            cls.set_metadata(var, val)

    @classmethod
    def get_metadata(cls, key: str) -> Any:
        """
        Get metadata with appropriate type.
        """
        val = os.environ.get(key)

        if val:
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
            if val.count("@") > 1:
                raise MetaError(
                    'Value for provided key should not contain multiple "@", consider substituting character.'
                )
            else:
                if val.count("@") == 0:
                    raise MetaError(
                        "Value for provided key is not in correct format, use method set_metadata to set correctly."
                    )
            val, _type = val.split("@", 1)
            t = _type.strip()
            _type = type_converters.get(t)

            if val.count(";") or (":" in val and not (t == "dict")):
                pass
                # raise MetaError("Multiple value separated data not supported yet, e.g. those in form env=value1:value2 or env=value1;value2")

            if _type:
                val = _type(val)
                return val
            else:
                raise MetaError(f"Unsupported type {_type.strip()}")

    @classmethod
    def set_metadata(cls, name: str, value: Any):
        """
        This stores a metadata in environment in format env=value@type.
        """
        if not isinstance(value,
                          (str, int, float, dict, set, list, tuple, bool)):
            raise MetaError(
                f"Cannot set metadata with value of unallowed type. {name}:{type(value)}"
            )

        var_type = str(type(value)).split(" ")[1].strip(">").strip("'")
        value = str(value)

        if "@" in value:
            raise MetaError(
                'Value should not contain "@", consider substituting character'
            )

        if ";" in value or (":" in value and not (var_type == "dict")):
            pass
            # raise MetaError("Multiple value separated data not supported yet, e.g. those in form env=value1:value2 or "	"env=value1;value2")

        val = f"{value}@{var_type}"
        os.environ[name] = val
