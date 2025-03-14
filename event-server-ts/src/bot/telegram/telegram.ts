import type { CharactersEvents } from "../../types/character"
import logger from "../../utils/logger"

export async function notifyTelegramSubscribers(events: CharactersEvents) {
  logger.info(
    `Notifying Telegram subscribers about ${events.level_ups.length} level up(s) and ${events.deaths.length} death(s)...`,
  )
}
