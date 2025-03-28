"""
Module for retrieving or saving all processes created by Duck.

Attributes:
- `set_main_pid`: Saves the main application process ID in json file.

Notes:
- When opening a file, an exclusive lock is acquired to avoid race conditions.
	
Process JSON Format:

```json
{
	"process-name": {
	    "id": "xxx",
	    "other-data": "xxx"
    },
	"another-process": {
	    "id": "xxx",
	}
}
```
"""

import json
import os

from duck.settings import SETTINGS
from duck.utils.filelock import open_and_lock
from duck.utils.path import joinpaths

BASE_DIR = str(SETTINGS["BASE_DIR"]).rstrip("/")
FILENAME = ".duck-processes.json"


def set_process_data(name: str, data: dict, clear_existing_data=False) -> str:
    """
    Saves the process data in json file.

    Returns:
            str: The json file in which the process data was saved.
    """
    json_file = joinpaths(BASE_DIR, FILENAME)
    old_data = {}
    mode = "w"

    if not "pid" in data:
        raise KeyError("Key `pid` required in data.")

    if os.path.isfile(json_file):
        # file exists
        if not clear_existing_data:
            with open_and_lock(json_file, "r") as json_fd:
                old_data = json.load(json_fd)
    else:
        mode = "a"  # mode to create new file

    if old_data:
        old_process_data = old_data.get(name)
        if old_process_data:
            old_process_data.update(data)
            data = old_process_data

    old_data[name] = data  # save new process data

    with open_and_lock(json_file, mode) as json_fd:
        json.dump(old_data, json_fd)

    return json_file


def get_process_data(name) -> dict:
    """
    Retrieves the process data from json file.
    """
    json_file = joinpaths(BASE_DIR, FILENAME)
    old_data = {}

    if not os.path.isfile(json_file):
        # file doesn't exist
        raise KeyError(f"No record found for process with name '{name}' ")

    with open_and_lock(json_file, "r") as json_fd:
        try:
            old_data = json.load(json_fd)
        except json.JSONDecodeError:
            pass

    if not name in old_data.keys():
        raise KeyError(f"No record found for process with name '{name}' ")
    return old_data.get(name)


def get_all_processes_data() -> dict:
    """
    Returns all processes data saved in json file.
    """
    json_file = joinpaths(BASE_DIR, FILENAME)

    if not os.path.isfile(json_file):
        # file doesn't exist
        return {}

    with open_and_lock(json_file, "r") as json_fd:
        old_data = json.load(json_fd)
    return old_data


def clear_processes_data():
    """
    Clears all processes data in json file.
    """
    json_file = joinpaths(BASE_DIR, FILENAME)

    if os.path.isfile(json_file):
        # file exists
        with open_and_lock(json_file, "w") as json_fd:
            json.dump({}, json_fd)


def delete_process_data(name: str) -> dict:
    """
    Deletes the process data in json file.

    Returns:
            dict: The deleted process data
    """
    json_file = joinpaths(BASE_DIR, FILENAME)

    if os.path.isfile(json_file):
        # file exists
        with open_and_lock(json_file, "r") as json_fd:
            old_data = json.load(json_fd)

        if name not in old_data.keys():
            raise KeyError(
                f"Deletion failed: No record found for process with name '{name}'"
            )

        data = old_data.pop(name)

        with open_and_lock(json_file, "w") as json_fd:
            json.dump(old_data, json_fd)
        return data
