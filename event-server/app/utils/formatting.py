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


def format_character(character: Character | CharacterWatch) -> str:
    char_str = f"*{character.name}*"
    if isinstance(character, CharacterBase):
        status = "🟢Online" if character.online else "⭕Offline"
        class_emoji = class_emojis.get(character.class_, "🎮")
        zone_info = f"📍{character.zone}" if character.zone else ""
        display_class = character.class_.value.replace("_", " ").title()
        death_info = ""
        if hasattr(character, "died_at") and character.died_at:
            death_date = character.died_at.strftime("%Y\\-%m\\-%d")
            death_info = f" \\| 💀{death_date}"
        char_str += f" \\| {character.level} {class_emoji} {display_class} \\|{zone_info}{death_info}"
    char_str += f" \\| 🌍{character.realm.title()}"
    return char_str
