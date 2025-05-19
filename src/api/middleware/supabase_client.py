from typing import Awaitable, Callable

import supabase
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.service_manager import SupabaseSettings


class SupabaseClientMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if (
            request.method != "OPTIONS"
            and request.headers.get("Authorization") is not None
        ):
            supabase_settings = SupabaseSettings()  # type: ignore
            supabase_client = await supabase.create_async_client(
                supabase_url="https://tzppymbakxwelmkouucs.supabase.co",
                supabase_key=supabase_settings.SUPABASE_KEY,
                options=supabase.AClientOptions(
                    headers={
                        "Authorization": f"{request.headers['Authorization']}"
                    }
                ),
            )
            request.state.supabase_client = supabase_client
        response = await call_next(request)
        return response
