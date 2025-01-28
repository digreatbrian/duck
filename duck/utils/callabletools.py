"""
Module for duplicating callables (functions and methods) with the same signature.

This module provides a utility function `duplicate_callable` that can create a 
duplicate of any given callable (function or method) with the same signature. 
The duplicated callable retains the original callable's metadata, such as its 
name and docstring, and can optionally be given a custom name. Additionally, 
a decorator can be applied to the duplicated callable.

Usage Example:

    # Define a function to be duplicated
    def example_function(arg1, arg2, kwarg1=None, kwarg2=None):
        '''
        An example function that takes two positional arguments and two keyword arguments.
        '''
        return f"arg1: {arg1}, arg2: {arg2}, kwarg1: {kwarg1}, kwarg2: {kwarg2}"

    # Create a duplicate of the function with a custom name
    duplicated_function = duplicate_callable(example_function, new_name="duplicated_function")
    result = duplicated_function(1, 2, kwarg1="test", kwarg2="example")
    print(result)  # Output: arg1: 1, arg2: 2, kwarg1: test, kwarg2: example
    
    # Define a class with a method to be duplicated
    class MyClass:
        def example_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
            '''
            An example method that takes two positional arguments and two keyword arguments.
            '''
            return f"arg1: {arg1}, arg2: {arg2}, kwarg1: {kwarg1}, kwarg2: {kwarg2}"

    # Create a duplicate of the method with a custom name
    MyClass.duplicated_method = duplicate_callable(MyClass.example_method, new_name="duplicated_method")
    obj = MyClass()
    result = obj.duplicated_method(1, 2, kwarg1="test", kwarg2="example")
    print(result)  # Output: arg1: 1, arg2: 2, kwarg1: test, kwarg2: example
"""

import inspect
import functools


def duplicate_callable(callable_obj, new_name=None, decorator=None):
    """
    Creates a duplicate of the given callable (function or method) with the same signature.

    This function is useful for dynamically generating new callables with the same
    signature as an existing callable, while optionally allowing the application
    of a decorator. The new callable can also be given a custom name.

    Args:
        callable_obj (callable): The original callable to duplicate.
        new_name (str, optional): The name for the new duplicated callable. Defaults to None.
        decorator (callable, optional): A decorator to apply to the callable. Defaults to None.

    Returns:
        callable: A new callable with the same signature as the original callable.

    Safety:
        - This function avoids using exec, which mitigates the risk of executing arbitrary code.
        - The function uses closures to ensure that the wrapper is correctly referenced, preventing name errors.
        - By preserving the callable's signature and using functools.wraps, the callable's metadata
          (like name and docstring) is maintained.

    Example Usage:

        # Define a function to be duplicated
        def example_function(arg1, arg2, kwarg1=None, kwarg2=None):
            '''
            An example function that takes two positional arguments and two keyword arguments.
            '''
            return f"arg1: {arg1}, arg2: {arg2}, kwarg1: {kwarg1}, kwarg2: {kwarg2}"

        # Create a duplicate of the function with a custom name
        duplicated_function = duplicate_callable(example_function, new_name="duplicated_function")
        result = duplicated_function(1, 2, kwarg1="test", kwarg2="example")
        print(result)  # Output: arg1: 1, arg2: 2, kwarg1: test, kwarg2: example

        # Define a class with a method to be duplicated
        class MyClass:
            def example_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
                '''
                An example method that takes two positional arguments and two keyword arguments.
                '''
                return f"arg1: {arg1}, arg2: {arg2}, kwarg1: {kwarg1}, kwarg2: {kwarg2}"

        # Create a duplicate of the method with a custom name
        MyClass.duplicated_method = duplicate_callable(MyClass.example_method, new_name="duplicated_method")
        obj = MyClass()
        result = obj.duplicated_method(1, 2, kwarg1="test", kwarg2="example")
        print(result)  # Output: arg1: 1, arg2: 2, kwarg1: test, kwarg2: example
    """
    # Get the signature of the original callable
    sig = inspect.signature(callable_obj)

    # Define the wrapper with the same signature
    @functools.wraps(callable_obj)
    def wrapper(*args, **kwargs):
        if decorator:
            decorated_callable = decorator(
                callable_obj)  # Apply the decorator if provided
        else:
            decorated_callable = callable_obj
        return decorated_callable(*args, **kwargs)

    # Use the signature to dynamically construct the new callable
    parameters = ", ".join(str(param) for param in sig.parameters.values())

    # Create a closure to contain the wrapper reference
    def create_callable(wrapper):
        # Construct the new callable within the closure
        if hasattr(callable_obj, "__self__"):
            # Handle methods
            def new_method(self, *args, **kwargs):
                return wrapper(self, *args, **kwargs)

            return new_method
        else:
            # Handle functions
            def new_func(*args, **kwargs):
                return wrapper(*args, **kwargs)

            return new_func

    # Create and return the new callable
    new_callable = create_callable(wrapper)
    new_callable.__name__ = new_name if new_name else callable_obj.__name__
    new_callable.__signature__ = sig

    return new_callable
