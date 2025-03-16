"""
Module for implementation of a basic Query Dictionary
"""

class QueryDict(dict):
    """
    A dictionary subclass that allows multiple values for a single key.
    """

    def __repr__(self):
        return f"<{self.__class__.__name__} {super().__repr__()}>"

    def appendlist(self, key: str, value) -> None:
        """Appends a value to a key's list."""
        if key in self:
            if isinstance(super().__getitem__(key), list):
                if value not in super().__getitem__(key):  # Avoid duplicates
                    super().__getitem__(key).append(value)
            else:
                super().__setitem__(key, [super().__getitem__(key), value])  # Convert to list
        else:
            super().__setitem__(key, [value])

    def __setitem__(self, key: str, value) -> None:
        """Ensures values are always stored as lists."""
        if key in self:
            existing_value = super().__getitem__(key)
            if isinstance(existing_value, list):
                if value not in existing_value:  # Avoid duplicates
                    existing_value.append(value)
            else:
                super().__setitem__(key, [existing_value, value])  # Convert to list
        else:
            super().__setitem__(key, [value])  # Store value as a list

    def __getitem__(self, key: str):
        """
        Returns the first value for the key, or raises KeyError if the key is missing.
        """
        if key in self:
            values = super().__getitem__(key)
            return values[0] if isinstance(values, list) else values
        raise KeyError(f"Key '{key}' not found")

    def __delitem__(self, key: str) -> None:
        """Deletes a key from the QueryDict."""
        if key in self:
            super().__delitem__(key)

    def update(self, other=None, **kwargs) -> None:
        """Merges values instead of replacing them."""
        if other:
            if isinstance(other, dict):
                for key, value in other.items():
                    if isinstance(value, list):
                        for v in value:
                            self.appendlist(key, v)
                    else:
                        self.appendlist(key, value)
            else:
                raise TypeError("QueryDict update() expects a dictionary or keyword arguments")
        
        for key, value in kwargs.items():
            self.appendlist(key, value)

    def get(self, key: str, default=None):
        """Retrieves the first value for a key, or `default` if not found."""
        return self[key] if key in self else default

    def getlist(self, key: str, default=None):
        """Retrieves all values for a key as a list."""
        return super().get(key, default if default is not None else [])

    def setlist(self, key: str, values: list) -> None:
        """Sets a key to multiple values, replacing existing ones."""
        if not isinstance(values, list):
            raise TypeError("setlist() expects a list")
        super().__setitem__(key, values)

    def pop(self, key: str, default=None):
        """Removes a key and returns its list of values."""
        return super().pop(key, default)

    def poplist(self, key: str, default=None):
        """Removes a key and returns its values as a list."""
        return super().pop(key, default if default is not None else [])

    def keys(self):
        """Returns all keys in the QueryDict."""
        return super().keys()

    def values(self):
        """Returns all values in the QueryDict."""
        return super().values()

    def items(self):
        """Returns all key-value pairs in the QueryDict."""
        return super().items()

    def copy(self):
        """Returns a copy of the QueryDict."""
        return QueryDict(self)

    def clear(self) -> None:
        """Removes all items from the QueryDict."""
        super().clear()


class FixedQueryDict(QueryDict):
    """
    A custom dictionary-like class that accepts a dictionary with any number of keys.
    This class does not support deletion or modification of keys but only modification of values.
    """

    def __init__(self, data: dict):
        """
        Initializes the FixedQueryDict with a dictionary of any number of keys.

        Args:
            data (dict): Dictionary with any number of keys.

        Raises:
            ValueError: If the input is not a dictionary.
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary.")

        self._data = data
        self._keys = set(data.keys())

    def __getitem__(self, key):
        """
        Retrieves the value associated with the given key.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key.
        """
        return self._data[key]

    def __setitem__(self, key, value):
        """
        Sets the value for the given key if the key is allowed.

        Args:
            key: The key to set the value for.
            value: The value to set.

        Raises:
            KeyError: If the key is not one of the allowed keys.
        """
        if key not in self._keys:
            raise KeyError(
                f"Key '{key}' is not allowed. Only {self._keys} keys are allowed."
            )
        self._data[key] = value

    def __delitem__(self, key):
        """
        Raises an error as deletion of keys is not supported.

        Args:
            key: The key to delete.

        Raises:
            KeyError: Always raised as deletion is not supported.
        """
        raise KeyError("Deletion of keys is not supported.")

    def __repr__(self):
        """
        Returns a string representation of the QueryDict.

        Returns:
            str: String representation of the QueryDict.
        """
        return f"<{self.__class__.__name__} {self._data}>"

    def get(self, key):
        """
        Retrieves the value associated with the given key, or None if the key is not found.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key, or None if the key is not found.
        """
        return self._data.get(key)

    def update(self, other: dict):
        """
        Updates the FixedQueryDict with values from another dictionary.

        Args:
            other (dict): Dictionary to update the FixedQueryDict with.

        Raises:
            KeyError: If any key in the other dictionary is not one of the allowed keys.
        """
        if not isinstance(other, dict):
            raise ValueError("Input must be a dictionary.")

        for key, value in other.items():
            if key not in self._keys:
                raise KeyError(
                    f"Key '{key}' is not allowed. Only {self._keys} keys are allowed."
                )
            self._data[key] = value
