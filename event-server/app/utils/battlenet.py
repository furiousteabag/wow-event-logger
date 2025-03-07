from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

import aiohttp
from pydantic import BaseModel, HttpUrl


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


class WoWProfileClient:
    def __init__(self, client_id: str, client_secret: str, region: Literal["us", "eu", "kr", "tw", "cn"] = "us"):
        """
        Initialize the World of Warcraft Profile API client.

        Args:
            client_id: Your Blizzard API client ID
            client_secret: Your Blizzard API client secret
            region: API region (us, eu, kr, tw, cn)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.token = None
        self.token_expiry = None
        self.session = None

        # Set the API host based on region
        if region == "cn":
            self.api_host = "gateway.battlenet.com.cn"
        else:
            self.api_host = f"{region}.api.blizzard.com"

    async def __aenter__(self):
        """Create session when entering async context"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session when exiting async context"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _get_access_token(self) -> str:
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

        token_url = f"https://{self.region}.battle.net/oauth/token"

        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
        async with self.session.post(token_url, data={"grant_type": "client_credentials"}, auth=auth) as response:
            response.raise_for_status()
            token_data = await response.json()

        self.token = token_data["access_token"]
        self.token_expiry = datetime.now().timestamp() + token_data["expires_in"] - 60  # Buffer of 60 seconds

        return self.token

    async def get_character_profile(
        self,
        realm_slug: str,
        character_name: str,
        namespace_type: Literal["profile", "profile-classic1x"] = "profile",
    ) -> CharacterProfile:
        """
        Get a character's profile information asynchronously.

        Args:
            realm_slug: The slug of the character's realm
            character_name: The name of the character (case-insensitive)
            namespace_type: The namespace type to use (profile for retail, profile-classic1x for Classic)

        Returns:
            CharacterProfile: The character profile data
        """
        access_token = await self._get_access_token()

        # Lowercase the character name for the API
        character_name = character_name.lower()

        # Construct the API URL
        url = f"https://{self.api_host}/profile/wow/character/{realm_slug}/{character_name}"

        # Set up the headers and parameters
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"namespace": f"{namespace_type}-{self.region}", "locale": "en_US"}

        # Create a session if none exists
        if not self.session:
            self.session = aiohttp.ClientSession()

        # Make the request
        async with self.session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            data = await response.json()

        try:
            # Parse the response into our Pydantic model
            return CharacterProfile.model_validate(data)
        except Exception as e:
            # If validation fails, print detailed error info to help debug
            print(f"Validation error for character {character_name}: {e}")
            print(f"Problematic data sample: {str(data)[:500]}...")  # Print first 500 chars of data
            raise

    async def get_guild_roster(
        self,
        realm_slug: str,
        guild_slug: str,
        namespace_type: Literal["profile", "profile-classic1x"] = "profile",
    ) -> GuildRoster:
        """
        Get a guild's roster information asynchronously.

        Args:
            realm_slug: The slug of the guild's realm
            guild_slug: The slug of the guild (lowercase, spaces replaced with hyphens)
            namespace_type: The namespace type to use (profile for retail, profile-classic1x for Classic)

        Returns:
            GuildRoster: The guild roster data
        """
        access_token = await self._get_access_token()

        # Construct the API URL
        url = f"https://{self.api_host}/data/wow/guild/{realm_slug}/{guild_slug}/roster"

        # Set up the headers and parameters
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"namespace": f"{namespace_type}-{self.region}", "locale": "en_US"}

        # Create a session if none exists
        if not self.session:
            self.session = aiohttp.ClientSession()

        # Make the request
        async with self.session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            data = await response.json()

        # Parse the response into our Pydantic model
        return GuildRoster.model_validate(data)
