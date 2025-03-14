import { createServer, startServer } from "./api/server"
import { startTelegramBot } from "./bot/telegram/telegram"
import { startWatchedCharacterUpdateScheduler } from "./scheduler/scheduler"

const app = createServer()

startTelegramBot()
startWatchedCharacterUpdateScheduler(1)
startServer(app)
