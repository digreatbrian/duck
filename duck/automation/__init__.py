"""
Module for automations used in automating tasks, jobs, actions, and more.

This module provides classes and utilities to define and manage automated tasks. It includes a base `Automation` class for creating and running tasks with various scheduling options, as well as supporting threading and callback functionalities.

Classes:
    - AutomationError: Custom exception for automation-related errors.
    - AutomationThread: Threading class for executing automations.
    - Automation: Base class for automating tasks, jobs, actions, etc.

Usage example:
    import os
    from duck.automation.dispatcher import DispatcherV1
    from duck.automation.trigger import NoTrigger

    class SimpleAutomation(Automation):
        def execute(self):
            # Execute a shell script
            os.system('bash some_script.sh')

    # Instantiate the automation with specified parameters
    automation = SimpleAutomation(
        name="Sample Automation",
        description="Sample automation",
        start_time='immediate',
        schedules=1,
        interval=0,
    )  # Set automation schedules to -1 for infinite schedules

    # Instantiate a trigger that executes immediately
    trigger = NoTrigger()
    # You can create a custom trigger by implementing the `check_trigger` method
    # in your AutomationTrigger subclass and returning True or False based on 
    # whether the trigger condition is satisfied

    # Create a dispatcher to manage and execute automations
    dispatcher = DispatcherV1()  # The first argument is the main running web application (optional)

    # Register the trigger and automation with the dispatcher
    dispatcher.register(trigger, automation)
    dispatcher.start()  # Listen for triggers and execute automations infinitely

    # Alternatively, use a callback function for the automation task
    def callback():
        # Perform the automation tasks here
        # Avoid using while loops; set the number of schedules to -1 for infinite schedules

    automation = Automation(
        callback=callback,
        name="Sample Automation",
        description="Sample automation"
    )
    # Register the trigger and automation with the dispatcher
    dispatcher.register(trigger, automation)
    dispatcher.start()  # Listen for triggers and execute automations infinitely
"""

import datetime
import threading
import time

from duck.utils.dateutils import build_readable_date, datetime_difference


class AutomationError(Exception):
    """Automation based exceptions"""


class AutomationThread(threading.Thread):
    """
    Threading class for Automations execution.
    """

    def set_on_stop_callback(self, callback: callable):
        """
        Set a callback that will be called whenever the thread finishes execution.

        Notes:
                - Make sure callback doesn't allow any positional or keyword arguments.
        """
        if not callable(callback):
            raise TypeError(
                f"Callback should be a callable object not {type(callback).__name__}"
            )
        self.on_stop_callback = callback

    def on_stop(self):
        """
        Method called whenever a thread finishes execution.

        The callback set with method 'set_on_stop_callback' will be called if present.
        """
        if hasattr(self, "on_stop_callback"):
            return self.on_stop_callback()

    def start(self, *args, **kw):
        returned = super().start(*args, **kw)
        self.on_stop()
        return returned


class Automation:
    """
    Automation class for automating tasks, jobs, actions, etc.

    Events:
        - on_pre_execute: Called before every execution cycle.
        - on_post_execute: Called after every execution cycle.
        - on_start: Called once when the automation starts.
        - on_finish: Called once when the automation finishes.
        - on_error: Called whenever there is an error during execution. Override this method to suppress or handle all errors.

    Notes:
        - The `start` method is the initial method to run an automation.
        - The `callback` argument is optional; if not provided, the `execute` method must be implemented.
        - Provide a name and description for more descriptive Automations.
        - The `join` method can be used to stop the next execution cycle, meaning the automation will stop immediately before entering the next execution cycle.
        - Using a while loop in the `callback` or `execute` method will cause the automation to hang, and `join` will not work if the callback is in a loop.
        - The `join` method works properly before the next execution cycle or after the current execution cycle.
    """

    def __init__(
        self,
        callback: callable = None,
        name: str = None,
        threaded: bool = True,
        start_time: datetime.datetime | str = "immediate",
        schedules: int = 1,
        interval: float | int = None,
        description: str = None,
    ):
        """
        Initialize the Automation class.

        Args:
            callback (callable, optional): A callable to be executed whenever the automation runs. If you do not provide a callback, implement the 'execute' method.
            name (str, optional): The name of the Automation. Defaults to None.
            threaded (bool): Indicates whether to run the automation in a new thread. Defaults to True.
            start_time (datetime.datetime | str): The datetime to start the Automation. It can be "immediate" or any specific datetime.
            schedules (int): The number of times to run the Automation. Defaults to 1. Set to -1 for infinite schedules.
            interval (int | float): The time period in seconds between successive runs of the Automation.
            description (str, optional): A brief description of the Automation. Defaults to an empty string.
        """
        self.__running_app = None
        self.__first_execution = False
        self.__execution_times = 0
        self.__started_at = None
        self.__finished_at = None
        self.__force_stop = False
        self.__running = False
        self.__finished = False
        self.__latest_error = None
        # run some checks
        # threaded checks
        if not isinstance(threaded, bool):
            raise AutomationError(
                f"Argument threaded should be a boolean not {type(threaded).__name__}"
            )

        # callback checks
        if callback:
            if not callable(callback):
                raise AutomationError(
                    "Callback should be a callable object, function or method."
                )

        # name checks
        if name:
            if not isinstance(name, str):
                raise AutomationError(
                    f"Name should be an instance of string not {type(name).__name__}"
                )

        if description and not isinstance(description, str):
            raise AutomationError(
                f"Description should be a string not {type(description).__name__}"
            )

        # start_time checks
        if isinstance(start_time, datetime.datetime):
            now = datetime.datetime.now()
            if start_time < now:
                diff_dict: dict = datetime_difference(now, start_time)
                diff = build_readable_date(diff_dict)
                if diff == "Just now":
                    diff = "Less than a second"
                raise AutomationError(
                    f'Start time for the automation "{self.__class__.__name__}" has already passed, difference: {diff}'
                )

        elif isinstance(start_time, str):
            if not start_time == "immediate":
                raise AutomationError(
                    'Start time provided is not recognized, should be either a datetime object or "immediate" '
                )
        else:
            if not start_time:
                raise AutomationError(
                    "Please provide start time for the automation.")
            raise AutomationError(
                "Start time provided is not recognized, should be either a string or datetime object."
            )

        # schedules checks
        if isinstance(schedules, int):
            if schedules < 0 and schedules != -1:
                raise AutomationError(
                    "Number of schedules for automation should not be less than zero, consider setting to -1 for infinite schedules."
                )

            elif schedules == 0:
                raise AutomationError(
                    "Number of schedules should be at least >=1 or -1 not zero."
                )
        else:
            if not schedules:
                raise AutomationError("Number of schedules required.")
            raise AutomationError(
                f"Number of shedules should an integer not {type(schedules).__name__}"
            )

        # interval checks
        if isinstance(interval, (float, int)):
            if interval < 0:
                raise AutomationError(
                    "Interval for automation should be a positive integer or float"
                )
            elif interval > 0 and (schedules < 2 and schedules != -1):
                raise AutomationError(
                    "Interval for automation is set yet the number of schedules is less than the minimum i.e. 2"
                )
        else:
            if interval:
                raise AutomationError(
                    "Invalid interval provided, should be an integer or a float."
                )
        self.callback = callback
        self.name = name
        self.threaded = threaded
        self.start_time = start_time
        self.schedules = schedules
        self.interval = interval or 0  # will be 0 if interval is set to None
        self.description = str(description)

    def wrap_automation(self) -> AutomationThread:
        """
        This wraps an automation in new Thread so that it may be executed nicely without blocking any other automations execution.

        Return:
                AutomationThread: Returns an automation in new thread.
        """

        def on_error_wrapper(error: Exception):
            """
            Function called on automation execution error.
            """
            self.__running = False
            self.__finished = True
            self.__latest_error = error
            self.__finished_at = datetime.datetime.now()
            self.on_error(error)

        def run_automation(automation):
            """
            Run an automation.
            """
            try:
                automation._start()
            except Exception as e:
                automation.join()  # stop next execution cycles just in case

                if automation.name:
                    e = AutomationError(
                        f'Error executing automation with name "{automation.name}": {e}'
                    )
                else:
                    e = AutomationError(
                        f'Error executing automation of class "{type(automation).__name__}": {e}'
                    )
                # call on_error event
                on_error_wrapper(e)

        if self.name:
            thread = AutomationThread(
                target=run_automation,
                args=[self],
                name=f'Automation-{self.name.strip().replace(" ", "-")}'.title(
                ),
            )
        else:
            thread = AutomationThread(target=run_automation, args=[self])
        return thread

    def get_thread(self):
        """
        This returns the Thread for running automation.

        Notes:
                - The thread is only created once.
        """
        if not hasattr(self, "_base_thread"):
            self._base_thread = self.wrap_automation()
        return self._base_thread

    def join(self):
        """
        Wait for the automation to finish the current execution cycle and stop the execution
        """
        self.__force_stop = True

    @property
    def latest_error(self):
        """
        Returns the latest exception encountered during execution.
        """
        return self.__latest_error

    @property
    def is_running(self) -> bool:
        """
        Whether the automation is running or not.
        """
        return self.__running

    @property
    def started_at(self) -> datetime.datetime:
        """
        The datetime where this automation started.
        """
        if not self.is_running and not self.finished:
            raise AutomationError(
                "The automation was never started so the time it started cannot be given."
            )
        return self.__started_at

    @property
    def finished_at(self) -> datetime.datetime:
        """
        The datetime where this automation finished.
        """
        if not self.finished:
            if self.is_running:
                raise AutomationError("Automation still running.")
            raise AutomationError(
                "The automation was never started so the time it finished cannot be given."
            )
        return self.__finished_at

    def get_short_description(self):
        """
        Get the short version of description.
        """
        max_limit = 20
        short_description = ""

        if len(self.description) > max_limit:
            splitted_description = self.description.split(" ")
            if len(splitted_description) > 1:
                for word in splitted_description:
                    incr = word + " "
                    if len(short_description) + len(incr) <= max_limit:
                        short_description += incr
                    else:
                        short_description = short_description.strip()
                        short_description += "..."
                        break
            else:
                short_description = (self.description[:max_limit].strip()
                                     + "...")
        else:
            return self.description
        return short_description

    @property
    def finished(self):
        """
        Whether the automation has been stopped completely.
        """
        return self.__finished

    @property
    def first_execution(self) -> bool:
        """
        Returns whether the automation has already been executed for the first time.

        Notes:
                - Take a look a property execution_times to see the number of times the Automation was Executed.
        """
        return self.__first_execution

    @property
    def execution_times(self) -> int:
        """
        Returns the number of times the automation has been executed.
        """
        return self.__execution_times

    @property
    def execution_cycles(self) -> int:
        """
        Returns the number of times the automation has been executed (same as property 'execution_times').
        """
        return self.execution_times

    def get_running_app(self):
        """
        Returns the main running application
        """
        if not self.__running_app:
            raise AutomationError("Main running application is not yet set.")

    def set_running_app(self, app):
        """
        Set the main running application
        """
        from duck.app import App

        if not isinstance(app, App):
            raise AutomationError(
                f"Invalid application type: '{type(app).__name__}'. Expected instance of 'duck.app.App'."
            )

    def start(self):
        """
        Entry method to execute an automation.
        """

        def on_error_wrapper(error: Exception):
            """
            Function called on automation execution error.
            """
            self.__running = False
            self.__finished = True
            self.__latest_error = error
            self.__finished_at = datetime.datetime.now()
            self.on_error(error)

        if self.threaded:
            thread = self.get_thread()
            if thread.is_alive():
                raise AutomationError(
                    "Automation is already running in another thread, cannot start automation."
                )
            thread.start()
        else:
            try:
                self._start()
            except Exception as e:
                self.join()  # stop next execution cycles just in case

                if self.name:
                    e = AutomationError(
                        f'Error executing automation with name "{self.name}": {e}'
                    )
                else:
                    e = AutomationError(
                        f'Error executing automation of class "{type(self).__name__}": {e}'
                    )
                # call on_error event
                on_error_wrapper(e)

    def _start(self):
        """
        Entry method to execute an automation.
        """
        self.__running = False
        self.__force_stop = False  # undo method "join" if it has been used
        self.__finished = False

        def on_start_wrapper():
            """
            Function called on automation start.
            """
            self.__running = True
            self.__first_execution = True
            self.__started_at = datetime.datetime.now()
            self.on_start()

        def on_finish_wrapper():
            """
            Function called on automation finish.
            """
            self.__running = False
            self.__finished = True
            self.__finished_at = datetime.datetime.now()
            self.on_finish()

        if self.schedules == -1:  # execute to infinite
            counter = 0

            while True:
                if self.__force_stop:
                    break  # force stop, maybe method join was used.

                if counter == 0:
                    on_start_wrapper(
                    )  # call function on_start_wrapper just once

                # continue with execution
                self.on_pre_execute()  # do some stuff before execution
                self.execute()  # execute the automation
                self.on_post_execute()  # do some stuff after execution
                self.__executed = (
                    True  # set that the method has executed for the first time
                )
                self.__execution_times += 1
                counter += 1  # counter is more accurate on number of times the loop was run compared to __execution_times.
                time.sleep(self.interval)  # sleep before next execution cycle
        else:
            for i in range(0, self.schedules):
                if self.__force_stop:
                    break  # force stop, maybe method join was used.

                if i == 0:
                    on_start_wrapper(
                    )  # call function on_start_wrapper just once

                # continue with execution
                self.on_pre_execute()  # do some stuff before execution
                self.execute()  # execute the automation
                self.on_post_execute()  # do some stuff after execution
                self.__executed = (
                    True  # automation has executed for the first time
                )
                self.__execution_times += 1
                time.sleep(self.interval)  # sleep before next execution cycle

        # finished or stopped execution
        on_finish_wrapper()

    def execute(self):
        """
        This executes an automation.
        Do whatever task you want here e.g. running bash scripts or something else.

        Example:

                import os

                class SimpleAutomation(Automation):
                        def execute(self):
                                os.system('bash some_script.bash')
                automation = SimpleAutomation(start_time='immediate', schedules=1, interval=0)
                automation.start # start the automation
        """
        if not self.callback:
            raise NotImplementedError(
                "AutomationError: The 'execute' method must be implemented. This method is the main entry point for automation execution. Alternatively, pass a callback argument to the Automation class."
            )
        self.callback()

    def on_pre_execute(self):
        """
        Method called before automation starts the current execution cycle.
        """

    def on_post_execute(self):
        """
        Method called after automation has finished the current execution cycle.
        """

    def on_start(self):
        """
        Method called once the execution has been started.

        Notes:
                - Method "on_start" is called before method "on_pre_execute"
        """

    def on_finish(self):
        """
        Method called on automation final finish.
        """

    def on_error(self, e):
        """
        Method called on execution automation after method "start" is called.
        """
        raise e

    def __repr__(self):
        return (
            f"[{self.__class__.__name__}] (\n"
            f"  name={repr(self.name)}\n"
            f"  description={repr(self.get_short_description()) if self.description else None}\n"
            f"  callback={self.callback}\n"
            f"  start_time={repr(self.start_time)}\n"
            f"  execution_times={self.execution_times}\n"
            f"  finished={self.finished}\n"
            f"  schedules={self.schedules}\n"
            f"  interval={self.interval}\n"
            f"  latest_error={type(self.latest_error).__name__ if self.latest_error else None}\n"
            ")")


class SampleAutomation(Automation):
    """
    A placeholder automation class designed for testing or sampling purposes.

    This automation is intentionally empty and does not perform any actions. It can be used
    as a base for creating more complex automations or for testing automation systems without
    side effects.

    Use this class when you need a no-op (no operation) automation that will not alter
    the application's state or behavior during execution.
    """

    def execute(self):
        """
        No-op method.

        This method is intentionally left empty and performs no actions. It is used as a placeholder
        or for testing purposes where no operation is required.
        """


SampleAutomation = SampleAutomation()
