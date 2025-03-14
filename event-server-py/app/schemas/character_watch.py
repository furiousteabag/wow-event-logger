from pydantic import BaseModel, ConfigDict


# Character Watch schema
class CharacterWatchBase(BaseModel):
    chat_id: int
    character_id: str

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        use_enum_values=True,
        json_schema_extra={
            "examples": [{"chat_id": 123456789, "character_id": "123e4567-e89b-12d3-a456-426614174000"}]
        },
    )


class CharacterWatchCreate(CharacterWatchBase):
    pass


class CharacterWatch(CharacterWatchBase):
    id: str

    model_config = ConfigDict(use_attribute_docstrings=True, from_attributes=True)
