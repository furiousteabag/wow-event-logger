import asyncio
import os
from typing import Dict, List, Tuple

from loguru import logger

from app.crud.character import crud_character
from app.schemas.character import Character, CharacterEventData, EventWatcherRequest, WatchlistData
from app.utils.battlenet import CharacterProfile, WoWProfileClient
from app.utils.db import get_db


async def fetch_character_from_battlenet(client: WoWProfileClient, realm: str, name: str):
    """Fetch a single character profile from Battle.net"""
    try:
        profile = await client.get_character_profile(realm.lower(), name.lower(), namespace_type="profile-classic1x")
        return realm, name, profile, None
    except Exception as e:
        return realm, name, None, str(e)


async def fetch_characters_from_battlenet():
    """
    Fetch all watched characters from the database and Battle.net,
    and return them in the format expected by the /character endpoint
    """
    battlenet_client_id = os.getenv("BATTLENET_CLIENT_ID")
    battlenet_client_secret = os.getenv("BATTLENET_CLIENT_SECRET")

    if not battlenet_client_id or not battlenet_client_secret:
        logger.error("Battle.net credentials not set, skipping character updates")
        return None

    try:
        session = get_db()
        # Get all character watches
        data, _ = await session.table("character_watch_chat_telegram").select("*").execute()
        _, watches = data

        # Group watches by character to avoid duplicate Battle.net API calls
        unique_characters: set[tuple[str, str]] = set()
        for watch in watches:
            unique_characters.add((watch["realm"], watch["name"]))

        if not unique_characters:
            logger.info("No characters being watched, skipping update")
            return None

        # Get existing characters from database
        existing_characters: dict[tuple[str, str], Character] = {}
        for realm, name in unique_characters:
            char = await crud_character.get(session, realm=realm, name=name)
            if char:
                existing_characters[(realm, name)] = char

        logger.info(f"Fetching {len(unique_characters)} characters from Battle.net")

        # Prepare the request structure
        realms: Dict[str, WatchlistData] = {}

        # Fetch all character profiles concurrently
        async with WoWProfileClient(battlenet_client_id, battlenet_client_secret) as client:
            # Create tasks for all characters
            tasks = [fetch_character_from_battlenet(client, realm, name) for realm, name in unique_characters]

            # Run all tasks concurrently
            results = await asyncio.gather(*tasks)

            # Process results
            for realm, name, profile, error in results:
                if error:
                    logger.error(f"Error fetching character {realm}/{name}: {error}")
                    continue

                # If this realm isn't in our realms dict yet, add it
                if realm not in realms:
                    realms[realm] = WatchlistData(watchlist={})

                # Get existing character for online status and zone
                existing_char = existing_characters.get((realm, name))

                # Convert class name to our enum format
                class_name = profile.get_class_name().lower().replace(" ", "_")

                # Use existing values for online and zone if available, otherwise defaults
                online = False if existing_char is None else existing_char.online
                zone = "Unknown" if existing_char is None else existing_char.zone

                if existing_char.died_at:
                    continue

                died_at = None
                if profile.is_ghost:
                    # Convert millisecond timestamp to seconds (UTC)
                    died_at = profile.last_login_timestamp // 1000

                # Create character event data
                # Using direct construction with correct field names
                realms[realm].watchlist[name] = CharacterEventData(
                    level=profile.level,
                    class_=class_name,  # Use field name, not alias
                    online=online,
                    zone=zone,
                    died_at=died_at,
                )

            # Create the final request object
            return EventWatcherRequest(realms=realms)

    except Exception as e:
        logger.error(f"Error preparing character update data: {e}")
        return None


async def scheduled_character_update(update_endpoint):
    """Call the character update endpoint with data from Battle.net"""
    try:
        request_data = await fetch_characters_from_battlenet()

        if request_data and request_data.realms:
            # Call the update endpoint
            logger.info("Calling character update endpoint with fetched data")
            response = await update_endpoint(get_db(), request_data)
            logger.info(f"Character update response: {response}")
        else:
            logger.info("No character data to update")

    except Exception as e:
        logger.error(f"Error in scheduled character update: {e}")


async def start_scheduler(update_endpoint):
    """Start the scheduler to update characters periodically"""
    logger.info("Starting character update scheduler")

    # Run immediately on startup
    await scheduled_character_update(update_endpoint)

    # Then run every hour
    while True:
        await asyncio.sleep(3600)  # 3600 seconds = 1 hour
        await scheduled_character_update(update_endpoint)
