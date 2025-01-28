import os
import platform


def is_phone():
    # Check OS
    os_name = platform.system().lower()
    if os_name in ["android", "ios"]:
        return True

    # Check for Android-specific files
    if os_name == "linux" and os.path.exists("/system/build.prop"):
        return True

    # Check architecture
    architecture = platform.machine().lower()
    if "arm" in architecture or "aarch64" in architecture:
        return True

    # Assume non-phone for other cases
    return False
