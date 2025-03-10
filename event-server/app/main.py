from dotenv import load_dotenv

load_dotenv()


import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.api import api_router
from app.bot import bot, setup_bot
from app.utils.db import initialize_supabase
from app.utils.scheduler import start_scheduler

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_bot()
    await initialize_supabase()
    scheduler_task = asyncio.create_task(start_scheduler())
    yield
    await bot.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
