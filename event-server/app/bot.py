import asyncio
import os

from telegram import Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes

from app.crud.character import crud_character
from app.crud.character_watch import crud_character_watch
from app.schemas.character_watch import CharacterWatchCreate
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

    if await crud_character_watch.exists(get_db(), chat_id=chat_id, realm=realm, name=name):
        await update.message.reply_text(f"Character {name} ({realm}) is already in the watchlist!")
        return

    await crud_character_watch.create(get_db(), obj_in=CharacterWatchCreate(chat_id=chat_id, realm=realm, name=name))
    await update.message.reply_text(f"Added character {name} ({realm}) to the watchlist")


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Please provide both realm and name. Usage: /remove <realm> <name>")
        return

    realm, name = context.args[0].capitalize(), context.args[1].capitalize()
    chat_id = update.message.chat_id

    if not await crud_character_watch.exists(get_db(), chat_id=chat_id, realm=realm, name=name):
        await update.message.reply_text(f"Character {name} ({realm}) is not in the watchlist!")
        return

    await crud_character_watch.delete(get_db(), chat_id=chat_id, realm=realm, name=name)
    await update.message.reply_text(f"Removed character {name} ({realm}) from the watchlist")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    watches = await crud_character_watch.get_by_chat(get_db(), chat_id=chat_id)
    if not watches:
        await update.message.reply_text("Watchlist is empty!")
        return

    message = "Characters in the watchlist:\n\n"
    for watch in watches:
        character_data = await crud_character.get(get_db(), realm=watch.realm, name=watch.name)
        if character_data:
            message += f"• {format_character(character_data)}\n"
        else:
            message += f"• {format_character(watch)}\n"
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
