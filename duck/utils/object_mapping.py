"""
Module contains a function to map keys and values to an object.
"""


def map_data_to_object(obj, data: dict):
    """
    Map key-value pairs from a dictionary to an object's attributes.

    This function takes a dictionary and maps its key-value pairs as attributes
    of the given object. Each key in the dictionary becomes an attribute of the
    object with the corresponding value.

    Args:
        obj: The object to which attributes will be added.
        data (dict): A dictionary containing key-value pairs to be mapped to the object.

    Raises:
        TypeError: If the provided data is not a dictionary.

    Example:
    
    ```py
    class Example:
        pass

    e = Example()
    map_data_to_object(e, {'name': 'Alice', 'age': 30})
    print(e.name)  # Output: Alice
    print(e.age)   # Output: 30
    """
    if not isinstance(data, dict):
        raise TypeError(
            "Mapping key, value pairs only require <dict> type as data")

    for key, value in data.items():
        setattr(obj, key, value)
