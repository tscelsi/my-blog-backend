import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.auth_router import router as auth_router
from api.fragment_router import router as fragment_router
from api.memory_router import router as memory_router
from api.middleware.auth import AuthBackend
from api.middleware.supabase_client import SupabaseClientMiddleware
from api.public_router import router as public_router
from api.service_manager import ServiceManager
from api.sharing_router import router as sharing_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    service_manager = ServiceManager.get()
    await service_manager.start()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["authorization"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)
app.add_middleware(
    AuthenticationMiddleware,
    backend=AuthBackend(),
)
app.add_middleware(SupabaseClientMiddleware)

app.include_router(memory_router, tags=["memory_router"])
app.include_router(fragment_router, tags=["fragment_router"])
app.include_router(sharing_router, tags=["sharing_router"])
app.include_router(public_router, tags=["public_router"])
app.include_router(auth_router, tags=["auth_router"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=5000)
