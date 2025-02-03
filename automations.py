"""
Define all your Automations and Triggers here and include them in your settings.py.

Example:

    from duck.automation import Automation
    from duck.automation.trigger import AutomationTrigger

    class CustomTrigger(AutomationTrigger):
        def check_trigger(self):
            # Check if a specific condition is fulfilled
            # Return True if the condition is met, otherwise return False
            if condition:
                return True
            else:
                return False

    class CustomAutomation(Automation):
        def execute(self):
            # Execute the automation tasks here
            pass

    # Instantiate the custom trigger
    custom_trigger = CustomTrigger()

    # Instantiate the custom automation with the specified parameters
    custom_automation = CustomAutomation(
        name="Custom Automation",
        description="Some description",
        start_time="immediate",
        schedules=-1,
        interval=1,
    )  # This automation starts immediately on trigger and runs indefinitely with a delay of 1 second on each cycle.
"""
