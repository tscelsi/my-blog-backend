from typing import Any

from httpx import AsyncClient, Response


async def _call(
    method: str,
    url: str,
    *args: Any,
    **kwargs: Any,
) -> Response:
    """Make a http request"""
    async with AsyncClient() as client:
        response = await client.request(method, url, *args, **kwargs)
    return response


async def get(
    url: str,
    *args: Any,
    **kwargs: Any,
) -> Response:
    """Send a GET request to a server.

    Args:
        url (str): A url of a resource on which to perform a GET action.

    Returns:
        Response: A successful response from the server.
    """
    res = await _call("GET", url, *args, **kwargs)
    res.raise_for_status()
    return res
