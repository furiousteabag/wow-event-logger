from supabase.client import AsyncClient

from app.crud.base import CRUDBase
from app.schemas.character_watch import CharacterWatch, CharacterWatchCreate


class CRUDCharacterWatch(CRUDBase[CharacterWatch, CharacterWatchCreate, CharacterWatchCreate]):
    async def create(self, db: AsyncClient, *, obj_in: CharacterWatchCreate) -> CharacterWatch:
        """Create a new character watch entry"""
        data, count = await db.table(self.table_name).insert(obj_in.model_dump()).execute()
        _, created = data
        return self.model(**created[0])

    async def delete(self, db: AsyncClient, *, chat_id: int, realm: str, name: str) -> CharacterWatch | None:
        """Delete a character watch entry by chat_id, realm and name"""
        data, count = (
            await db.table(self.table_name)
            .delete()
            .eq("chat_id", chat_id)
            .eq("realm", realm)
            .eq("name", name)
            .execute()
        )
        _, deleted = data
        if not deleted:
            return None
        return self.model(**deleted[0])

    async def get_by_chat(self, db: AsyncClient, *, chat_id: int) -> list[CharacterWatch]:
        """Get all character watches for a specific chat"""
        data, count = await db.table(self.table_name).select("*").eq("chat_id", chat_id).execute()
        _, got = data
        return [self.model(**item) for item in got]

    async def get_by_character(self, db: AsyncClient, *, realm: str, name: str) -> list[CharacterWatch]:
        """Get all watches for a specific character"""
        data, count = await db.table(self.table_name).select("*").eq("realm", realm).eq("name", name).execute()
        _, got = data
        return [self.model(**item) for item in got]

    async def exists(self, db: AsyncClient, *, chat_id: int, realm: str, name: str) -> bool:
        """Check if a watch entry exists"""
        data, count = (
            await db.table(self.table_name)
            .select("*")
            .eq("chat_id", chat_id)
            .eq("realm", realm)
            .eq("name", name)
            .execute()
        )
        _, got = data
        return len(got) > 0


crud_character_watch = CRUDCharacterWatch(CharacterWatch, "character_watch_chat_telegram")
