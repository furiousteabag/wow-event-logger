from dotenv import load_dotenv

load_dotenv()


import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from loguru import logger
from telegram.error import Forbidden

from app.bot import bot, setup_bot
from app.crud.character import crud_character
from app.crud.character_watch import crud_character_watch
from app.schemas.character import CharacterCreate, CharacterUpdate, EventWatcherRequest
from app.schemas.common import ResponseModel
from app.utils.db import SessionDep, initialize_supabase
from app.utils.formatting import format_character
from app.utils.scheduler import start_scheduler

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_bot()
    await initialize_supabase()

    scheduler_task = asyncio.create_task(start_scheduler(add_data))

    yield

    await bot.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/character", tags=["Characters"])
async def add_data(session: SessionDep, request: EventWatcherRequest) -> ResponseModel:
    """
    Update or create character data and notify watchers of changes
    """
    try:
        level_up_notifications: dict[int, list[str]] = {}
        death_notifications: dict[int, list[str]] = {}

        for realm_name, realm_data in request.realms.items():
            for char_name, char_info in realm_data.watchlist.items():
                existing_char = await crud_character.get(session, realm=realm_name, name=char_name)

                should_notify_level_up = False
                should_notify_death = False
                updated_char = None

                if existing_char:
                    if existing_char.level > char_info.level:
                        continue

                    char_died = not existing_char.died_at and char_info.died_at

                    if (
                        existing_char.level < char_info.level
                        or existing_char.online != char_info.online
                        or existing_char.zone != char_info.zone
                        or char_died
                    ):
                        updated_char = await crud_character.update(
                            session,
                            realm=realm_name,
                            name=char_name,
                            obj_in=CharacterUpdate(
                                level=char_info.level,
                                online=char_info.online,
                                zone=char_info.zone,
                                died_at=char_info.died_at if char_info.died_at else None,
                            ),
                        )
                        # If character died, only send death notification, otherwise check for level up
                        should_notify_death = char_died
                        should_notify_level_up = (existing_char.level < char_info.level) and not should_notify_death
                else:
                    new_char = CharacterCreate(
                        **{
                            "realm": realm_name,
                            "name": char_name,
                            "level": char_info.level,
                            "class": char_info.class_,
                            "online": char_info.online,
                            "zone": char_info.zone,
                            "died_at": char_info.died_at if char_info.died_at else None,
                        }
                    )
                    updated_char = await crud_character.create(session, obj_in=new_char)
                    # For new characters, prioritize death notification over level up
                    should_notify_death = bool(char_info.died_at)
                    should_notify_level_up = not should_notify_death

                if updated_char:
                    watchers = await crud_character_watch.get_by_character(session, realm=realm_name, name=char_name)
                    char_update = format_character(updated_char)

                    for watcher in watchers:
                        if should_notify_level_up:
                            if watcher.chat_id not in level_up_notifications:
                                level_up_notifications[watcher.chat_id] = []
                            level_up_notifications[watcher.chat_id].append(char_update)

                        if should_notify_death:
                            if watcher.chat_id not in death_notifications:
                                death_notifications[watcher.chat_id] = []
                            death_notifications[watcher.chat_id].append(char_update)

        # Send level up notifications to each chat separately
        for chat_id, char_updates in level_up_notifications.items():
            if char_updates:
                message = "🎉 LEVEL UP\\! 🎉\n\n" + "\n".join(f"{update}" for update in char_updates)
                logger.info(f"Sending level up message to chat_id: {chat_id}")
                try:
                    await bot.bot.send_message(chat_id=chat_id, text=message, parse_mode="MarkdownV2")
                except Forbidden as e:
                    logger.warning(f"Chat {chat_id} no longer accessible, removing watches: {e}")
                    await crud_character_watch.delete_by_chat(session, chat_id=chat_id)
                except Exception as e:
                    logger.error(f"Error sending level up notification to chat {chat_id}: {e}")

        # Send death notifications to each chat separately
        for chat_id, char_updates in death_notifications.items():
            if char_updates:
                message = "☠️ DEATH ☠️\n\n" + "\n".join(f"{update}" for update in char_updates)
                logger.info(f"Sending death message to chat_id: {chat_id}")
                try:
                    await bot.bot.send_message(chat_id=chat_id, text=message, parse_mode="MarkdownV2")
                except Forbidden as e:
                    logger.warning(f"Chat {chat_id} no longer accessible, removing watches: {e}")
                    await crud_character_watch.delete_by_chat(session, chat_id=chat_id)
                except Exception as e:
                    logger.error(f"Error sending death notification to chat {chat_id}: {e}")

        return {"status": "success", "message": "Character data processed successfully"}
    except Exception as e:
        logger.error(f"Error processing character data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Yo! Check /docs for API documentation"}
