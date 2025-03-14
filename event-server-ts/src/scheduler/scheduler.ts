import { populateCharacter } from "../battlenet/battlenet"
import { notifyTelegramSubscribers } from "../bot/telegram/telegram"
import { handleCharactersUpdates } from "../character/characterUpdate"
import { supabase } from "../supabase/client"
import logger from "../utils/logger"

async function updateWatchedCharacters() {
  try {
    logger.info("Starting watched characters update process...")

    const { data: watchedCharacters, error } = await supabase.rpc("get_watched_characters")
    if (error) {
      logger.error(`Error fetching characters: ${error.message}`)
      throw new Error("Error fetching characters")
    }
    if (!watchedCharacters || watchedCharacters.length === 0) {
      logger.info("No watched characters found")
      return
    }
    logger.info(`Found ${watchedCharacters.length} watched character(s), retrieving battlenet data...`)

    const updatedCharacters = await Promise.all(
      watchedCharacters.map(async (character) => {
        try {
          const updatedCharacter = await populateCharacter(character)
          return updatedCharacter
        } catch (error) {
          logger.error(`Error updating character ${character.name}: ${error}`)
          return character
        }
      }),
    )

    await handleCharactersUpdates(updatedCharacters, [notifyTelegramSubscribers])
  } catch (error) {
    logger.error(`Character update process failed: ${error}`)
    throw error
  }
}

async function runUpdateWatchedCharacters() {
  try {
    await updateWatchedCharacters()
  } catch (error) {
    console.error("Failed to update watched characters:", error)
  }
}

export function startWatchedCharacterUpdateScheduler(intervalHours: number) {
  logger.info(`Starting character update scheduler (interval: ${intervalHours} hour(s))`)
  const intervalMs = intervalHours * 60 * 60 * 1000
  runUpdateWatchedCharacters()
  setInterval(runUpdateWatchedCharacters, intervalMs)
}
