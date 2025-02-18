from enum import Enum
from typing import Optional, TypedDict

from pydantic import BaseModel, ConfigDict, Field


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


# class CharacterDefinition(TypedDict):
#     realm: str
#     name: str
