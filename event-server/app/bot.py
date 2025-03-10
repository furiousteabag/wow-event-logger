import asyncio
import os
from typing import Optional, TypedDict

from telegram import Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes

from app.api.endpoints.character import upload_character_data
from app.crud.character import crud_character
from app.crud.character_watch import crud_character_watch
from app.schemas.character import CharacterEventData, EventWatcherRequest, GameRegion, GameVersion
from app.schemas.character_watch import CharacterWatch, CharacterWatchCreate
from app.utils.battlenet import wow_api_client
from app.utils.db import get_db
from app.utils.formatting import format_character


class CharacterParams(TypedDict):
    version: GameVersion
    region: GameRegion
    realm: str
    name: str


bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
bot = Application.builder().token(bot_token).build()


async def validate_character_params(
    command: str, args: list[str] | None
) -> tuple[Optional[CharacterParams], Optional[str]]:
    """Validate character parameters and return them if valid"""
    if not args or len(args) < 4:
        return (
            None,
            "Please provide version, region, realm and name."
            f"\n\nUsage: /{command} <version> <region> <realm> <name>"
            "\n\nArguments:\n"
            f"<version> — one of: {', '.join([v.value for v in GameVersion])}\n"
            f"<region> — one of: {', '.join([r.value for r in GameRegion])}\n",
        )

    version, region, realm, name = args[0].lower(), args[1].lower(), args[2].capitalize(), args[3].capitalize()

    valid_versions = [v.value for v in GameVersion]
    if version not in valid_versions:
        return None, f"Invalid version. Must be one of: {', '.join(valid_versions)}"

    valid_regions = [r.value for r in GameRegion]
    if region not in valid_regions:
        return None, f"Invalid region. Must be one of: {', '.join(valid_regions)}"

    return CharacterParams(version=GameVersion(version), region=GameRegion(region), realm=realm, name=name), None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey! Check what's possible via /help or start adding characters that you want to track right away with /add <version> <region> <realm> <name>"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I can monitor changes in WoW character's levels and share them with you.\n\nCommands:\n"
        "/add <version> <region> <realm> <name> — add a character to the watchlist\n"
        "/remove <version> <region> <realm> <name> — remove a character from the watchlist\n"
        "/list — show all characters in the watchlist\n"
        "/help — show this message"
        "\n\nArguments:\n"
        f"<version> — one of: {', '.join([v.value for v in GameVersion])}\n"
        f"<region> — one of: {', '.join([r.value for r in GameRegion])}\n",
    )


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    params, error_msg = await validate_character_params("add", context.args)
    if not params:
        await update.message.reply_text(error_msg or "Invalid parameters")
        return

    version, region, realm, name = params["version"], params["region"], params["realm"], params["name"]
    chat_id = update.message.chat_id

    character_api = await wow_api_client.get_character(version=version, region=region, realm=realm, name=name)
    if character_api:
        character_api_dump = character_api.model_dump()
        character_api_dump["died_at"] = (
            int(character_api_dump["died_at"].timestamp()) if character_api_dump["died_at"] else None
        )
        character_event_data = CharacterEventData(**character_api_dump)
        print(character_event_data)
    else:
        character_event_data = CharacterEventData()
    event_watcher_request = EventWatcherRequest(
        version=version,
        region=region,
        realms={realm: {name: character_event_data}},
    )
    upload_character_data_response = await upload_character_data(bot, get_db(), event_watcher_request)
    character = await crud_character.get(get_db(), version=version, region=region, realm=realm, name=name)
    if not character:
        await update.message.reply_text("Character not found in the game!")
        return

    if character_watch := await crud_character_watch.get_by_chat_and_character(
        get_db(), chat_id=chat_id, character_id=character.id
    ):
        await update.message.reply_text(
            f"Character is already in the watchlist:\n\n{format_character(character or character_watch)}",
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )
        return

    character_watch = await crud_character_watch.create(
        get_db(), obj_in=CharacterWatchCreate(chat_id=chat_id, character_id=character.id)
    )
    await update.message.reply_text(
        f"Added character to the watchlist:\n\n{format_character(character or character_watch)}",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    params, error_msg = await validate_character_params("remove", context.args)
    if not params:
        await update.message.reply_text(error_msg or "Invalid parameters")
        return

    version, region, realm, name = params["version"], params["region"], params["realm"], params["name"]
    chat_id = update.message.chat_id

    # Check if character exists in database
    character = await crud_character.get(get_db(), version=version, region=region, realm=realm, name=name)
    if not character:
        await update.message.reply_text("Character not found in the watchlist!")
        return

    character_watch = await crud_character_watch.delete_by_chat_and_character(
        get_db(), chat_id=chat_id, character_id=character.id
    )
    if not character_watch:
        await update.message.reply_text(f"Character {name} ({realm}) is not in the watchlist!")
        return

    await update.message.reply_text(
        f"Removed character from the watchlist:\n\n{format_character(character or character_watch)}",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    watches = await crud_character_watch.get_by_chat(get_db(), chat_id=chat_id)

    if not watches:
        await update.message.reply_text("Watchlist is empty!")
        return

    # Fetch all character data in parallel
    async def fetch_character(watch):
        character_data = await crud_character.get_by_id(get_db(), id=watch.character_id)
        if not character_data:
            raise ValueError(f"Character not found for watch {watch.id}")
        return character_data

    # Create tasks for all character lookups
    tasks = [fetch_character(watch) for watch in watches]
    characters = await asyncio.gather(*tasks)

    # Group characters by realm, then by alive/dead status
    realms = {}
    for character in characters:
        realm = character.realm
        is_dead = bool(character.died_at)
        formatted_char = format_character(character, include_realm=False)

        if realm not in realms:
            realms[realm] = {"alive": [], "dead": []}

        level = character.level if character.level else -1

        if is_dead:
            realms[realm]["dead"].append((character.died_at, formatted_char))
        else:
            realms[realm]["alive"].append((level, formatted_char))

    message = ""

    for realm in sorted(realms.keys()):
        message += f"🌍 *{realm.title()}*\n\n"

        if realms[realm]["alive"]:
            message += "  Alive:\n"
            for _, char in sorted(realms[realm]["alive"], key=lambda x: x[0], reverse=True):
                message += f"    {char}\n"

        if realms[realm]["dead"]:
            message += "\n  Dead:\n"
            for _, char in sorted(realms[realm]["dead"], key=lambda x: x[0], reverse=True):
                message += f"    {char}\n"

        message += "\n"

    message = message.rstrip()

    await update.message.reply_text(message, parse_mode=constants.ParseMode.MARKDOWN_V2)


async def setup_bot():
    bot.add_handler(CommandHandler("start", start_command))
    bot.add_handler(CommandHandler("help", help_command))
    bot.add_handler(CommandHandler("add", add_command))
    bot.add_handler(CommandHandler("remove", remove_command))
    bot.add_handler(CommandHandler("list", list_command))
    await bot.initialize()
    await bot.start()
    asyncio.create_task(bot.updater.start_polling())
