import asyncio
import os
from typing import Dict, List, Tuple

from loguru import logger

from app.api.endpoints.character import upload_character_data
from app.bot import bot
from app.crud.character import crud_character
from app.crud.character_watch import crud_character_watch
from app.schemas.character import Character, CharacterEventData, EventWatcherRequest, GameRegion, GameVersion
from app.utils.battlenet import CharacterProfile, WoWAPIClient, wow_api_client
from app.utils.db import get_db


async def fetch_characters_from_battlenet():
    """
    Fetch all watched characters from the database and Battle.net,
    and return them in the format expected by the /character endpoint,
    grouped by region and version
    """
    try:
        session = get_db()
        watches = await crud_character_watch.get_all(session)
        unique_characters: set[str] = set()
        for watch in watches:
            unique_characters.add(watch.character_id)

        if not unique_characters:
            logger.info("No characters being watched, skipping update")
            return None

        # Fetch character data from database in parallel
        db_tasks = [crud_character.get_by_id(session, id=id) for id in unique_characters]
        db_results = await asyncio.gather(*db_tasks)

        # Filter out None results
        existing_characters: list[Character] = [char for char in db_results if char]

        logger.info(f"Fetching {len(unique_characters)} characters from Battle.net")

        # Fetch all character data from Battle.net
        tasks = [
            wow_api_client.get_character(realm=char.realm, name=char.name, version=char.version, region=char.region)
            for char in existing_characters
        ]
        results = await asyncio.gather(*tasks)

        # Group characters by region and version
        grouped_data: Dict[Tuple[GameRegion, GameVersion], Dict[str, Dict[str, CharacterEventData]]] = {}

        for character_api in results:
            if not character_api:
                continue

            # Create the character event data
            character_api_dump = character_api.model_dump()
            character_api_dump["died_at"] = (
                int(character_api_dump["died_at"].timestamp()) if character_api_dump["died_at"] else None
            )
            character_event_data = CharacterEventData(**character_api_dump)

            # Get the region and version
            # Ensure these are proper GameRegion and GameVersion objects
            region = character_api.region
            version = character_api.version
            realm = character_api.realm
            name = character_api.name

            # Create the group key - ensure we're using the enum values if they're not already
            if isinstance(region, str):
                try:
                    region = GameRegion[region]
                except KeyError:
                    region = GameRegion.US  # Default fallback

            if isinstance(version, str):
                try:
                    version = GameVersion[version]
                except KeyError:
                    version = GameVersion.CLASSIC  # Default fallback

            group_key = (region, version)

            # Initialize the group if it doesn't exist
            if group_key not in grouped_data:
                grouped_data[group_key] = {}

            # Initialize the realm if it doesn't exist
            if realm not in grouped_data[group_key]:
                grouped_data[group_key][realm] = {}

            # Add the character data
            grouped_data[group_key][realm][name] = character_event_data

        # Create request objects for each group
        requests = []
        for (region, version), realms in grouped_data.items():
            request = EventWatcherRequest(region=region, version=version, realms=realms)
            requests.append(request)

        return requests
    except Exception as e:
        logger.error(f"Error preparing character update data: {e}")
        return None


async def scheduled_character_update():
    """Call the character update endpoint with data from Battle.net for each region/version group"""
    try:
        request_data_list = await fetch_characters_from_battlenet()

        if not request_data_list:
            logger.info("No character data to update")
            return

        for request_data in request_data_list:
            if request_data and request_data.realms:
                # Call the update endpoint for each group
                logger.info(
                    f"Calling character update endpoint for region={request_data.region} version={request_data.version}"
                )
                response = await upload_character_data(bot, get_db(), request_data)
                logger.info(f"Character update response: {response}")
    except Exception as e:
        logger.error(f"Error in scheduled character update: {e}")


async def start_scheduler():
    """Start the scheduler to update characters periodically"""
    logger.info("Starting character update scheduler")

    # Run immediately on startup
    await scheduled_character_update()

    # Then run every hour
    while True:
        await asyncio.sleep(3600)  # 3600 seconds = 1 hour
        await scheduled_character_update()
