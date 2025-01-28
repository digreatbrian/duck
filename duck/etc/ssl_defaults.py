import ssl

from duck.settings import SETTINGS

SSL_DEFAULTS = {
    "certfile": SETTINGS["SSL_CERTFILE_LOCATION"],
    "keyfile": SETTINGS["SSL_PRIVATE_KEY_LOCATION"],
    "version": ssl.PROTOCOL_TLS_SERVER,
    "ciphers": None,
}
