from datetime import datetime
from enum import Enum
from typing import Annotated, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GameVersion(str, Enum):
    CLASSIC = "classic"
    TBC_CLASSIC = "tbc-classic"
    WRATH_CLASSIC = "wrath-classic"
    CATA_CLASSIC = "cata-classic"
    RETAIL = "retail"


class GameRegion(str, Enum):
    US = "us"
    EU = "eu"
    KR = "kr"
    TW = "tw"
    CN = "cn"


class CharacterClass(str, Enum):
    DEATH_KNIGHT = "death-knight"
    DEMON_HUNTER = "demon-hunter"
    DRUID = "druid"
    EVOKER = "evoker"
    HUNTER = "hunter"
    MAGE = "mage"
    MONK = "monk"
    PALADIN = "paladin"
    PRIEST = "priest"
    ROGUE = "rogue"
    SHAMAN = "shaman"
    WARLOCK = "warlock"
    WARRIOR = "warrior"


class CharacterBase(BaseModel):
    version: GameVersion
    region: GameRegion
    realm: str
    name: str
    class_: Optional[Annotated[CharacterClass, Field(alias="class")]] = None
    level: Optional[int] = None
    zone: Optional[str] = None
    online: Optional[bool] = None
    died_at: Optional[datetime] = None

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        use_enum_values=True,
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "realm": "silvermoon",
                    "name": "Thrall",
                    "level": 70,
                    "class_": "warrior",
                    "online": True,
                    "zone": "Orgrimmar",
                    "version": "classic",
                    "region": "us",
                }
            ]
        },
    )


class CharacterCreate(CharacterBase):
    died_at: Optional[int] = None


class Character(CharacterBase):
    id: str

    model_config = ConfigDict(use_attribute_docstrings=True, from_attributes=True)


class CharacterUpdate(BaseModel):
    level: Optional[int] = None
    zone: Optional[str] = None
    online: Optional[bool] = None
    died_at: Optional[int] = None

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        json_schema_extra={"examples": [{"level": 70, "online": False, "zone": "Stormwind"}]},
    )


class CharacterEventData(BaseModel):
    class_: Optional[CharacterClass] = Field(alias="class", default=None)
    level: Optional[int] = None
    zone: Optional[str] = None
    online: Optional[bool] = None
    died_at: Optional[int] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"online": True, "level": 23, "class": "warrior", "zone": "Thunder Bluff"}},
    )

    @field_validator("class_", mode="before")
    @classmethod
    def transform_class(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value.lower().replace(" ", "-")
        # Handle cases where the value might be the enum itself
        return value


class EventWatcherRequest(BaseModel):
    region: GameRegion
    version: GameVersion
    realms: Dict[str, Dict[str, CharacterEventData]]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "region": "us",
                "version": "classic",
                "realms": {
                    "Doomhowl": {
                        "Furioustea": {"online": True, "level": 23, "class": "warrior", "zone": "Thunder Bluff"}
                    }
                },
            }
        },
    )
