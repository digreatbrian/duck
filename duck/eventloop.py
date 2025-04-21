import asyncio
import threading

class AsyncioLoopManager:
    def __init__(self):
        self.loop = None
        self.thread = None

    def start(self):
        """
        Start the event loop in a separate thread when called.
        """
        if self.loop is None:
            self.loop = asyncio.new_event_loop()

        def run_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=run_loop, daemon=True)
            self.thread.start()

    def submit_task(self, coro):
        """Submit an asynchronous task to the event loop."""
        if self.loop is not None and self.loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        else:
            raise RuntimeError("Event loop is not running. Call start() first.")

    def stop(self):
        """
        Stop the event loop gracefully.
        """
        if self.loop:
            self.loop.stop()
            self.thread.join()  # Ensure the thread finishes gracefully
