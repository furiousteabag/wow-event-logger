from enum import Enum
from typing import Dict, Optional, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CharacterClass(str, Enum):
    DEATH_KNIGHT = "death_knight"
    DEMON_HUNTER = "demon_hunter"
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
    realm: str
    name: str
    level: int
    class_: CharacterClass = Field(alias="class")
    online: bool = False
    zone: str

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        json_schema_extra={
            "examples": [
                {
                    "realm": "silvermoon",
                    "name": "Thrall",
                    "level": 70,
                    "class_": "warrior",
                    "online": True,
                    "zone": "Orgrimmar",
                }
            ]
        },
    )


class CharacterCreate(CharacterBase):
    pass


class Character(CharacterBase):
    model_config = ConfigDict(use_attribute_docstrings=True, from_attributes=True)


class CharacterUpdate(BaseModel):
    level: Optional[int] = None
    online: Optional[bool] = None
    zone: Optional[str] = None

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        json_schema_extra={"examples": [{"level": 70, "online": False, "zone": "Stormwind"}]},
    )


class CharacterEventData(BaseModel):
    online: bool
    level: int
    class_: CharacterClass = Field(alias="class")
    zone: str

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"online": True, "level": 23, "class": "warrior", "zone": "Thunder Bluff"}},
    )

    @field_validator("class_", mode="before")
    @classmethod
    def transform_class(cls, value: str) -> str:
        return value.lower().replace(" ", "_")


class WatchlistData(BaseModel):
    watchlist: Dict[str, CharacterEventData]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "watchlist": {"Furioustea": {"online": True, "level": 23, "class": "warrior", "zone": "Thunder Bluff"}}
            }
        }
    )


class EventWatcherRequest(BaseModel):
    realms: Dict[str, WatchlistData]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "realms": {
                    "Doomhowl": {
                        "watchlist": {
                            "Furioustea": {"online": True, "level": 23, "class": "warrior", "zone": "Thunder Bluff"}
                        }
                    }
                }
            }
        }
    )


# class CharacterDefinition(TypedDict):
#     realm: str
#     name: str
