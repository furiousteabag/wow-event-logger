from typing import Optional

from supabase.client import AsyncClient

from app.crud.base import CRUDBase
from app.schemas.character import Character, CharacterCreate, CharacterUpdate, GameRegion, GameVersion


class CRUDCharacter(CRUDBase[Character, CharacterCreate, CharacterUpdate]):
    async def create(self, db: AsyncClient, *, obj_in: CharacterCreate) -> Character:
        # Convert class_ to class in the data sent to DB
        db_data = obj_in.model_dump(by_alias=True, exclude_unset=True)
        db_data = self.convert_timestamp_to_datetime(db_data)
        if "class_" in db_data:
            db_data["class"] = db_data.pop("class_")
        data, _ = await db.table(self.table_name).insert(db_data).execute()
        _, created = data
        if "class" in created[0]:
            created[0]["class_"] = created[0].pop("class")
        return self.model(**created[0])

    async def get_by_id(self, db: AsyncClient, *, id: str) -> Character | None:
        """Get character by id"""
        data, _ = await db.table(self.table_name).select("*").eq("id", id).execute()
        _, got = data
        if not got:
            return None
        if "class" in got[0]:
            got[0]["class_"] = got[0].pop("class")
        return self.model(**got[0])

    async def get(
        self,
        db: AsyncClient,
        *,
        version: GameVersion,
        region: GameRegion,
        realm: str,
        name: str,
    ) -> Character | None:
        """Get character by realm, name, version and region"""
        data, _ = (
            await db.table(self.table_name)
            .select("*")
            .eq("version", version.value if type(version) == GameVersion else version)
            .eq("region", region.value if type(region) == GameRegion else region)
            .eq("realm", realm)
            .eq("name", name)
            .execute()
        )
        _, got = data
        if not got:
            return None
        if "class" in got[0]:
            got[0]["class_"] = got[0].pop("class")
        return self.model(**got[0])

    async def update_by_id(self, db: AsyncClient, *, id: str, obj_in: CharacterUpdate) -> Character | None:
        """Update character by id"""
        db_data = obj_in.model_dump(exclude_unset=True, by_alias=True)
        db_data = self.convert_timestamp_to_datetime(db_data)
        if "class_" in db_data:
            db_data["class"] = db_data.pop("class_")
        data, _ = await db.table(self.table_name).update(db_data).eq("id", id).execute()
        _, updated = data
        if not updated:
            return None
        if "class" in updated[0]:
            updated[0]["class_"] = updated[0].pop("class")
        return self.model(**updated[0])

    async def update(
        self,
        db: AsyncClient,
        *,
        version: GameVersion,
        region: GameRegion,
        realm: str,
        name: str,
        obj_in: CharacterUpdate,
    ) -> Character | None:
        """Update character by realm, name, version and region"""
        db_data = obj_in.model_dump(exclude_unset=True, by_alias=True)
        db_data = self.convert_timestamp_to_datetime(db_data)
        if "class_" in db_data:
            db_data["class"] = db_data.pop("class_")
        data, _ = (
            await db.table(self.table_name)
            .update(db_data)
            .eq("version", version.value if type(version) == GameVersion else version)
            .eq("region", region.value if type(region) == GameRegion else region)
            .eq("realm", realm)
            .eq("name", name)
            .execute()
        )
        _, updated = data
        if not updated:
            return None
        if "class" in updated[0]:
            updated[0]["class_"] = updated[0].pop("class")
        return self.model(**updated[0])

    async def delete_by_id(self, db: AsyncClient, *, id: str) -> Character | None:
        """Delete character by id"""
        data, _ = await db.table(self.table_name).delete().eq("id", id).execute()
        _, deleted = data
        if not deleted:
            return None
        if "class" in deleted[0]:
            deleted[0]["class_"] = deleted[0].pop("class")
        return self.model(**deleted[0])

    async def delete(
        self,
        db: AsyncClient,
        *,
        version: GameVersion,
        region: GameRegion,
        realm: str,
        name: str,
    ) -> Character | None:
        """Delete character by realm, name, version and region"""
        data, _ = (
            await db.table(self.table_name)
            .delete()
            .eq("version", version.value if type(version) == GameVersion else version)
            .eq("region", region.value if type(region) == GameRegion else region)
            .eq("realm", realm)
            .eq("name", name)
            .execute()
        )
        _, deleted = data
        if not deleted:
            return None
        if "class" in deleted[0]:
            deleted[0]["class_"] = deleted[0].pop("class")
        return self.model(**deleted[0])

    async def get_all(self, db: AsyncClient) -> list[Character]:
        return await super().get_all(db)

    async def get_by_realm(
        self,
        db: AsyncClient,
        *,
        version: GameVersion,
        region: GameRegion,
        realm: str,
    ) -> list[Character]:
        """Get all characters in a realm"""
        data, _ = (
            await db.table(self.table_name)
            .select("*")
            .eq("version", version.value if type(version) == GameVersion else version)
            .eq("region", region.value if type(region) == GameRegion else region)
            .eq("realm", realm)
            .execute()
        )
        _, got = data
        for item in got:
            if "class" in item:
                item["class_"] = item.pop("class")
        return [self.model(**item) for item in got]

    async def get_online(
        self, db: AsyncClient, version: Optional[GameVersion] = None, region: Optional[GameRegion] = None
    ) -> list[Character]:
        """Get all online characters"""
        query = db.table(self.table_name).select("*").eq("online", True)

        if version:
            query = query.eq("version", version.value if type(version) == GameVersion else version)
        if region:
            query = query.eq("region", region.value if type(region) == GameRegion else region)

        data, _ = await query.execute()
        _, got = data
        for item in got:
            if "class" in item:
                item["class_"] = item.pop("class")
        return [self.model(**item) for item in got]


crud_character = CRUDCharacter(Character, "character")
