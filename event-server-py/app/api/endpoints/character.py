import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from telegram.error import Forbidden
from telegram.ext import ContextTypes, ExtBot, JobQueue
from telegram.ext._application import Application
from telegram.ext._utils.types import BD, BT, CCT, CD, JQ, UD
from tqdm import tqdm

from app.crud.character import crud_character
from app.crud.character_watch import crud_character_watch
from app.schemas.character import CharacterCreate, CharacterEventData, CharacterUpdate, EventWatcherRequest
from app.schemas.common import ResponseModel
from app.utils.db import SessionDep
from app.utils.formatting import format_character

router = APIRouter()


def get_bot():
    from app.bot import bot

    return bot


BotDep = Annotated[
    Application[
        ExtBot[None],
        ContextTypes.DEFAULT_TYPE,
        dict[Any, Any],
        dict[Any, Any],
        dict[Any, Any],
        JobQueue[ContextTypes.DEFAULT_TYPE],
    ],
    Depends(get_bot),
]


@router.post("")
async def upload_character_data(
    bot: BotDep,
    session: SessionDep,
    request: EventWatcherRequest,
) -> ResponseModel:
    """
    Update or create character data and notify watchers of changes
    """
    try:
        # Shared dictionaries for notifications across all tasks
        level_up_notifications: dict[int, list[str]] = {}
        death_notifications: dict[int, list[str]] = {}

        async def process_character(realm_name: str, char_name: str, char_info: CharacterEventData):
            existing_char = await crud_character.get(
                session, version=request.version, region=request.region, realm=realm_name, name=char_name
            )

            if char_name == "Furiousbag":
                print(char_info)

            should_notify_level_up = False
            should_notify_death = False
            updated_char = None

            if existing_char:
                if existing_char.level and (not char_info.level or existing_char.level > char_info.level):
                    return

                char_died = not existing_char.died_at and char_info.died_at
                if (
                    (not existing_char.level and char_info.level)
                    or (existing_char.level and char_info.level and existing_char.level < char_info.level)
                    or (existing_char.online != char_info.online)
                    or existing_char.zone != char_info.zone
                    or char_died
                ):
                    updated_char = await crud_character.update_by_id(
                        session,
                        id=existing_char.id,
                        obj_in=CharacterUpdate(
                            level=char_info.level if char_info.level else existing_char.level,
                            online=char_info.online if type(char_info.online) == bool else existing_char.online,
                            zone=char_info.zone if char_info.zone else existing_char.zone,
                            died_at=(
                                char_info.died_at
                                if (char_info.died_at and not existing_char.died_at)
                                else (int(existing_char.died_at.timestamp()) if existing_char.died_at else None)
                            ),
                        ),
                    )
                    if not updated_char:
                        raise HTTPException(status_code=500, detail=f"Error updating character {char_name}")
                    # If character died, only send death notification, otherwise check for level up
                    should_notify_death = char_died
                    should_notify_level_up = (
                        (not existing_char.level and char_info.level)
                        or (existing_char.level and char_info.level and (existing_char.level < char_info.level))
                    ) and not should_notify_death
            else:
                new_char = CharacterCreate(
                    version=request.version,
                    region=request.region,
                    realm=realm_name,
                    name=char_name,
                    class_=char_info.class_,
                    level=char_info.level,
                    online=char_info.online,
                    zone=char_info.zone,
                    died_at=char_info.died_at if char_info.died_at else None,
                )
                updated_char = await crud_character.create(session, obj_in=new_char)
                # For new characters, prioritize death notification over level up
                should_notify_death = bool(char_info.died_at)
                should_notify_level_up = not should_notify_death

            if updated_char:
                watchers = await crud_character_watch.get_by_character_id(session, character_id=updated_char.id)
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

        # Process all realms and characters in parallel
        tasks = []
        for realm_name, realm_data in request.realms.items():
            for char_name, char_info in realm_data.items():
                tasks.append(process_character(realm_name, char_name, char_info))

        # Use tqdm to show progress while processing tasks
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            await f

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
