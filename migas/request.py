"""Stripped down, minimal import way to communicate with server"""
from __future__ import annotations

import json
import os
import warnings
from typing import Optional, Tuple, Union
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

from . import __version__

ETResponse = Tuple[int, Union[dict, str]]  # status code, body

DEFAULT_TIMEOUT = 3
TIMEOUT_RESPONSE = (
    408,
    {"data": None, "errors": [{"message": "Connection to server timed out."}]},
)
UNAVAIL_RESPONSE = (503, {"data": None, "errors": [{"message": "Could not connect to server."}]})


def request(
    url: str,
    *,
    query: str = None,
    timeout: float = None,
    method: str = "POST",
    chunk_size: int | None = None,
    wait: bool = False,
) -> None:
    """
    Send a non-blocking call to the server.

    This will never check the future, and no assumptions can be made about server receptivity.
    """
    with ThreadPoolExecutor() as executor:
        future = executor.submit(
            _request, url, query=query, timeout=timeout, method=method, chunk_size=chunk_size,
        )

        if wait is True:
            return future.result()


def _request(
    url: str,
    *,
    query: str = None,
    timeout: float = None,
    method: str = "POST",
    chunk_size: int = None,
) -> ETResponse:
    purl = urlparse(url)
    # TODO: 3.10 - Replace with match/case
    if purl.scheme == 'https':
        Connection = HTTPSConnection
    elif purl.scheme == 'http':
        Connection = HTTPConnection
    else:
        raise ValueError("URL scheme not supported")

    timeout = timeout or float(os.getenv("MIGAS_TIMEOUT", DEFAULT_TIMEOUT))
    conn = Connection(purl.netloc, timeout=timeout)
    headers = {
        'User-Agent': f'migas-client/{__version__}',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
    }
    body = None
    if query:
        body = json.dumps({"query": query}).encode("utf-8")
        headers.update(
            {
                'Content-Length': len(body),
                'Content-Type': 'application/json; charset=utf-8',
            }
        )

    try:
        conn.request(method, purl.path, body=body, headers=headers)
        response = conn.getresponse()
        encoding = response.headers.get('content-encoding')
        body = _read_response(response, encoding, chunk_size)
    except TimeoutError:
        return TIMEOUT_RESPONSE
    except ConnectionError:
        return UNAVAIL_RESPONSE
    except OSError as e:
        # Python < 3.10, this could be socket.timeout or socket.gaierror
        import socket

        if isinstance(e, socket.timeout):
            return TIMEOUT_RESPONSE
        else:
            return UNAVAIL_RESPONSE
    finally:
        conn.close()

    if body and response.headers.get("content-type", "").startswith("application/json"):
        body = json.loads(body)

    if not response.headers.get("X-Backend-Server"):
        warnings.warn(
            "migas server is incorrectly configured.",
            UserWarning,
            stacklevel=1,
        )
    return response.status, body


def _read_response(
    response: HTTPResponse,
    encoding: Optional[str] = None,
    chunk_size: Optional[int] = None
) -> str:
    """
    Read and aggregate the response body.

    If `chunk_size` is `None`, the entire response is read at once.
    """
    stream = b''
    # TODO: 3.8 - Replace with walrus
    # while chunk := response.read(chunk_size):
    chunk = 1
    while chunk:
        chunk = response.read(chunk_size)
        stream += chunk

    if encoding:
        stream = _decompress_stream(stream, encoding)
    return stream.decode()


def _decompress_stream(stream: bytes, encoding: str) -> bytes:
    """
    Decompress the compressed response byte stream.
    """
    # TODO: 3.10 - replace with match
    if encoding == 'gzip':
        import gzip

        decomp = gzip.decompress(stream)
    elif encoding == 'deflate':
        import zlib

        decomp = zlib.decompress(stream)
    else:
        raise NotImplementedError(f'Cannot decode response with encoding "{encoding}>"')
    return decomp
