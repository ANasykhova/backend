import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5435/hw"


@asynccontextmanager
async def database_lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with asyncpg.create_pool(
        os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        min_size=0,
        timeout=5,
        command_timeout=5,
    ) as pool:
        app.state.database_pool = pool
        yield


def get_database_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.database_pool
