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


def format_character(character: Character, include_realm: bool = True) -> str:
    name = character.name
    formatted_name = f"*{name}*"

    class_emoji = class_emojis.get(character.class_, "🎮") if character.class_ else "🎮"
    display_class = character.class_.replace("_", " ").title() if character.class_ else ""
    zone_info = f"📍{character.zone}" if character.zone else ""
    status = "🟢Online" if character.online else "⭕Offline"
    death_info = ""
    if hasattr(character, "died_at") and character.died_at:
        death_date = character.died_at.strftime("%Y\\-%m\\-%d")
        death_info = f" 💀{death_date}"

    char_str = f"{class_emoji}{character.level if character.level else '??'} {formatted_name} {zone_info}{death_info}"

    if include_realm:
        char_str += f" 🌍{character.realm.title()}"
    return char_str
