import asyncio
import os

from telegram import Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes

from app.crud.character import crud_character
from app.crud.character_watch import crud_character_watch
from app.schemas.character_watch import CharacterWatch, CharacterWatchCreate
from app.utils.db import get_db
from app.utils.formatting import format_character

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
bot = Application.builder().token(bot_token).build()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey! Check what's possible via /help or start adding characters that you want to track right away with /add <realm> <name>"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I can monitor changes in WoW character's levels and share them with you.\n\nCommands:\n/add <realm> <name> — add a character to the watchlist\n/remove <realm> <name> — remove a character from the watchlist\n/list — show all characters in the watchlist\n/help — show this message"
    )


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Please provide both realm and name. Usage: /add <realm> <name>")
        return

    realm, name = context.args[0].capitalize(), context.args[1].capitalize()
    chat_id = update.message.chat_id
    character = await crud_character.get(get_db(), realm=realm, name=name)

    if character_watch := await crud_character_watch.get(get_db(), chat_id=chat_id, realm=realm, name=name):
        await update.message.reply_text(
            f"Character is already in the watchlist:\n\n{format_character(character or character_watch)}",
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )
        return

    character_watch = await crud_character_watch.create(
        get_db(), obj_in=CharacterWatchCreate(chat_id=chat_id, realm=realm, name=name)
    )
    await update.message.reply_text(
        f"Added character to the watchlist:\n\n{format_character(character or character_watch)}",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Please provide both realm and name. Usage: /remove <realm> <name>")
        return

    realm, name = context.args[0].capitalize(), context.args[1].capitalize()
    chat_id = update.message.chat_id
    character = await crud_character.get(get_db(), realm=realm, name=name)

    character_watch = await crud_character_watch.delete(get_db(), chat_id=chat_id, realm=realm, name=name)
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

    # Group characters by realm, then by living/dead status
    realms = {}

    for watch in watches:
        character_data = await crud_character.get(get_db(), realm=watch.realm, name=watch.name)

        if character_data:
            # Use the actual character data if available
            character = character_data
            realm = character.realm
            is_dead = bool(character.died_at)
        else:
            # If we don't have character data yet, use watch data and assume they're alive
            character = watch
            realm = watch.realm
            is_dead = False

        formatted_char = format_character(character, include_realm=False)

        if realm not in realms:
            realms[realm] = {"living": [], "dead": []}

        level = character.level if not isinstance(character, CharacterWatch) else -1

        if is_dead:
            realms[realm]["dead"].append((level, formatted_char))
        else:
            realms[realm]["living"].append((level, formatted_char))

    message = ""

    for realm in sorted(realms.keys()):
        message += f"🌍 *{realm.title()}*\n"

        if realms[realm]["living"]:
            message += "  Living:\n"
            for _, char in sorted(realms[realm]["living"], key=lambda x: x[0], reverse=True):
                message += f"    {char}\n"

        if realms[realm]["dead"]:
            message += "  Dead:\n"
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
