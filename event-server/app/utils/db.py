import os
from typing import Annotated

from fastapi import Depends
from supabase import acreate_client
from supabase.client import AsyncClient

supabase_client: AsyncClient | None = None


async def initialize_supabase():
    global supabase_client

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is not set")

    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_KEY environment variable is not set")

    supabase_client = await acreate_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )


def get_db() -> AsyncClient:
    if supabase_client is None:
        raise RuntimeError("Supabase client is not initialized")
    return supabase_client


SessionDep = Annotated[AsyncClient, Depends(get_db)]
