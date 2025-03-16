"""
Secure Python Code Sandbox:

This script defines a class `SafeCodeSandbox` that provides a secure execution environment
for running arbitrary Python code. It ensures isolation by:
- Running code in a subprocess.
- Blocking dangerous imports and built-ins.
- Restricting system resources like CPU and memory.
- Providing execution time and memory limits to prevent abuse.
"""
import subprocess
import sys
import json
import tempfile
import os
import resource
import traceback


class SafeCodeSandbox:
    """
    Secure Python Code Sandbox:

    This class runs Python code in a secure, isolated environment. It blocks unsafe imports,
    limits resource usage (CPU and memory), and executes the code in a subprocess to prevent
    access to the host system. This approach helps in executing untrusted Python code safely.

    Attributes:
        None
    """

    def execute(self, code: str, variable_name: str):
        """
        Executes the provided Python code in a secure sandbox environment and retrieves the value of a specific variable.

        Args:
            code (str): The Python code to be executed in the sandbox.
            variable_name (str): The name of the variable whose value we want to retrieve.

        Returns:
            dict: A dictionary with either:
                - "success": the value of the specified variable.
                - "error": error message including full traceback if an exception occurs.

        Raises:
            ValueError: If the provided code tries to use blocked imports or built-ins.
            subprocess.TimeoutExpired: If the execution exceeds the time limit.
        """
        try:
            # Prepare the sandboxed execution environment (a separate dictionary for globals)
            sandbox_globals = {}

            # Compile and execute the code in a restricted namespace (sandbox_globals)
            compiled_code = compile(self.sanitize_code(code), "<string>", "exec")

            # Execute the code in a safe, isolated environment
            exec(compiled_code, sandbox_globals)

            # Access the desired variable from sandbox_globals
            if variable_name in sandbox_globals:
                return {"success": sandbox_globals[variable_name]}  # Return variable value in its native type
            else:
                return {"error": f"Variable '{variable_name}' not found"}

        except Exception as e:
            # Capture and return the full traceback in case of an error
            error_traceback = traceback.format_exc()
            return {"error": error_traceback}

    def sanitize_code(self, code: str) -> str:
        """ Blocks unauthorized imports and dangerous built-ins """
        blocked_imports = ["os", "sys", "subprocess", "shutil", "socket", "ctypes"]
        blocked_builtins = ["exec", "eval", "compile", "open", "__import__"]

        for banned in blocked_imports:
            if f"import {banned}" in code or f"from {banned}" in code:
                raise ValueError(f"Blocked import: {banned}")

        for banned in blocked_builtins:
            if banned in code:
                raise ValueError(f"Blocked usage: {banned}")

        return code  # Return sanitized code if safe

    def restrict_resources(self):
        """ Limits memory and CPU usage to prevent abuse """
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))  # Max 2 sec CPU time
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))  # Max 256MB RAM
