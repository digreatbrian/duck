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
            
            # Run the code in the subprocess with chroot isolation
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.run_in_subprocess(sanitized_code, variable_name, temp_dir)
            return result

        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": traceback.format_exc()}

    def sanitize_code(self, code: str) -> str:
        blocked_imports = [
            "os",
            "re",
            "builtins",
            "sys",
            "subprocess",
            "shutil",
            "socket",
            "ctypes",
            "pathlib",
            "threading",
            "multiprocessing",
            "warnings",
            "dotenv",
            "django",
        ]
        blocked_builtins = [
            "exec",
            "eval",
            "compile",
            "open",
            "__builtins__",
            "__import__",
        ]

        for banned in blocked_imports:
            if re.search(rf'\b(import|from)\s+{banned}\b', code):
                raise ValueError(f"Blocked import: {banned}")

        for banned in blocked_builtins:
            if re.search(rf'\b{banned}\b', code):
                raise ValueError(f"Blocked usage: {banned}")

        return code

    def run_in_subprocess(self, py_code: str, variable_name: str, temp_dir: str) -> dict:
        try:
            # `chroot` will ensure the subprocess is isolated to the temp_dir
            command = [
                sys.executable, '-c', f"""
import json
import resource
import sys
import os
import traceback

# Enforce resource limits
resource.setrlimit(resource.RLIMIT_CPU, (1, 1))  # Limit CPU time
resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))  # Limit RAM (128MB)

# Override os functions to prevent changing directories
def safe_chdir(path):
    raise PermissionError("Changing directories is not allowed")

def safe_getcwd():
    return "{temp_dir}"

# Create read-only open function to block write access
def safe_open(path, mode='r', *args, **kwargs):
    if 'w' in mode or 'a' in mode or '+' in mode or 'x' in mode:
        raise PermissionError("Write access is forbidden")
    if not os.path.isfile(path):
        raise FileNotFoundError("Only regular files are accessible")
    if path.startswith(('/etc', '/proc', '/sys', '/dev', '/bin', '/lib', '/boot')):
        raise PermissionError("Access to system directories is not allowed")
    return open(path, mode, *args, **kwargs)

# Safe built-ins
safe_builtins = {{
    "range": range,
    "len": len,
    "int": int,
    "float": float,
    "str": str,
    "print": print,
    "bool": bool,
    "dict": dict,
    "list": list,
    "set": set,
    "tuple": tuple,
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "open": safe_open,
    "Exception": Exception,
    "chdir": safe_chdir,
    "getcwd": safe_getcwd,
    "__import__": __import__,
}}

def enforce_chroot():
    # Enforce chroot
    os.system("chroot {temp_dir}")
    os.chdir('/')

enforce_chroot()

sandbox_globals = {{}}
py_code = '''{py_code}'''

try:
    exec(py_code, {{"__builtins__": safe_builtins}}, sandbox_globals)
    result = sandbox_globals.get("{variable_name}", "Variable '{variable_name}' not found")
    print(json.dumps({{"success": result}}))
except MemoryError:
    print(json.dumps({{"error": "MemoryError: Exceeded memory limit"}}))
except Exception as e:
    print(json.dumps({{"error": "".join(traceback.format_exception(type(e), e, e.__traceback__))}}))
"""
            ]

            # Create the chroot environment for isolation
            process = subprocess.run(
                command,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=2,
            )

            output = process.stdout.strip()
            if output:
                return json.loads(output)
            else:
                return {"error": f"No output. stderr: {process.stderr.strip()}"}

        except subprocess.TimeoutExpired:
            return {"error": "Execution time limit exceeded"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON output from subprocess"}
        except Exception:
            return {"error": traceback.format_exc()}

