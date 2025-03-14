import { notifyTelegramSubscribers } from "../bot/telegram/telegram"
import { handleCharactersUpdates } from "../character/characterUpdate"
import { CharacterRequestSchema } from "../types/character"
import type { Character } from "../types/character"
import logger from "../utils/logger"
import cors from "cors"
import express, { Router } from "express"
import type { Application } from "express"
import { ZodError } from "zod"

export const router = Router()

router.get("/", (_, res) => {
  res.json({ message: "Hey! Send something via POST `/character`" })
})

router.post("/character", async (req, res) => {
  try {
    const characterRequest = CharacterRequestSchema.parse(req.body)
    logger.info(
      `Received POST /character for ${characterRequest.version}-${characterRequest.region}: ${Object.keys(
        characterRequest.realms,
      )
        .map((realm) => `${realm} (${Object.keys(characterRequest.realms[realm]).length})`)
        .join(", ")}`,
    )
    const characters: Character[] = []
    for (const [realm, realmCharacters] of Object.entries(characterRequest.realms)) {
      for (const [name, character] of Object.entries(realmCharacters)) {
        characters.push({
          version: characterRequest.version,
          region: characterRequest.region,
          realm: realm,
          name: name,
          class: character.class,
          level: character.level,
          zone: character.zone,
          online: character.online,
          died_at: character.died_at ? new Date(character.died_at * 1000).toISOString() : null,
        })
      }
    }
    // const charactersEvents = await handleCharactersUpdates(characters, [notifyTelegramSubscribers])
    const charactersFull = await handleCharactersUpdates(characters, [notifyTelegramSubscribers])
    res.json({
      success: true,
      // data: { level_ups: charactersEvents.level_ups.length, deaths: charactersEvents.deaths.length },
      data: { message: `Updated ${charactersFull.length} character(s)` },
    })
  } catch (error) {
    if (error instanceof ZodError) {
      res.status(400).json({
        message: "Invalid request data",
        errors: error.issues,
      })
    } else {
      res.status(500).json({ message: "Server error", error })
    }
  }
})

export function createServer(): Application {
  const app: Application = express()

  app.use(express.json())
  app.use(cors())

  app.use(router)

  return app
}

export function startServer(app: Application) {
  return app.listen(8000, () => {
    logger.info("Server started on http://localhost:8000")
  })
}
