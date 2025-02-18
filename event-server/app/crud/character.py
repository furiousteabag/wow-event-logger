from supabase.client import AsyncClient

from app.crud.base import CRUDBase
from app.schemas.character import Character, CharacterCreate, CharacterUpdate


class CRUDCharacter(CRUDBase[Character, CharacterCreate, CharacterUpdate]):
    async def create(self, db: AsyncClient, *, obj_in: CharacterCreate) -> Character:
        # Convert class_ to class in the data sent to DB
        db_data = obj_in.model_dump(by_alias=True)  # This will use "class" instead of "class_"
        data, _ = await db.table(self.table_name).insert(db_data).execute()
        _, created = data
        created[0] = self.convert_datetime_to_int(created[0])
        return self.model(**created[0])

    async def get(self, db: AsyncClient, *, realm: str, name: str) -> Character | None:
        """Get character by realm and name"""
        data, _ = await db.table(self.table_name).select("*").eq("realm", realm).eq("name", name).execute()
        _, got = data
        if not got:
            return None
        return self.model(**got[0])

    async def update(self, db: AsyncClient, *, realm: str, name: str, obj_in: CharacterUpdate) -> Character | None:
        db_data = obj_in.model_dump(exclude_unset=True, by_alias=True)
        data, _ = await db.table(self.table_name).update(db_data).eq("realm", realm).eq("name", name).execute()
        _, updated = data
        if not updated:
            return None
        return self.model(**updated[0])

    async def delete(self, db: AsyncClient, *, realm: str, name: str) -> Character | None:
        """Delete character by realm and name"""
        data, _ = await db.table(self.table_name).delete().eq("realm", realm).eq("name", name).execute()
        _, deleted = data
        if not deleted:
            return None
        return self.model(**deleted[0])

    async def get_all(self, db: AsyncClient) -> list[Character]:
        return await super().get_all(db)

    async def get_by_realm(self, db: AsyncClient, *, realm: str) -> list[Character]:
        """Get all characters in a realm"""
        data, _ = await db.table(self.table_name).select("*").eq("realm", realm).execute()
        _, got = data
        return [self.model(**item) for item in got]

    async def get_online(self, db: AsyncClient) -> list[Character]:
        """Get all online characters"""
        data, _ = await db.table(self.table_name).select("*").eq("online", True).execute()
        _, got = data
        return [self.model(**item) for item in got]


crud_character = CRUDCharacter(Character, "character")
