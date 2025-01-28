"""
Module for implementation of a basic Query Dictionary
"""


class QueryDict(dict):
    """
    Class implementation of a query dictionary.
    """
    def __repr__(self):
        """
        Returns a string representation of the QueryDict.

        Returns:
            str: String representation of the QueryDict.
        """
        return f"<{self.__class__.__name__} {super().__repr__()}>"

    def appendlist(self, key: str, value: str) -> None:
        """
        Appends a value to a list of values for a given key in the QueryDict.

        If the key does not already exist, it creates a new list with the given value.

        Args:
            key (str): The key to append the value to.
            value (str): The value to append to the key's list.
        """
        if key in self:
            self[key].append(value)
        else:
            self[key] = [value]


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
