"""
Module for Automation Triggers.

This module provides classes for defining and managing automation triggers.
It includes a base `AutomationTrigger` class and a `NoTrigger` class for scenarios where no trigger is needed.
"""


class AutomationTrigger:
    """
    Base class for Automation Triggers.

    This class serves as a blueprint for creating automation triggers.
    """

    def __init__(self, name: str = None, description: str = None):
        """
        Initialize the AutomationTrigger.

        Args:
            name (str, optional): The name of the trigger.
            description (str, optional): The description of the trigger.
        """
        self.name = name
        self.description = description

        if name:
            assert isinstance(name, str), "Name should be a string"
        if description:
            assert isinstance(description,
                              str), "Description should be a string"

    def check_trigger(self) -> bool:
        """
        Check if the trigger is satisfied.

        Returns:
            bool: True if the trigger is satisfied, otherwise False.

        Raises:
            NotImplementedError: This method should be implemented in a subclass.
        """
        raise NotImplementedError(
            'Implement method "check_trigger" to return bool on whether the trigger is satisfied or not.'
        )

    def __repr__(self):
        """
        Return a string representation of the AutomationTrigger.

        Returns:
            str: A string representation of the AutomationTrigger.
        """
        addr = super().__repr__().split(" ")[-1].strip(">")
        name = f'"{self.name}"' or None
        return f"<{self.__class__.__name__} name={name} at {addr}>"


class NoTriggerBase(AutomationTrigger):
    """
    A trigger that always returns True.

    This trigger can be used in scenarios where no specific trigger condition is required.
    """

    def check_trigger(self) -> bool:
        """
        Check if the trigger is satisfied.

        Returns:
            bool: Always returns True.
        """
        return True


# Default triggers definition
NoTrigger = NoTriggerBase()
