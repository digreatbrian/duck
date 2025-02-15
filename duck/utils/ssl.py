import os
import struct
import subprocess

from duck.exceptions.all import SettingsError
from duck.logging import logger
from duck.settings import SETTINGS


def is_ssl_data(data: bytes) -> bool:
    """
    Checks if the given data is an SSL/TLS record.

    :param data: Raw bytes received from a socket.
    :return: True if data appears to be SSL/TLS, False otherwise.
    """
    if len(data) < 3:
        return False  # Not enough data to determine SSL

    first_byte, version_major, version_minor = struct.unpack("!BBB", data[:3])

    # SSL/TLS content types (Handshake, ChangeCipherSpec, Alert, Application Data)
    if first_byte in {0x14, 0x15, 0x16, 0x17}:
        # Check for valid SSL/TLS versions
        if (version_major == 0x03 and version_minor in {0x00, 0x01, 0x02, 0x03, 0x04}):
            return True

    return False


def generate_server_cert():
    """
    Generates a key pair (Key), csr (Certificate Signing Request ) and a self-signed certificate (CRT) for server-side use.

    This will generate 3 files using openssl:
        server.csr
        server.key
        server.crt

    This uses variables set in settings.py
    """
    csr_path = SETTINGS["SSL_CSR_LOCATION"]
    certfile_path = SETTINGS["SSL_CERTFILE_LOCATION"]
    private_key_path = SETTINGS["SSL_PRIVATE_KEY_LOCATION"]
    logger.log("Generating SSL certificate to use for HTTPS",
               level=logger.DEBUG)
    logger.log(
        "This will generate a self-signed certificate for development.",
        level=logger.DEBUG,
    )
    logger.log(
        "For production, please submit the CSR (Certificate Signing Request) to trusted CA (Certificate Authority) for "
        "signing to ensure browser compatibility and trust.\n",
        level=logger.WARNING,
    )

    # check if certfile and private key both exist, if not then continue
    if os.path.isfile(certfile_path) and os.path.isfile(private_key_path):
        # both are present flag a warning
        overwrite_existing = input(
            "SSL certfile and key pair already exist. Overwrite existing (y/N): "
        )

        print()

        if not overwrite_existing.lower().startswith("y"):
            logger.log("Cancelled SSL Certificate generation",
                       level=logger.DEBUG)
            return

    domain = SETTINGS["SERVER_DOMAIN"]
    country = SETTINGS["SERVER_COUNTRY"]
    state = SETTINGS["SERVER_STATE"]
    locality = SETTINGS["SERVER_LOCALITY"]
    organization = SETTINGS["SERVER_ORGANIZATION"]
    organization_unit = SETTINGS["SERVER_ORGANIZATION_UNIT"]

    if not domain:
        raise SettingsError("Please set SERVER_DOMAIN in settings.py")

    if len(country) != 2:
        raise SettingsError(
            "SERVER_COUNTRY should be a two-letter country code in settings.py"
        )

    if not state:
        raise SettingsError("SERVER_STATE should be set in settings.py")

    if not locality:
        raise SettingsError("SERVER_LOCALITY should be set in settings.py")

    if not organization:
        raise SettingsError("SERVER_ORGANIZATION should be set in settings.py")

    if not organization_unit:
        raise SettingsError(
            "SERVER_ORGANIZATION_UNIT should be set in settings.py")

    # checking for openssl availability
    try:
        # Run the openssl command to check if it's available
        result = subprocess.run(
            ["openssl", "version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # If openssl is available, result.returncode should be 0
        if result.returncode == 0:
            logger.log(
                f"OpenSSL version: {result.stdout.decode('utf-8').strip()}",
                level=logger.INFO,
            )
        else:
            logger.log(
                "Error: OpenSSL command failed unexpectedly",
                level=logger.ERROR,
            )
            logger.log("Cancelled SSL Certificate generation",
                       level=logger.ERROR)
            return

    except FileNotFoundError:
        # If OpenSSL is not found on the system
        logger.log(
            "Error: OpenSSL is not installed on your system",
            level=logger.ERROR,
        )
        logger.log("Cancelled SSL Certificate generation", level=logger.ERROR)
        return
    except subprocess.CalledProcessError as e:
        # Catch any errors during the command execution
        logger.log(
            f"Error: OpenSSL command failed with message: {e.stderr.decode('utf-8')}",
            level=logger.ERROR,
        )
        logger.log("Cancelled SSL Certificate generation", level=logger.ERROR)
        return

    # create commands
    private_key_cmd = ["openssl", "genrsa", "-out", "server.key", "2048"]

    csr_cmd = [
        "openssl",
        "req",
        "-new",
        "-key",
        "server.key",
        "-out",
        csr_path,
    ]

    certfile_signing_cmd = [
        "openssl",
        "req",
        "-new",
        "-key",
        private_key_path,
        "-out",
        csr_path,
        "-subj",
        f"/C={country}/ST={state}/L={locality}/O={organization}/OU={organization_unit}/CN={domain}",
    ]

    # generate private key
    process = subprocess.run(private_key_cmd, check=True)

    if process.returncode == 0:
        logger.log(
            f"Created private key in {private_key_path}",
            custom_color=logger.Fore.GREEN,
        )
    else:
        logger.log("Failed to create a private key", level=logger.ERROR)
        logger.log_raw(
            f"{process.stderr.decode('utf-8')}",
            level=logger.ERROR,
            custom_color=logger.Style.RESET_ALL,
        )
        logger.log("Cancelled SSL Certificate generation", level=logger.ERROR)
        return

    # generate csr (certificate signing request)
    process = subprocess.run(csr_cmd, check=True)
    if process.returncode == 0:
        logger.log(
            f"Created CSR (certificate signing request) in {csr_path}",
            custom_color=logger.Fore.GREEN,
        )
    else:
        logger.log("Failed to create CSR", level=logger.ERROR)
        logger.log_raw(
            f"{process.stderr.decode('utf-8')}",
            level=logger.ERROR,
            custom_color=logger.Style.RESET_ALL,
        )
        logger.log("Cancelled SSL Certificate generation", level=logger.ERROR)
        return

    # self-sign and create certificate
    process = subprocess.run(certfile_signing_cmd, check=True)
    if process.returncode == 0:
        logger.log(
            f"Created self-signed certificate in {certfile_path}",
            custom_color=logger.Fore.GREEN,
        )
        logger.log(
            "SSL certificate generated successfully.",
            custom_color=logger.Fore.GREEN,
        )
    else:
        logger.log("Failed to create ssl certificate", level=logger.ERROR)
        logger.log_raw(
            f"{process.stderr.decode('utf-8')}",
            level=logger.ERROR,
            custom_color=logger.Style.RESET_ALL,
        )
        logger.log("Cancelled SSL Certificate generation", level=logger.ERROR)
        return
