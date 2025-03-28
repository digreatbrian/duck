"""
Module for storing, updating and manipulating global variables

Example usage:

```py
import duck.globals
	
duck.global.some_variable = 1234
	
# then using this variable somewhere else
# some_module.py
import duck.globals
	
perform_action(duck.globals.some_variable) # perform action on variable
```
"""

session_storage_connector = None
