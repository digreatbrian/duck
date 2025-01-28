"""
Performance Utilities Module

Provides functions for measuring code performance, timing code execution, 
and optimizing operations.
"""
import time


def time_execution(func):
    """
    A decorator that measures the execution time of a function.
    
    Args:
        func (function): The function to measure.
    
    Returns:
        function: The wrapped function that will time its execution.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def measure_time(func):
    """
    Measures the time taken to run a function.
    
    Args:
        func (function): The function to measure.
    
    Returns:
        float: The execution time in seconds.
    """
    start_time = time.time()
    func()
    end_time = time.time()
    return end_time - start_time


def optimize_list_sort(lst: list) -> list:
    """
    Optimizes sorting by removing duplicates before sorting the list.
    
    Args:
        lst (list): The list to be sorted.
    
    Returns:
        list: The sorted list without duplicates.
    """
    return sorted(set(lst))
