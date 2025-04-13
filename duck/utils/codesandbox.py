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
import os
import resource
import traceback
import tempfile
import json
import sys
import re


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
            # Sanitize the code to block dangerous imports and built-ins
            sanitized_code = self.sanitize_code(code)

            # Create a temporary file to store the code
            with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_code_file:
                temp_code_file.write(sanitized_code.encode('utf-8'))
                temp_code_path = temp_code_file.name

            # Execute the code in a separate process with restricted resources
            result = self.run_in_subprocess(temp_code_path, variable_name)

            # Clean up the temporary file
            os.remove(temp_code_path)

            return result

        except ValueError as ve:
            # Capture and return the specific ValueError message
            return {"error": str(ve)}
        except Exception as e:
            # Capture and return the full traceback in case of an error
            error_traceback = traceback.format_exc()
            return {"error": error_traceback}

    def sanitize_code(self, code: str) -> str:
        """ Blocks unauthorized imports and dangerous built-ins """
        blocked_imports = ["os", "builtins", "sys", "subprocess", "shutil", "socket", "ctypes", "pathlib"]
        blocked_builtins = ["exec", "eval", "compile", "open", "__import__", "__builtins__"]

        for banned in blocked_imports:
            if re.search(rf'\bimport\b\s*{banned}', code) or re.search(rf'\bfrom\b\s*{banned}', code):
                raise ValueError(f"Blocked import: {banned}")

        for banned in blocked_builtins:
            if re.search(rf'\b{banned}\b', code):
                raise ValueError(f"Blocked usage: {banned}")

        return code  # Return sanitized code if safe

    def run_in_subprocess(self, script_path: str, variable_name: str) -> dict:
        """ Runs the provided script in a subprocess with restricted resources """
        try:
            # Define the command to execute the script
            command = [sys.executable, '-c', f"""
import json
import resource
import sys
import traceback

# Restrict resources
resource.setrlimit(resource.RLIMIT_CPU, (2, 2))  # Max 2 sec CPU time
resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))  # Max 256MB RAM

# Execute the script
sandbox_globals = {{}}
try:
    exec(open('{script_path}').read(), sandbox_globals)
    result = sandbox_globals.get('{variable_name}', "Variable '{variable_name}' not found")
    print(json.dumps({{"success": result}}))
except MemoryError:
    print(json.dumps({{"error": "MemoryError: Exceeded memory limit"}}))
except Exception as e:
    print(json.dumps({{"error": "".join(
        traceback.format_exception(type(e), value=e, tb=e.__traceback__))}}))
            """]

            # Run the command in a subprocess with a time limit
            process = subprocess.run(command, capture_output=True, text=True, timeout=3)

            # Parse the output from the subprocess
            output = process.stdout.strip()
            if output:
                result = json.loads(output)
            else:
                # Include the stderr output in the error message for more information
                stderr_output = process.stderr.strip()
                if stderr_output:
                    result = {"error": f"No output from subprocess, stderr: {stderr_output}"}
                else:
                    result = {"error": "No output from subprocess"}

            return result

        except subprocess.TimeoutExpired:
            return {"error": "Execution time limit exceeded"}

        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON output from subprocess"}

        except Exception as e:
            # Capture and return the full traceback in case of an error
            error_traceback = traceback.format_exc()
            return {"error": error_traceback}
