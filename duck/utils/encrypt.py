import base64
import zlib


def compress_and_encode(input_string):
    """Compresses and encodes the input string using zlib and base64."""
    compressed_data = zlib.compress(input_string.encode("utf-8"))
    encoded_data = base64.b64encode(compressed_data).decode("utf-8")
    return encoded_data


def decode_and_decompress(encoded_string):
    """Decodes and decompresses the input string."""
    compressed_data = base64.b64decode(encoded_string.encode("utf-8"))
    decompressed_data = zlib.decompress(compressed_data).decode("utf-8")
    return decompressed_data
