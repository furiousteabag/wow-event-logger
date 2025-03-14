import type { Character, CharactersEvents } from "../types/character"
import logger from "../utils/logger"

export async function handleCharactersUpdates(
  characters: Character[],
  notifySubscribers: ((events: CharactersEvents) => Promise<void>)[],
): Promise<CharactersEvents> {
  logger.info(`Handling updates for ${characters.length} character(s)...`)

  const charactersEvents: CharactersEvents = {
    level_ups: [],
    deaths: [],
  }

  await Promise.all(notifySubscribers.map((notifyFn) => notifyFn(charactersEvents)))

  logger.info(`Finished handling updates for ${characters.length} character(s)`)

  return charactersEvents
}
