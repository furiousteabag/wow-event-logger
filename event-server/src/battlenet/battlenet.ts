import { type Character, normalizeString } from "../types/character"
import type { Database } from "../types/db"
import logger from "../utils/logger"
import { characterProfileSummary } from "@blizzard-api/classic-wow"
import { createBlizzardApiClient } from "@blizzard-api/client"
import { HTTPError } from "ky"

if (!process.env.BATTLENET_CLIENT_ID || !process.env.BATTLENET_CLIENT_SECRET) {
  throw new Error("Missing BATTLENET_CLIENT_ID or BATTLENET_CLIENT_SECRET in environment")
}

const battlenetClient = await createBlizzardApiClient({
  key: process.env.BATTLENET_CLIENT_ID,
  secret: process.env.BATTLENET_CLIENT_SECRET,
  origin: "us",
})

export async function populateCharacter(character: Character): Promise<Character> {
  // const namespace = character.version === "retail" ? "profile" : "profile-classic1x"
  const namespace = "profile-classic1x"
  try {
    const characterResponse = await battlenetClient.sendRequest(
      characterProfileSummary(namespace, character.realm.toLowerCase(), character.name.toLowerCase()),
      {
        origin: character.region,
      },
    )
    const updatedCharacter: Character = {
      ...character,
      class: normalizeString(characterResponse.character_class.name) as Database["public"]["Enums"]["character_class"],
      level: characterResponse.level,
    }
    if (characterResponse.is_ghost) {
      updatedCharacter.died_at = new Date(characterResponse.last_login_timestamp).toISOString()
    }
    return updatedCharacter
  } catch (error) {
    if (error instanceof HTTPError) {
      logger.error(`Error fetching character data: ${error.message}`)
    } else {
      logger.error(`Error fetching character data: ${error}`)
    }
    return character
  }
}
