"""
Module for Automators that automate specific tasks.

This module provides classes and utilities to define and manage automated tasks.
It includes an `AutomationDispatcher` class for dispatching automations based on triggers
and a custom exception class for handling dispatcher-related errors.

Classes:
    - `AutomationDispatcherError`: Custom exception for automation dispatcher-related errors.
    - `AutomationDispatcher`: Class for dispatching automations based on triggers.

Usage example:
 
 ```py
from duck.automation import Automation
from duck.automation.trigger import AutomationTrigger

# Define your automations and triggers
trigger = AutomationTrigger(...)
automation = Automation(...)

# Create a dispatcher and register automations with triggers
dispatcher = AutomationDispatcher(application)
dispatcher.register(trigger, automation)

# Start the dispatcher to listen for triggers and run automations
dispatcher.start()
```
"""

import time

from duck.automation import Automation
from duck.automation.trigger import AutomationTrigger


class AutomationDispatcherError(Exception):
    """
    Automation Dispatcher related exceptions
    """


class AutomationDispatcher:
    """
    Automation dispatcher class.

    Notes:
    - You can create your own dispatcher class by creating a subclass from this class and implement method `listen`
    """

    __queue: dict[AutomationTrigger, list[Automation]] = {}
    """Dictionary of automation triggers mapping to their Automations"""

    __executed_automations: list[Automation] = []
    """List of automations that has been started, these may be in finished or running state"""

    poll: int | float = 1
    """
	Poll interval to listen for triggers
	"""

    def __init__(self, application=None):
        self.__force_stop = False
        self.application = application

    def start(self):
        """
        Start listening for registered triggers and executes automations
        """
        while True:
            if not self.__force_stop:
                self.listen(
                )  # listen for triggers and execute corresonding automations
            else:
                break
            time.sleep(self.poll)  # sleep before listening to new triggers.

    def listen(self):
        """
        Listen for any triggers and execute any automations associated with those triggers.

        This method removes each trigger that is satisfied and executes the corresponding automations.

        Implement this method to customize how automations should be run based on your specific requirements.

        Notes:
        - You can check if a trigger is satisfied by using the "check_trigger" method on that trigger.
        - Potential RuntimeError may be raised if you try accessing self.queue.keys convert self.queue.keys to another type instead to avoid this error.

        Example:
        
        ```py
        def listen(self):
            for trigger in set(self.queue.keys()):
                trigger_satisfied = trigger.check_trigger()  # whether trigger is satisfied or fulfilled
                if trigger_satisfied:
                    self.run_automations(self.queue.pop(trigger))  # pop trigger and execute corresponding automations
        ```
        """
        raise NotImplementedError('Method "listen" should be implemented.')

    def run_automations(self, automations: list[Automation]):
        """
        Run all provided automations.
        """
        for automation in automations:
            automation.start()
            self.__executed_automations.append(automation)

    @property
    def executed_automations(self) -> list[Automation]:
        """
        Get all automations that have been executed, whether running or finished.
        """
        return self.__executed_automations

    @property
    def queue(self) -> dict[AutomationTrigger, list[Automation]]:
        """
        Returns a dictionary mapping of triggers to their automations.
        """
        return self.__queue

    def prepare_stop(self):
        """
        Called before the main application termination.
        """
        for executed_automation in self.executed_automations:
            if executed_automation.is_running:
                executed_automation.prepare_stop()
    
    def unregister(self, trigger: AutomationTrigger, automation: Automation):
        """
        Removes an automation from the ready queue.

        Returns:
                Automation: The removed automation.
        """
        if trigger not in self.__queue:
            raise AutomationDispatcherError(
                "Trigger provided doesn't exist in ready queue, perhaps no automation is associated with the trigger."
            )
        existing_automations = self.__queue.get(trigger, [])
        if not automation in existing_automations:
            raise AutomationDispatcherError(
                "Automation does not exist for the given trigger, perhaps it has already been dispatched."
            )
        else:
            existing_automations.remove(
                automation)  # remove automation from existing automations
            self.__queue[trigger] = existing_automations
        return automation

    def register(self, trigger: AutomationTrigger, automation: Automation):
        """
        This adds an Automation to ready queue.
        """
        if not isinstance(trigger, AutomationTrigger):
            raise AutomationDispatcherError(
                f"Trigger provided is unknown, should be an instance of AutomationTrigger not {type(trigger).__name__}"
            )

        if not isinstance(automation, Automation):
            raise AutomationDispatcherError(
                f"Automation provided is unknown, should be an instance of Automation not {type(automation).__name__}"
            )

        (automation.set_running_app(self.application)
         if self.application else None)  # set automation application

        if trigger in self.__queue.keys():
            existing_automations: list = self.__queue.get(trigger, [])
            existing_automations.append(
                automation
            )  # add automation to existing automations with the same trigger
            self.__queue[trigger] = existing_automations
        else:
            self.__queue[trigger] = [automation]


class DispatcherV1(AutomationDispatcher):

    def listen(self):
        for trigger in set(self.queue.keys()):
            trigger_satisfied = (trigger.check_trigger()
                                 )  # whether trigger is satisfied or fulfilled
            if trigger_satisfied:
                self.run_automations(
                    self.queue.pop(trigger)
                )  # pop trigger and execute corresponding automations
