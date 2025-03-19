import type { Character } from "../types/character"
import type { Database } from "../types/db"

type CharacterClass = Database["public"]["Enums"]["character_class"]

const classEmojis: Record<CharacterClass, string> = {
  warrior: "⚔️",
  paladin: "🔨",
  hunter: "🏹",
  rogue: "🗡️",
  priest: "✨",
  "death-knight": "❄️",
  shaman: "⚡",
  mage: "🔮",
  warlock: "😈",
  monk: "🐼",
  druid: "🍃",
  "demon-hunter": "👁️",
  evoker: "🐲",
}

export function formatCharacter(character: Character, includeRealm = true): string {
  let formattedName = `*${character.name}*`
  if (character.version === "classic" && character.level && character.level >= 10) {
    // formattedName = `[${formattedName}](https://era.raider.io/characters/${character.region}/${character.realm}/${character.name})`
    formattedName = `[${formattedName}](https://classicwowarmory.com/character/${character.region}/${character.realm}/${character.name})`
  }
  const classEmoji = character.class ? classEmojis[character.class] || "🎮" : "🎮"
  const zoneInfo = character.zone ? `📍${character.zone}` : ""
  // const status = character.online ? "🟢Online" : "⭕Offline"
  let deathInfo = ""
  if (character.died_at) {
    const deathDate = new Date(character.died_at).toISOString().split("T")[0].replace(/-/g, "\\-")
    deathInfo = ` 💀${deathDate}`
  }
  let charStr = `${classEmoji}${character.level || "??"} ${formattedName} ${zoneInfo}${deathInfo}`
  if (includeRealm) {
    charStr += ` 🌍${character.realm.charAt(0).toUpperCase() + character.realm.slice(1)}`
  }
  return charStr
}
