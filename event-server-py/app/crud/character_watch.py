from supabase.client import AsyncClient

from app.crud.base import CRUDBase
from app.schemas.character import GameRegion, GameVersion
from app.schemas.character_watch import CharacterWatch, CharacterWatchCreate


class CRUDCharacterWatch(CRUDBase[CharacterWatch, CharacterWatchCreate, CharacterWatchCreate]):

    async def create(self, db: AsyncClient, *, obj_in: CharacterWatchCreate) -> CharacterWatch:
        """Create a new character watch entry"""
        data, _ = await db.table(self.table_name).insert(obj_in.model_dump()).execute()
        _, created = data
        return self.model(**created[0])

    async def get_by_id(self, db: AsyncClient, *, id: str) -> CharacterWatch | None:
        """Get watch by id"""
        data, _ = await db.table(self.table_name).select("*").eq("id", id).execute()
        _, got = data
        if not got:
            return None
        return self.model(**got[0])

    async def delete_by_id(self, db: AsyncClient, *, id: str) -> CharacterWatch | None:
        """Delete a character watch entry by id"""
        data, _ = await db.table(self.table_name).delete().eq("id", id).execute()
        _, deleted = data
        if not deleted:
            return None
        return self.model(**deleted[0])

    async def delete_by_character_id(self, db: AsyncClient, *, character_id: str) -> list[CharacterWatch]:
        """Delete all watches for a specific character"""
        data, _ = await db.table(self.table_name).delete().eq("character_id", character_id).execute()
        _, deleted = data
        return [self.model(**item) for item in deleted]

    async def delete_by_chat_and_character(
        self, db: AsyncClient, *, chat_id: int, character_id: str
    ) -> CharacterWatch | None:
        """Delete a character watch entry by chat_id and character_id"""
        data, _ = (
            await db.table(self.table_name).delete().eq("chat_id", chat_id).eq("character_id", character_id).execute()
        )
        _, deleted = data
        if not deleted:
            return None
        return self.model(**deleted[0])

    async def delete_by_chat(self, db: AsyncClient, *, chat_id: int) -> list[CharacterWatch]:
        """Delete all character watches for a specific chat"""
        data, _ = await db.table(self.table_name).delete().eq("chat_id", chat_id).execute()
        _, deleted = data
        return [self.model(**item) for item in deleted]

    async def get_by_chat(self, db: AsyncClient, *, chat_id: int) -> list[CharacterWatch]:
        """Get all character watches for a specific chat"""
        data, _ = await db.table(self.table_name).select("*").eq("chat_id", chat_id).execute()
        _, got = data
        return [self.model(**item) for item in got]

    async def get_by_character_id(self, db: AsyncClient, *, character_id: str) -> list[CharacterWatch]:
        """Get all watches for a specific character"""
        data, _ = await db.table(self.table_name).select("*").eq("character_id", character_id).execute()
        _, got = data
        return [self.model(**item) for item in got]

    async def exists(self, db: AsyncClient, *, chat_id: int, character_id: str) -> bool:
        """Check if a watch entry exists"""
        data, _ = (
            await db.table(self.table_name)
            .select("*")
            .eq("chat_id", chat_id)
            .eq("character_id", character_id)
            .execute()
        )
        _, got = data
        return len(got) > 0

    async def get_by_chat_and_character(
        self, db: AsyncClient, *, chat_id: int, character_id: str
    ) -> CharacterWatch | None:
        """Get a watch entry by chat_id and character_id"""
        data, _ = (
            await db.table(self.table_name)
            .select("*")
            .eq("chat_id", chat_id)
            .eq("character_id", character_id)
            .execute()
        )
        _, got = data
        if not got:
            return None
        return self.model(**got[0])

    async def get_all(self, db: AsyncClient) -> list[CharacterWatch]:
        """Get all watch entries"""
        data, _ = await db.table(self.table_name).select("*").execute()
        _, got = data
        return [self.model(**item) for item in got]


crud_character_watch = CRUDCharacterWatch(CharacterWatch, "character_watch_chat_telegram")
