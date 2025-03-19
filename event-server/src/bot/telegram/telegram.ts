import { populateCharacter } from "../../battlenet/battlenet"
import { handleCharactersUpdates } from "../../character/characterUpdate"
import { supabase } from "../../supabase/client"
import {
  type Character,
  type CharacterFull,
  CharacterTelegramSchema,
  type CharactersEvents,
  gameRegionEnum,
  gameVersionEnum,
} from "../../types/character"
import { formatCharacter } from "../../utils/formatter"
import logger from "../../utils/logger"
import { Bot } from "grammy"
import { z } from "zod"

if (!process.env.TELEGRAM_BOT_TOKEN) {
  throw new Error("TELEGRAM_BOT_TOKEN is required")
}

const bot = new Bot(process.env.TELEGRAM_BOT_TOKEN)

const VERSION_OPTIONS = gameVersionEnum.innerType().options.join(", ")
const REGION_OPTIONS = gameRegionEnum.innerType().options.join(", ")
const ARGS_HELP_MESSAGE = [
  "Arguments:",
  `<version> — one of: ${VERSION_OPTIONS}`,
  `<region> — one of: ${REGION_OPTIONS}`,
].join("\n")

const START_MESSAGE = [
  "Hey! Check what's possible via /help or start adding characters that you want to track right away with:",
  "",
  "/add <version> <region> <realm> <name>",
  "",
  ARGS_HELP_MESSAGE,
].join("\n")

const HELP_MESSAGE = [
  "I can monitor changes in WoW character's levels and share them with you.",
  "",
  "Commands:",
  "/add <version> <region> <realm> <name> — add a character to the watchlist",
  "/remove <version> <region> <realm> <name> — remove a character from the watchlist",
  "/list — show all characters in the watchlist",
  "/help — show this message",
  "",
  ARGS_HELP_MESSAGE,
].join("\n")

export type ValidationResult = { data: Character; error: null } | { data: null; error: string }

function validateParams(command: string, args?: string[]): ValidationResult {
  const defaultError = [
    "Please provide version, region, realm and name.",
    "",
    `Usage: /${command} <version> <region> <realm> <name>`,
    "",
    ARGS_HELP_MESSAGE,
  ].join("\n")

  if (!args || args.length < 4) return { data: null, error: defaultError }
  try {
    const [versionArg, regionArg, realmArg, nameArg] = args
    const result = CharacterTelegramSchema.parse({
      version: versionArg,
      region: regionArg,
      realm: realmArg,
      name: nameArg,
    })
    return { data: result, error: null }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const firstError = error.errors[0]
      const path = firstError?.path?.[0]
      const message = firstError?.message

      return { data: null, error: `${path} is invalid: ${message}` }
    }
    return { data: null, error: defaultError }
  }
}

bot.command("start", (ctx) => ctx.reply(START_MESSAGE))

bot.command("help", (ctx) => ctx.reply(HELP_MESSAGE))

bot.command("add", async (ctx) => {
  const chatId = ctx.chat.id
  const args = ctx.message?.text?.split(" ").slice(1)
  const { data: characterData, error } = validateParams("add", args)
  if (error !== null) return ctx.reply(error)
  const characterDataPopulated = await populateCharacter(characterData)
  const [characterFull] = await handleCharactersUpdates([characterDataPopulated], [notifyTelegramSubscribers])
  const { data: existingWatches, error: watchError } = await supabase
    .from("character_watch_chat_telegram")
    .select("id")
    .eq("character_id", characterFull.id)
    .eq("chat_id", chatId)
    .maybeSingle()
  if (watchError) {
    logger.error("Error checking for existing watch:", watchError)
    return ctx.reply(`Error checking if character is already being watched: ${watchError.message}`)
  }
  if (existingWatches)
    return ctx.reply(`This character is already in the watchlist:\n\n${formatCharacter(characterFull)}`, {
      parse_mode: "MarkdownV2",
      link_preview_options: {
        is_disabled: true,
      },
    })
  const { error: insertError } = await supabase.from("character_watch_chat_telegram").insert({
    character_id: characterFull.id,
    chat_id: chatId,
  })
  if (insertError) {
    logger.error("Error adding watch:", insertError)
    return ctx.reply(`Error adding character to watchlist: ${insertError.message}`)
  }
  return ctx.reply(`Added character to watchlist:\n\n${formatCharacter(characterFull)}`, {
    parse_mode: "MarkdownV2",
    link_preview_options: {
      is_disabled: true,
    },
  })
})

bot.command("remove", async (ctx) => {
  const chatId = ctx.chat.id
  const args = ctx.message?.text?.split(" ").slice(1)
  const { data: characterData, error } = validateParams("remove", args)
  if (error !== null) return ctx.reply(error)

  const { data: characterFull, error: characterError } = await supabase
    .from("character")
    .select("*")
    .eq("name", characterData.name)
    .eq("realm", characterData.realm)
    .eq("region", characterData.region)
    .eq("version", characterData.version)
    .single()
  if (characterError) {
    logger.error("Error fetching character:", characterError)
    return ctx.reply(`Character ${characterData.name} was not found in the database!`)
  }

  const { error: deleteError } = await supabase
    .from("character_watch_chat_telegram")
    .delete()
    .eq("character_id", characterFull.id)
    .eq("chat_id", chatId)
  if (deleteError) {
    logger.error("Error removing watch:", deleteError)
    return ctx.reply(`Character ${characterData.name} is not in the watchlist!`)
  }
  return ctx.reply(`Removed character from watchlist:\n\n${formatCharacter(characterFull)}`, {
    parse_mode: "MarkdownV2",
    link_preview_options: {
      is_disabled: true,
    },
  })
})

bot.command("list", async (ctx) => {
  const chatId = ctx.chat.id

  const { data: watches, error: watchesError } = await supabase
    .from("character_watch_chat_telegram")
    .select("character_id")
    .eq("chat_id", chatId)

  if (watchesError) {
    logger.error("Error fetching watches:", watchesError)
    return ctx.reply("Error fetching your watchlist!")
  }

  if (!watches || watches.length === 0) {
    return ctx.reply("Watchlist is empty!")
  }

  const { data: characters, error: charactersError } = await supabase
    .from("character")
    .select("*")
    .in(
      "id",
      watches.map((watch) => watch.character_id),
    )

  if (charactersError || !characters) {
    logger.error("Error fetching characters:", charactersError)
    return ctx.reply("Error fetching character data!")
  }

  const realms: Record<
    string,
    {
      alive: Array<[number, string]>
      dead: Array<[string | null, string]>
    }
  > = {}

  for (const character of characters) {
    const realm = character.realm
    const isDead = Boolean(character.died_at)
    const formattedChar = formatCharacter(character, false)

    if (!realms[realm]) {
      realms[realm] = { alive: [], dead: [] }
    }

    const level = character.level || -1

    if (isDead) {
      realms[realm].dead.push([character.died_at, formattedChar])
    } else {
      realms[realm].alive.push([level, formattedChar])
    }
  }

  let message = ""

  for (const realm of Object.keys(realms).sort()) {
    message += `🌍 *${realm}*\n\n`

    if (realms[realm].alive.length > 0) {
      message += "  Alive:\n"
      // Sort by level, highest first
      realms[realm].alive.sort((a, b) => b[0] - a[0])
      for (const [, formattedChar] of realms[realm].alive) {
        message += `    ${formattedChar}\n`
      }
    }

    if (realms[realm].dead.length > 0) {
      message += "\n  Dead:\n"
      // Sort by death date, most recent first
      realms[realm].dead.sort((a, b) => {
        if (!a[0]) return 1
        if (!b[0]) return -1
        return b[0].localeCompare(a[0])
      })
      for (const [, formattedChar] of realms[realm].dead) {
        message += `    ${formattedChar}\n`
      }
    }

    message += "\n"
  }

  message = message.trim()

  return ctx.reply(message, {
    parse_mode: "MarkdownV2",
    link_preview_options: {
      is_disabled: true,
    },
  })
})

export async function notifyTelegramSubscribers(events: CharactersEvents): Promise<void> {
  logger.info(
    `Notifying Telegram subscribers about ${events.level_ups.length} level up(s) and ${events.deaths.length} death(s)...`,
  )

  const allCharacterIds = [...events.level_ups.map((char) => char.id), ...events.deaths.map((char) => char.id)]
  if (allCharacterIds.length === 0) {
    logger.info("No characters to notify about")
    return
  }

  const { data: watches, error: watchesError } = await supabase
    .from("character_watch_chat_telegram")
    .select("chat_id, character_id")
    .in("character_id", allCharacterIds)
  if (watchesError) {
    logger.error("Error fetching character watches:", watchesError)
    return
  }
  if (!watches || watches.length === 0) {
    logger.info("No watches found for these characters")
    return
  }

  interface NotificationGroups {
    levelUps: Record<number, CharacterFull[]>
    deaths: Record<number, CharacterFull[]>
  }
  const notifications: NotificationGroups = {
    levelUps: {},
    deaths: {},
  }

  const characterDeathIds = new Set(events.deaths.map((char) => char.id))
  for (const character of events.deaths) {
    const characterWatches = watches.filter((watch) => watch.character_id === character.id)
    for (const watch of characterWatches) {
      if (!notifications.deaths[watch.chat_id]) {
        notifications.deaths[watch.chat_id] = []
      }
      notifications.deaths[watch.chat_id].push(character)
    }
  }

  // Group level up notifications, but only for characters that didn't die
  for (const character of events.level_ups) {
    if (characterDeathIds.has(character.id)) {
      continue
    }
    const characterWatches = watches.filter((watch) => watch.character_id === character.id)
    for (const watch of characterWatches) {
      if (!notifications.levelUps[watch.chat_id]) {
        notifications.levelUps[watch.chat_id] = []
      }
      notifications.levelUps[watch.chat_id].push(character)
    }
  }

  // Helper function to send notifications
  async function sendNotification(chatId: string, characters: CharacterFull[], type: "level-up" | "death") {
    if (characters.length === 0) return

    const header = type === "level-up" ? "🎉 LEVEL UP\\! 🎉" : "☠️ DEATH ☠️"
    const message = `${header}\n\n${characters.map((char) => formatCharacter(char)).join("\n")}`

    logger.info(`Sending ${type} notification to chat_id: ${chatId}`)

    try {
      await bot.api.sendMessage(parseInt(chatId), message, {
        parse_mode: "MarkdownV2",
        link_preview_options: {
          is_disabled: true,
        },
      })
    } catch (error) {
      logger.error(`Error sending ${type} notification to chat ${chatId}: ${error}`)
      // if (
      //   error.description?.includes("bot was blocked") ||
      //   error.description?.includes("chat not found") ||
      //   error.description?.includes("user is deactivated")
      // ) {
      //   logger.warning(`Chat ${chatId} no longer accessible, removing watches`)

      //   // Remove all watches for this chat
      //   const { error: deleteError } = await supabase
      //     .from("character_watch_chat_telegram")
      //     .delete()
      //     .eq("chat_id", chatId)

      //   if (deleteError) {
      //     logger.error(`Error removing watches for chat ${chatId}:`, deleteError)
      //   }
    }
    // else {
    //   logger.error(`Error sending ${type} notification to chat ${chatId}:`, error)
    // }
  }

  for (const [chatId, characters] of Object.entries(notifications.levelUps)) {
    await sendNotification(chatId, characters, "level-up")
  }

  for (const [chatId, characters] of Object.entries(notifications.deaths)) {
    await sendNotification(chatId, characters, "death")
  }
}

export function startTelegramBot() {
  bot.start()
  logger.info("Telegram bot started")
}
