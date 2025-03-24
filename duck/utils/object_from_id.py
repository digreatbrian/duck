"""
Retrieving an object by using its memory address.
"""
import ctypes


def get_object_by_id(address):
    """Retrieves an object by using its memory address."""
    try:
        # Validate that the address is an integer
        if not isinstance(address, int):
            raise TypeError("Address must be an integer.")

        # Attempt to access the object from the memory address
        obj_from_address = ctypes.cast(address, ctypes.py_object).value
        return obj_from_address

    except (TypeError, ValueError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}") from e
