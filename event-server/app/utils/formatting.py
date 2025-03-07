from app.schemas.character import Character, CharacterBase, CharacterClass
from app.schemas.character_watch import CharacterWatch

class_emojis: dict[CharacterClass, str] = {
    CharacterClass.WARRIOR: "⚔️",
    CharacterClass.PALADIN: "🔨",
    CharacterClass.HUNTER: "🏹",
    CharacterClass.ROGUE: "🗡️",
    CharacterClass.PRIEST: "✨",
    CharacterClass.DEATH_KNIGHT: "❄️",
    CharacterClass.SHAMAN: "⚡",
    CharacterClass.MAGE: "🔮",
    CharacterClass.WARLOCK: "😈",
    CharacterClass.MONK: "🐼",
    CharacterClass.DRUID: "🍃",
    CharacterClass.DEMON_HUNTER: "👁️",
    CharacterClass.EVOKER: "🐲",
}


def format_character(character: Character | CharacterWatch, include_realm: bool = True) -> str:
    name = character.name
    formatted_name = f"*{name}*"

    if isinstance(character, CharacterBase):
        class_emoji = class_emojis.get(character.class_, "🎮")
        display_class = character.class_.value.replace("_", " ").title()
        zone_info = f"📍{character.zone}" if character.zone else ""
        status = "🟢Online" if character.online else "⭕Offline"
        death_info = ""
        if hasattr(character, "died_at") and character.died_at:
            death_date = character.died_at.strftime("%Y\\-%m\\-%d")
            death_info = f" 💀{death_date}"

        char_str = f"{class_emoji}{character.level} {formatted_name} {zone_info}{death_info}"
    else:
        char_str = f"🎮 ? {formatted_name}"

    if include_realm:
        char_str += f" 🌍{character.realm.title()}"
    return char_str
