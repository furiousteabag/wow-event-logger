from dotenv import load_dotenv
from telegram.error import Forbidden

load_dotenv()


from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from loguru import logger

from app.bot import bot, setup_bot
from app.crud.character import crud_character
from app.crud.character_watch import crud_character_watch
from app.schemas.character import CharacterCreate, CharacterUpdate, EventWatcherRequest
from app.schemas.common import ResponseModel
from app.utils.db import SessionDep, initialize_supabase
from app.utils.formatting import format_character

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_bot()
    await initialize_supabase()
    yield
    await bot.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Yo! Check /docs for API documentation"}


@app.post("/character", tags=["Characters"])
async def add_data(session: SessionDep, request: EventWatcherRequest) -> ResponseModel:
    """
    Update or create character data and notify watchers of changes
    """
    try:
        notifications: dict[int, list[str]] = {}

        for realm_name, realm_data in request.realms.items():
            for char_name, char_info in realm_data.watchlist.items():
                existing_char = await crud_character.get(session, realm=realm_name, name=char_name)

                should_notify = False
                updated_char = None

                if existing_char:
                    if existing_char.level > char_info.level:
                        continue
                    if (
                        existing_char.level < char_info.level
                        or existing_char.online != char_info.online
                        or existing_char.zone != char_info.zone
                    ):
                        updated_char = await crud_character.update(
                            session,
                            realm=realm_name,
                            name=char_name,
                            obj_in=CharacterUpdate(level=char_info.level, online=char_info.online, zone=char_info.zone),
                        )
                        should_notify = existing_char.level < char_info.level
                else:
                    new_char = CharacterCreate(
                        **{
                            "realm": realm_name,
                            "name": char_name,
                            "level": char_info.level,
                            "class": char_info.class_,
                            "online": char_info.online,
                            "zone": char_info.zone,
                        }
                    )
                    updated_char = await crud_character.create(session, obj_in=new_char)
                    should_notify = True

                if should_notify and updated_char:
                    watchers = await crud_character_watch.get_by_character(session, realm=realm_name, name=char_name)
                    char_update = format_character(updated_char)

                    for watcher in watchers:
                        if watcher.chat_id not in notifications:
                            notifications[watcher.chat_id] = []
                        notifications[watcher.chat_id].append(char_update)

        # Send grouped notifications
        for chat_id, char_updates in notifications.items():
            if char_updates:
                message = "🎉 LEVEL UP\\! 🎉\n\n" + "\n".join(f"• {update}" for update in char_updates)
                logger.info(f"Sending message to chat_id: {chat_id}")
                try:
                    await bot.bot.send_message(chat_id=chat_id, text=message, parse_mode="MarkdownV2")
                except Forbidden as e:
                    await crud_character_watch.delete_by_chat(session, chat_id=chat_id)

        return {"status": "success", "message": "Character data processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
