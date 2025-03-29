"""
Module for HTTP headers.
"""

from typing import Optional


class Headers(dict):
    """
    Headers class for representing request or response headers.
    """
    def titled_headers(self):
        """
        Returns headers in title format rather than small cased

        Example:
        - {'Connection': 'close'} rather than {'connection': 'close'}
        """
        return {h.title(): v for h, v in self.items()}

    def _get_header(self, header: str, default_value=None) -> Optional[str]:
        """
        Returns a header value of default_value if not found.
        """
        last_header_value = None
        for hd in self.keys():
            if hd.lower() == header.lower():
                last_header_value = self[hd]
        return default_value if not last_header_value else last_header_value

    def get(self, header: str, default=None):
        """
        Returns a header value of default if not found.
        """
        return self._get_header(header, default)

    def set_header(self, header: str, value: str):
        """
        Sets a header value.
        """
        return self.__setitem__(header, value)

    def delete_header(self, header: str, failsafe: bool = True):
        """
        Deletes a header and if failsafe is True, no error will be raised if header doesn't exist
        """
        if failsafe:
            for hd in set(self.keys()): # convert keys to set to avoid dictionary changed size error.
                if hd.lower() == header.lower():
                    self.pop(hd)
        else:
             self.pop(hd)
        
    def parse_from_bytes(self, data: bytes, delimeter="\r\n"):
        """
        Load headers from bytes.

        Args:
                delimeter (str | bytes): Delimeter separating the headers.
        """
        assert isinstance(data, bytes), "Only bytes is allowed as data."
        delimeter = (delimeter.decode("utf-8")
                     if isinstance(delimeter, bytes) else delimeter)
        data = data.strip().decode("utf-8")
        lines = data.split(delimeter)
        # set headers to self
        for line in lines:
            if ": " in line:
                parts = line.split(": ", 1)
                self.update({parts[0]: parts[1]})

    def validate_key_value(self, key: str, value: str):
        """
        Validates header key and value pair.
        """
        if not isinstance(key, str) or not isinstance(value, str):
            if not isinstance(key, str):
                raise KeyError(
                    f"Only an instance of string is allowed for key '{key}'")
            raise ValueError(
                f"Only an instance of string is allowed for value of key '{key}'"
            )
    
    def setdefault(self, key: str, value: str):
        self.validate_key_value(key, value)
        super().setdefault(key.lower(), value)
    
    def update(self, data: dict):
        for key, value in data.items():
            self.__setitem__(key, value)
            
    def __setitem__(self, key: str, value: str):
        self.validate_key_value(key, value)
        super().__setitem__(key.lower(), value)
        
    def __delitem__(self, key):
        super().__delitem__(key)

    def __repr__(self):
        return f"<{self.__class__.__name__} {dict(self)}>"
