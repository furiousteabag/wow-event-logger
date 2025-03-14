import { createServer, startServer } from "./api/server"
import { populateCharacter } from "./battlenet/battlenet"
import { notifyTelegramSubscribers } from "./bot/telegram/telegram"
import { handleCharactersUpdates } from "./character/characterUpdate"
import { startWatchedCharacterUpdateScheduler } from "./scheduler/scheduler"
import type { Character } from "./types/character"
import logger from "./utils/logger"

let character: Character = {
  version: "classic",
  region: "us",
  realm: "Doomhowl",
  name: "Furiousuncle",
}
character = await populateCharacter(character)
logger.info(`Character data: ${JSON.stringify(character)}`)
await handleCharactersUpdates([character], [notifyTelegramSubscribers])

startWatchedCharacterUpdateScheduler(1)

const app = createServer()
startServer(app)
