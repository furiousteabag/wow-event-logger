import type { Database } from "./db"
import { z } from "zod"

export type Character = Database["public"]["Tables"]["character"]["Insert"]
export type CharacterFull = Database["public"]["Tables"]["character"]["Row"]

export type CharactersEvents = {
  level_ups: CharacterFull[]
  deaths: CharacterFull[]
}

export function normalizeString(str: string): string {
  return str.trim().toLowerCase().replace(/\s+/g, "-")
}

const characterClassEnum = z.preprocess(
  (val) => {
    if (typeof val !== "string") return val
    return normalizeString(val)
  },
  z.enum([
    "death-knight",
    "demon-hunter",
    "druid",
    "evoker",
    "hunter",
    "mage",
    "monk",
    "paladin",
    "priest",
    "rogue",
    "shaman",
    "warlock",
    "warrior",
  ]) satisfies z.ZodType<Database["public"]["Enums"]["character_class"]>,
)

export const gameRegionEnum = z.preprocess(
  (val) => {
    if (typeof val !== "string") return val
    return normalizeString(val)
  },
  z.enum(["us", "eu", "kr", "tw", "cn"]) satisfies z.ZodType<Database["public"]["Enums"]["game_region"]>,
)

export const gameVersionEnum = z.preprocess(
  (val) => {
    if (typeof val !== "string") return val
    return normalizeString(val)
  },
  z.enum(["classic", "tbc-classic", "wrath-classic", "cata-classic", "retail"]) satisfies z.ZodType<
    Database["public"]["Enums"]["game_version"]
  >,
)

export const CharacterSchema = z.object({
  class: characterClassEnum.nullable().optional(),
  level: z.number().optional(),
  zone: z.string().optional(),
  online: z.boolean().optional(),
  died_at: z.number().optional(),
})

export const CharacterRequestSchema = z.object({
  region: gameRegionEnum,
  version: gameVersionEnum,
  realms: z.record(z.record(CharacterSchema)),
})

export const CharacterTelegramSchema = z.object({
  version: gameVersionEnum,
  region: gameRegionEnum,
  realm: z
    .string()
    .min(2, "Realm name must be at least 2 characters")
    .transform((s) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()),
  name: z
    .string()
    .min(2, "Character name must be at least 2 characters")
    .transform((s) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()),
})
