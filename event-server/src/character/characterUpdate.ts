import { supabase } from "../supabase/client"
import type { Character, CharacterFull, CharactersEvents } from "../types/character"
import logger from "../utils/logger"

export async function handleCharactersUpdates(
  characters: Character[],
  notifySubscribers: ((events: CharactersEvents) => Promise<void>)[],
): Promise<CharacterFull[]> {
  logger.info(`Handling updates for ${characters.length} character(s)...`)

  const charactersEvents: CharactersEvents = {
    level_ups: [],
    deaths: [],
  }

  const updatedCharacters: CharacterFull[] = []

  const processCharacter = async (character: Character): Promise<CharacterFull | null> => {
    try {
      // Find existing character
      const { data: existingChar } = await supabase
        .from("character")
        .select("*")
        .eq("version", character.version)
        .eq("region", character.region)
        .eq("realm", character.realm)
        .eq("name", character.name)
        .maybeSingle()

      let updatedChar: CharacterFull

      if (existingChar) {
        if (existingChar.name === "Furiousbars") {
          console.log(existingChar)
          console.log(character)
        }

        // Skip updates that would decrease level (likely an error)
        if (existingChar.level && character.level && existingChar.level > character.level) {
          return existingChar
        }

        let died_at = null
        if (character.died_at && existingChar.died_at) {
          died_at = existingChar.died_at
        } else if (character.died_at && !existingChar.died_at) {
          died_at = character.died_at
        } else if (!character.died_at && existingChar.died_at) {
          // resurrection if person is restarted and achieved higher level
          if (existingChar.level && character.level && existingChar.level < character.level) {
            died_at = null
          } else {
            died_at = existingChar.died_at
          }
        } else {
          died_at = null
        }

        // Update the character
        const { data: updated, error: updateError } = await supabase
          .from("character")
          .update({
            level: character.level ?? existingChar.level,
            online: character.online ?? existingChar.online,
            zone: character.zone ?? existingChar.zone,
            died_at: died_at,
          })
          .eq("id", existingChar.id)
          .select("*")
          .single()
        if (updateError) throw updateError

        updatedChar = updated

        const characterDied = !existingChar.died_at && character.died_at
        const leveledUp =
          (existingChar.level && character.level && existingChar.level < character.level) ||
          (!existingChar.level && character.level)

        if (characterDied) {
          charactersEvents.deaths.push(updatedChar)
        } else if (leveledUp) {
          charactersEvents.level_ups.push(updatedChar)
        }
      } else {
        // Create new character
        const { data: newChar, error: insertError } = await supabase
          .from("character")
          .insert(character)
          .select("*")
          .single()
        if (insertError) throw insertError

        updatedChar = newChar

        if (character.died_at) {
          charactersEvents.deaths.push(updatedChar)
        } else if (character.level) {
          charactersEvents.level_ups.push(updatedChar)
        }
      }

      return updatedChar
    } catch (error) {
      logger.error(`Error processing character ${character.name}:`, error)
      return null
    }
  }

  const tasks = characters.map((character) => processCharacter(character))
  const results = await Promise.all(tasks)
  updatedCharacters.push(...(results.filter(Boolean) as CharacterFull[]))

  const hasEvents = charactersEvents.level_ups.length > 0 || charactersEvents.deaths.length > 0
  if (hasEvents && notifySubscribers.length > 0) {
    await Promise.all(notifySubscribers.map((notify) => notify(charactersEvents)))
  }

  logger.info(
    `Processed ${characters.length} character(s): ${charactersEvents.level_ups.length} level ups, ${charactersEvents.deaths.length} deaths`,
  )

  return updatedCharacters
}
