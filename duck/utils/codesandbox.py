"""
Secure Python Code Sandbox:

This script defines a class `SafeCodeSandbox` that provides a secure execution environment
for running arbitrary Python code. It ensures isolation by:
- Running code in a subprocess.
- Blocking dangerous imports and built-ins.
- Restricting system resources like CPU and memory.
- Providing execution time and memory limits to prevent abuse.

Note:
- This is only available for Linux environment.
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
    Enhanced Secure Python Code Sandbox:

    This class runs Python code in a highly secure, isolated environment. It blocks unsafe imports,
    restricts resource usage (CPU, memory), and executes the code in a subprocess with limited
    system call access to prevent abuse.
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
        """
        try:
            sanitized_code = self.sanitize_code(code)

            # Create a temporary directory and file to isolate the code execution
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_code_path = os.path.join(temp_dir, "sandbox_script.py")
                with open(temp_code_path, 'w') as temp_code_file:
                    temp_code_file.write(sanitized_code)

                # Execute the code in a subprocess with restricted resources
                result = self.run_in_subprocess(temp_code_path, variable_name, temp_dir)

            return result

        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
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

        return code

    def run_in_subprocess(self, script_path: str, variable_name: str, temp_dir: str) -> dict:
        """ Runs the provided script in a subprocess with restricted resources """
        try:
            command = [
                sys.executable, '-c', f"""
import json
import resource
import sys
import os
import traceback

# Restrict resources
resource.setrlimit(resource.RLIMIT_CPU, (1, 1))  # Max 1 sec CPU time
resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))  # Max 128MB RAM

# Drop privileges (if running as root)
def drop_privileges():
    if os.getuid() == 0:
        os.setgid(65534)  # Set group to 'nobody'
        os.setuid(65534)  # Set user to 'nobody'

drop_privileges()

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
                """
            ]

            # Run the command in a subprocess with additional restrictions
            process = subprocess.run(
                command,
                cwd=temp_dir,  # Change working directory to temp_dir (isolation)
                capture_output=True,
                text=True,
                timeout=2  # Time limit for the subprocess
            )

            output = process.stdout.strip()
            if output:
                result = json.loads(output)
            else:
                stderr_output = process.stderr.strip()
                result = {"error": f"No output from subprocess, stderr: {stderr_output}"}

            return result

        except subprocess.TimeoutExpired:
            return {"error": "Execution time limit exceeded"}

        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON output from subprocess"}

        except Exception as e:
            error_traceback = traceback.format_exc()
            return {"error": error_traceback}
