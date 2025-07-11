"""
Lazy loading for callable Python objects.
"""

from collections import OrderedDict
from typing import (
    Callable,
    Tuple,
    Dict,
    Any,
)


class Lazy:
    """
    Lazily evaluates a callable and caches its result with an LRU policy.

    This class delays the execution of a callable (function, method, or class)
    until its result is explicitly needed. It caches the result to avoid 
    recomputation, using an LRU strategy based on maxsize.

    Attributes:
        _global_cache (OrderedDict): Shared LRU cache across all Lazy instances.
    """

    _global_cache: "OrderedDict[Tuple[Callable, Tuple, Tuple], Any]" = OrderedDict()

    __slots__ = (
        "_Lazy__callable",
        "_Lazy__args",
        "_Lazy__kwargs",
        "_Lazy__maxsize",
        "_Lazy__result",
    )

    def __init__(self, _callable: Callable, _maxsize: int = 256, *args, **kwargs):
        """
        Initializes the Lazy object.

        Args:
            _callable (Callable): The callable to lazily evaluate.
            _maxsize (int): Maximum size of the global cache.
            *args: Positional arguments to pass to the callable.
            **kwargs: Keyword arguments to pass to the callable.
        """
        self.__callable = _callable
        self.__args = args
        self.__kwargs = kwargs
        self.__maxsize = _maxsize

    def __getattr__(self, key):
        if key in self.__slots__:
            return super().__getattribute__(key)
        return getattr(self.getresult(), key)

    def __setattr__(self, key, value):
        if key in self.__slots__:
            super().__setattr__(key, value)
        else:
            setattr(self.getresult(), key, value)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.__callable})>"

    def __eq__(self, value):
        return self.getresult() == value

    def __gt__(self, value):
        return self.getresult() > value

    def __lt__(self, value):
        return self.getresult() < value

    def __iter__(self):
        return iter(self.getresult())
    
    def __getitem__(self, key):
        return self.getresult()[key]
        
    def __setitem__(self, key, value):
        self.getresult()[key] = value

    def __delitem__(self, key):
        del self.getresult()[key]

    def __call__(self, *args, **kwargs):
        result = self.getresult()
        return result(*args, **kwargs) if (args or kwargs) else result

    def getresult(self) -> Any:
        """
        Computes and caches the result of the callable using LRU eviction.

        Returns:
            Any: The result of the callable.
        """
        get_attr = super().__getattribute__
        set_attr = super().__setattr__

        try:
            return get_attr("_Lazy__result")
        except AttributeError:
            pass

        callable_ = get_attr("_Lazy__callable")
        args = get_attr("_Lazy__args")
        kwargs = get_attr("_Lazy__kwargs")
        maxsize = get_attr("_Lazy__maxsize")

        key = (callable_, args, tuple(sorted(kwargs.items())))

        cache = Lazy._global_cache

        if key in cache:
            # Move to end to mark as recently used
            result = cache.pop(key)
            cache[key] = result
        else:
            result = callable_(*args, **kwargs)
            cache[key] = result
            # Evict oldest entry if over maxsize
            while len(cache) > maxsize:
                cache.popitem(last=False)

        set_attr("_Lazy__result", result)
        return result
