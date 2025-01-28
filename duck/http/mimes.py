import mimetypes


def guess_file_mimetype(filename: str) -> str:
    """
    Determine the MIME type of a file based on its filename or content.

    This function first attempts to guess the MIME type using the file's
    extension by leveraging the `mimetypes` module. If the MIME type could not
    be determined from the filename, it reads the file content and attempts to
    infer the MIME type from the data.

    Args:
        filename (str): The path to the file for which the MIME type needs to be determined.

    Returns:
        str: The determined MIME type of the file. Defaults to 'application/octet-stream' if the type cannot be determined.
    """
    mimetype = None

    if filename:
        # Attempt to guess the MIME type based on the file extension
        mimetype, _ = mimetypes.guess_type(filename)
    return mimetype


def guess_data_mimetype(data: bytes) -> str:
    """
    Determine the MIME type of the provided content or file based on its initial bytes.

    This function checks the initial bytes of the data to infer its MIME type by matching
    known signatures for various file types (e.g., images, text, compressed files, etc.).
    If no known signature is detected, it defaults to 'application/octet-stream'.

    Args:
        data (bytes): The input data for which the MIME type needs to be determined.

    Returns:
        str: The determined MIME type of the input data.
    """
    html_tags = [
        b"<html",
        b"<!DOCTYPE html",
        b"<head>",
        b"<body>",
        b"<title>",
        b"<h1>",
        b"<div>",
        b"<span>",
        b"<p>",
        b"<a ",
        b"<img ",
        b"<script",
        b"<style",
        b"<meta",
        b"<link",
        b"<form",
        b"<table>",
        b"<tr>",
        b"<td>",
        b"<th>",
        b"<ul>",
        b"<ol>",
        b"<li>",
        b"<header>",
        b"<footer>",
        b"<nav>",
        b"<section>",
        b"<article>",
        b"<aside>",
        b"<main>",
        b"<figure>",
        b"<figcaption>",
        b"<blockquote>",
        b"<pre>",
        b"<code>",
        b"<canvas>",
        b"<svg>",
        b"<br",
        b"<b>",
    ]
    data = data.lstrip()
    if data.startswith(b"\xFF\xD8"):
        return "image/jpeg"
    elif data.startswith(b"\x89PNG\r\n\x1A\n"):
        return "image/png"
    elif data.startswith(b"GIF89a") or data.startswith(b"GIF87a"):
        return "image/gif"
    elif data.startswith(b"%PDF-"):
        return "application/pdf"
    elif data.startswith(b"PK\x03\x04"):
        return "application/zip"
    elif data.startswith(b"PK\x05\x06") or data.startswith(b"PK\x07\x08"):
        return "application/zip"
    elif data.startswith(b"\x1F\x8B"):
        return "application/gzip"
    elif any(tag in data[:500] for tag in html_tags):
        return "text/html"
    elif data.startswith(b"{") and data.rstrip().endswith(b"}"):
        return "application/json"
    elif data.startswith(b"<"):
        return "application/xml"
    elif data.startswith(b"OggS"):
        return "application/ogg"
    elif data.startswith(b"\x00\x00\x00\x18ftyp"):
        return "video/mp4"
    elif data.startswith(b"\x52\x49\x46\x46") and data[8:12] == b"AVI ":
        return "video/x-msvideo"
    elif data.startswith(b"MThd"):
        return "audio/midi"
    elif data.startswith(b"ID3") or data[0:2] == b"\xff\xfb":
        return "audio/mpeg"
    elif data.startswith(b"/*") or data.startswith(b"@charset") or b"{\n" in data[:500] or b"{\r\n" in data[:500]:
        return "text/css"
    elif data.startswith(b"//") or data.startswith(b"/*") or b"function " in data[:500] or b"var " in data[:500] or b"let " in data[:500] or b"const " in data[:500]:
        return "application/javascript"
    elif all(32 <= byte <= 126 or byte in (9, 10, 13) for byte in data):
        return "text/plain"
    else:
        return "application/octet-stream"
