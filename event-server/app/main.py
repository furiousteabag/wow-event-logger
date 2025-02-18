from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request

from app.bot import bot, setup_bot
from app.crud.character import crud_character
from app.utils.db import SessionDep, initialize_supabase

load_dotenv()


app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_bot()
    await initialize_supabase()
    yield
    await bot.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/data", tags=["data"])
async def add_data(session: SessionDep, request: Request):

    character_data = await crud_character.get(session, realm="Doomhowl", name="Furioustea")
    print(character_data)

    try:
        await bot.bot.send_message(chat_id=123, text="test")

        return {"status": "success", "message": "Message sent successfully"}
    except Exception as e:
        return {"error": str(e)}
