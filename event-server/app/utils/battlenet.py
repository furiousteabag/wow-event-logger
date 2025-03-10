import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

import aiohttp
from loguru import logger
from pydantic import BaseModel, HttpUrl

from app.schemas.character import Character, CharacterBase, CharacterClass, GameRegion, GameVersion


class Namespace(str, Enum):
    PROFILE = "profile"
    PROFILE_CLASSIC = "profile-classic"
    PROFILE_CLASSIC1X = "profile-classic1x"


namespace_map: dict[GameVersion, Namespace] = {
    GameVersion.RETAIL: Namespace.PROFILE,
    GameVersion.CLASSIC: Namespace.PROFILE_CLASSIC1X,
    GameVersion.TBC_CLASSIC: Namespace.PROFILE_CLASSIC,
    GameVersion.WRATH_CLASSIC: Namespace.PROFILE_CLASSIC,
    GameVersion.CATA_CLASSIC: Namespace.PROFILE_CLASSIC,
}


class LocalizedString(BaseModel):
    """
    Model for localized strings that can come in two formats:
    1. A simple string value
    2. A dictionary with language codes as keys
    """

    en_US: Optional[str] = None
    es_MX: Optional[str] = None
    pt_BR: Optional[str] = None
    de_DE: Optional[str] = None
    en_GB: Optional[str] = None
    es_ES: Optional[str] = None
    fr_FR: Optional[str] = None
    it_IT: Optional[str] = None
    ru_RU: Optional[str] = None
    ko_KR: Optional[str] = None
    zh_TW: Optional[str] = None
    zh_CN: Optional[str] = None

    # For when the API returns just a string instead of a dictionary
    _plain_value: Optional[str] = None

    @classmethod
    def __get_validators__(cls):
        yield cls.model_validate

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        """Custom validation to handle both string and dictionary formats"""
        if isinstance(obj, str):
            return cls(_plain_value=obj)
        return super().model_validate(obj, *args, **kwargs)

    def __str__(self):
        """Return the English version if available, otherwise the plain value"""
        if self.en_US:
            return self.en_US
        if self._plain_value:
            return self._plain_value
        return "Unknown"

    def get_text(self) -> str:
        """Get the string representation, prioritizing English"""
        return str(self)


class Link(BaseModel):
    href: HttpUrl


class Links(BaseModel):
    self: Link


class KeyModel(BaseModel):
    href: HttpUrl


class SlugModel(BaseModel):
    slug: str


class NamedRef(BaseModel):
    key: KeyModel
    name: Union[str, LocalizedString]
    id: int

    def get_name(self) -> str:
        """Get the name as a string, handling both string and LocalizedString objects"""
        if isinstance(self.name, str):
            return self.name
        return str(self.name)


class NamedRefWithSlug(NamedRef):
    slug: str


class TypedName(BaseModel):
    type: str
    name: Union[str, LocalizedString]

    def get_name(self) -> str:
        """Get the name as a string, handling both string and LocalizedString objects"""
        if isinstance(self.name, str):
            return self.name
        return str(self.name)


class PlayableClassRef(BaseModel):
    key: KeyModel
    id: int


class PlayableRaceRef(BaseModel):
    key: KeyModel
    id: int


class GuildMemberCharacter(BaseModel):
    key: KeyModel
    name: str
    id: int
    level: int
    playable_class: PlayableClassRef
    playable_race: PlayableRaceRef
    realm: SlugModel


class GuildMember(BaseModel):
    character: GuildMemberCharacter
    rank: int


class GuildRef(BaseModel):
    key: KeyModel
    name: str
    id: int
    realm: NamedRefWithSlug
    faction: TypedName


class GuildRoster(BaseModel):
    _links: Links
    guild: GuildRef
    members: List[GuildMember]


class ResourceHref(BaseModel):
    href: HttpUrl


class CharacterProfile(BaseModel):
    _links: Links
    id: int
    name: str
    gender: TypedName
    faction: TypedName
    race: NamedRef
    character_class: NamedRef
    active_spec: Optional[Dict[str, Any]] = None  # Changed to Dict to be more flexible
    realm: NamedRefWithSlug
    guild: Optional[GuildRef] = None
    level: int
    experience: int
    titles: Optional[ResourceHref] = None
    pvp_summary: Optional[ResourceHref] = None
    media: Optional[ResourceHref] = None
    last_login_timestamp: int
    average_item_level: int
    equipped_item_level: int
    specializations: Optional[ResourceHref] = None
    statistics: Optional[ResourceHref] = None
    equipment: Optional[ResourceHref] = None
    appearance: Optional[ResourceHref] = None
    is_ghost: Optional[bool] = None
    is_self_found: Optional[bool] = None

    def get_last_login_datetime(self) -> datetime:
        """Convert the login timestamp to a datetime object"""
        return datetime.fromtimestamp(self.last_login_timestamp / 1000)  # Convert milliseconds to seconds

    def get_faction_name(self) -> str:
        """Get the faction name as a string"""
        return self.faction.get_name()

    def get_race_name(self) -> str:
        """Get the race name as a string"""
        return self.race.get_name()

    def get_class_name(self) -> str:
        """Get the class name as a string"""
        return self.character_class.get_name()

    def get_spec_id(self) -> Optional[int]:
        """Get the specialization ID if available"""
        if isinstance(self.active_spec, dict) and "id" in self.active_spec:
            return self.active_spec["id"]
        return None


class WoWAPIClient:
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize the World of Warcraft Profile API client.

        Args:
            client_id: Your Blizzard API client ID
            client_secret: Your Blizzard API client secret
            region: API region (us, eu, kr, tw, cn)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expiry = None
        self.session = None

    async def __aenter__(self):
        """Create session when entering async context"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session when exiting async context"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _get_access_token(self, region: GameRegion) -> str:
        """
        Get an access token from the Blizzard API.

        Returns:
            str: Access token
        """
        if self.token and self.token_expiry and datetime.now().timestamp() < self.token_expiry:
            return self.token

        # Create a session if none exists
        if not self.session:
            self.session = aiohttp.ClientSession()

        token_url = f"https://{region.value}.battle.net/oauth/token"

        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
        async with self.session.post(token_url, data={"grant_type": "client_credentials"}, auth=auth) as response:
            response.raise_for_status()
            token_data = await response.json()

        self.token = token_data["access_token"]
        self.token_expiry = datetime.now().timestamp() + token_data["expires_in"] - 60  # Buffer of 60 seconds

        return self.token

    async def get_character_profile(
        self,
        namespace: Namespace,
        region: GameRegion,
        realm: str,
        name: str,
    ) -> CharacterProfile:
        access_token = await self._get_access_token(region)
        api_host = f"{region.value}.api.blizzard.com" if region != GameRegion.CN else "gateway.battlenet.com.cn"

        url = f"https://{api_host}/profile/wow/character/{realm.lower()}/{name.lower()}"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"namespace": f"{namespace.value}-{region.value}", "locale": "en_US"}

        if not self.session:
            self.session = aiohttp.ClientSession()

        async with self.session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            data = await response.json()

        try:
            return CharacterProfile.model_validate(data)
        except Exception as e:
            logger.error(f"Validation error for character {name}: {e}")
            logger.error(f"Problematic data sample: {str(data)[:500]}...")
            raise

    async def get_character(
        self, version: GameVersion, region: GameRegion, realm: str, name: str
    ) -> CharacterBase | None:
        version = GameVersion(version) if type(version) == str else version
        region = GameRegion(region) if type(region) == str else region
        namespace = namespace_map[version]
        try:
            profile = await self.get_character_profile(namespace, region, realm, name)
        except Exception as e:
            logger.error(f"Error fetching character {name} from Battle.net: {e}")
            return None
        character = CharacterBase(
            region=region,
            version=version,
            realm=realm,
            name=name,
            class_=CharacterClass(profile.get_class_name().lower().replace(" ", "-")),
            level=profile.level,
        )
        if profile.is_ghost:
            # character.died_at = datetime.fromtimestamp(profile.last_login_timestamp // 1000).astimezone(timezone.utc)
            character.died_at = datetime.fromtimestamp(profile.last_login_timestamp // 1000).astimezone(timezone.utc)
        return character

    # async def get_guild_roster(
    #     self,
    #     realm_slug: str,
    #     guild_slug: str,
    #     namespace_type: Literal["profile", "profile-classic1x"] = "profile",
    # ) -> GuildRoster:
    #     """
    #     Get a guild's roster information asynchronously.

    #     Args:
    #         realm_slug: The slug of the guild's realm
    #         guild_slug: The slug of the guild (lowercase, spaces replaced with hyphens)
    #         namespace_type: The namespace type to use (profile for retail, profile-classic1x for Classic)

    #     Returns:
    #         GuildRoster: The guild roster data
    #     """
    #     access_token = await self._get_access_token()

    #     # Construct the API URL
    #     url = f"https://{self.api_host}/data/wow/guild/{realm_slug}/{guild_slug}/roster"

    #     # Set up the headers and parameters
    #     headers = {"Authorization": f"Bearer {access_token}"}
    #     params = {"namespace": f"{namespace_type}-{self.region}", "locale": "en_US"}

    #     # Create a session if none exists
    #     if not self.session:
    #         self.session = aiohttp.ClientSession()

    #     # Make the request
    #     async with self.session.get(url, headers=headers, params=params) as response:
    #         response.raise_for_status()
    #         data = await response.json()

    #     # Parse the response into our Pydantic model
    #     return GuildRoster.model_validate(data)


battlenet_client_id = os.getenv("BATTLENET_CLIENT_ID")
battlenet_client_secret = os.getenv("BATTLENET_CLIENT_SECRET")

if not battlenet_client_id or not battlenet_client_secret:
    logger.error("Battle.net credentials not set, skipping character updates")
    raise ValueError("Battle.net credentials not set")


wow_api_client = WoWAPIClient(battlenet_client_id, battlenet_client_secret)
