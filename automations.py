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
import json
import asyncio
import threading

from typing import Deque
from collections import deque

from duck.automation import Automation
from duck.logging import logger
from apps.mail.mail import Gmail


class EmailAutomation(Automation):
    # Automate sending pending emails
    emails: Deque[Gmail] = deque()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not hasattr(type(self), "event_loop"):
            # Set attribute on class rather than instance to avoid recreating event loop
            type(self).event_loop = asyncio.get_event_loop()
            type(self).event_loop_thread = threading.Thread(
                target=self.event_loop.run_forever, daemon=True)
            self.load_pending_emails()

    def on_start(self):
        self.event_loop_thread.start()
        
    def load_pending_emails(self, file="pending_emails.json"):
        """Load pending emails from a JSON file."""
        try:
            with open(file, "r") as f:
                email_data = json.load(f)
            
            # Convert the loaded data back into email objects
            self.emails = deque([
                Gmail(
                    to=email["to"],
                    from_=email["from_"],
                    subject=email["subject"],
                    name=email["name"],
                    body=email["body"],
                    recipients=email["recipients"],
                    use_bc=email["use_bc"],
                ) for email in email_data
            ])
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
    
    def save_pending_emails(self, pending_emails, file="pending_emails.json"):
        """Save pending emails to a JSON file."""
        emails = []
        for email in set(pending_emails):  # Use a set to avoid duplicates
            email_data = {
                "to": email.to,
                "from_": email.from_,
                "subject": email.subject,  # Include subject
                "name": email.name,        # Include name
                "body": email.body,
                "recipients": email.recipients,
                "use_bc": email.use_bc,
            }
            emails.append(email_data)
        
        # Write the emails list as JSON to the specified file
        with open(file, "w") as f:
            json.dump(emails, f, indent=4)
        
    @logger.handle_exception
    def prepare_stop(self):
        # Pre callback called before application execution
        self.join()  # Assuming this is synchronous
        
        # Get all tasks in the current event loop
        all_tasks = asyncio.all_tasks(loop=self.event_loop)
    
        # Process and cancel each task
        for task in all_tasks:
            task.cancel()  # Cancel every task
    
        # Wait for all tasks to finish
        for task in all_tasks:
            try:
                task.result()  # This will raise an exception if the task was cancelled
            except asyncio.CancelledError:
                pass  # Ignore the cancel error since the task was cancelled
    
        # Now, move all unsent emails back to the emails list
        for task in all_tasks:
            if hasattr(task, 'email') and not task.email.is_sent:
                self.emails.insert(0, task.email)  # Add unsent emails to the front of the list
    
        # Save pending emails to persistent storage
        self.save_pending_emails(self.emails)
    
    async def async_send_email(self, email: Gmail):
        """Asynchronously send an email and handle failures."""
        try:
            await asyncio.to_thread(email.send)
            logger.log(f"✅ Email sent to {email.to}", level=logger.DEBUG)
        except Exception as e:
            if not hasattr(email, "last_error"):
                # Only log email error message once
                logger.log(f"⚠️ Failed to send email to {email.to}, re-queuing... {e}", level=logger.WARNING)
                email.last_error = e
            self.emails.append(email)  # Retry by adding it back to the queue

    def execute(self):
        """Processes the email queue asynchronously."""
        if not self.emails:
            return  # No emails to send

        email = self.emails.popleft()  # Get the first email in queue
        coro = self.async_send_email(email)
        task = asyncio.run_coroutine_threadsafe(coro, loop=self.event_loop)  # Schedule async send
        task.email = email

# Instantiate the custom automation with the specified parameters
# This automation is automatically started in new thread
EmailAutomation = EmailAutomation(
    name="Email Automation",
    description="Automation for sending & scheduling emails",
    start_time="immediate",
    schedules=-1,
    interval=0.5,  # Runs every 0.5 seconds
)


# Function to add an email to the queue
def queue_email(email: Gmail):
    EmailAutomation.emails.append(email)
