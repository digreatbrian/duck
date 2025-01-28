"""
Module containing the JsxCodeStore class responsible for mapping jsx code code to unique identifiers.
"""
import hashlib
from typing import Any


class JsxCodeStore:
    """
    JsxCodeStore class responsible for mapping jsx code code to unique ID's.
    """
    _store = {}
    
    @classmethod
    def update(cls, jsx_code_id: Any, jsx_code: str):
        """
        Updates or saves the jsx code in respective to the jsx code ID.
        """
        cls._store[jsx_code_id] = jsx_code
    
    @classmethod
    def jsx_code_exists(cls, jsx_code_id: Any):
        """
        Checks whether the jsx code with the provided jsx_code_id exists.
        """
        return True if jsx_code_id in cls._store.keys() else False
     
    @classmethod
    def get_jsx_code(cls, jsx_code_id: Any, default: Any = None) -> str:
        """
        Returns the jsx code for the given jsx code ID.
        If jsx code cannot be found, the default value will be returned.
        """
        return cls._store.get(jsx_code_id, default)
    
    @classmethod
    def get_jsx_code_id(cls, jsx_code: str, ext: str = '.jsx'):
        """
        Returns a sha256 unique ID for the jsx code plus extension (if applicable).
        
        Args:
            jsx_code (str): The jsx code.
            ext (str): The extension to add as a prefix to the final ID.
        """
        jsx_code_id = hashlib.sha256((jsx_code[:1000]).encode('utf-8')).hexdigest() + ext
        return jsx_code_id
