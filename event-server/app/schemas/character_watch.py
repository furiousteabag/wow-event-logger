from pydantic import BaseModel, ConfigDict


class CharacterWatchBase(BaseModel):
    chat_id: int
    realm: str
    name: str

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        json_schema_extra={"examples": [{"chat_id": 123456789, "realm": "silvermoon", "name": "Thrall"}]},
    )


class CharacterWatchCreate(CharacterWatchBase):
    pass


class CharacterWatch(CharacterWatchBase):
    model_config = ConfigDict(use_attribute_docstrings=True, from_attributes=True)
