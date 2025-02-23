#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "fire",
#     "requests",
#     "lupa",
#     "loguru",
#     "black",
#     "isort",
# ]
# ///


import json
import os
import time
from pathlib import Path
from typing import Optional

import requests
from fire import Fire
from loguru import logger
from lupa import LuaRuntime


def find_event_watcher(wow_folder: str) -> Optional[str]:
    """Find the first EventWatcher.lua file in the WoW directory structure."""
    wow_path = Path(wow_folder)
    classic_path = wow_path / "_classic_era_" / "WTF" / "Account"

    if not classic_path.exists():
        logger.error(f"Classic WoW path not found: {classic_path}")
        return None

    # Find first account folder
    for account_folder in classic_path.iterdir():
        if account_folder.is_dir():
            event_watcher = account_folder / "SavedVariables" / "EventWatcher.lua"
            if event_watcher.exists():
                logger.info(f"Found EventWatcher.lua at: {event_watcher}")
                return str(event_watcher)

    logger.error("EventWatcher.lua not found in any account folder")
    return None


def convert_lua_value(value):
    """Convert Lua value to Python value."""
    if isinstance(value, bytes):
        return value.decode("utf-8")
    elif value == True or value == False:
        return bool(value)
    elif isinstance(value, (int, float, str)):
        return value
    elif value is None:
        return None
    elif hasattr(value, "items"):  # It's a table
        return lua_table_to_dict(value)
    else:
        return str(value)  # Convert any other type to string


def lua_table_to_dict(table):
    """Convert a Lua table to a Python dictionary recursively."""
    if not table:
        return {}

    result = {}
    for k, v in table.items():
        key = convert_lua_value(k)
        value = convert_lua_value(v)
        result[key] = value
    return result


def parse_lua_table(content: str) -> dict:
    """Parse the Lua table using Lupa."""
    lua = LuaRuntime(encoding=None)  # type: ignore

    try:
        # Execute the Lua code
        lua.execute(content)
        # Get the EventWatcherDump table
        result = lua_table_to_dict(lua.globals().EventWatcherDump)  # type: ignore
        # Verify JSON serialization
        json.dumps(
            result
        )  # This will raise an error if result contains non-serializable types
        return result
    except Exception as e:
        logger.error(f"Failed to parse Lua table: {e}")
        return {}


def monitor_events(
    wow_folder: str, event_server_url: str = "https://wow.asmirnov.xyz/character"
):
    """
    Monitor EventWatcher.lua for changes and send updates to the server.

    Args:
        wow_folder: Path to WoW installation folder
        event_server_url: URL to send character updates (default: https://wow.asmirnov.xyz/character)
    """
    event_watcher_path = find_event_watcher(wow_folder)
    if not event_watcher_path:
        return

    last_data = None
    last_modified = 0

    while True:
        try:
            current_modified = os.path.getmtime(event_watcher_path)

            if current_modified != last_modified:
                with open(event_watcher_path, "r", encoding="utf-8") as f:
                    content = f.read()

                current_data = parse_lua_table(content)

                # Debug log the parsed data
                # logger.debug(f"Parsed data: {json.dumps(current_data, indent=2)}")

                # Send update if it's the first run or if data has changed
                if last_data is None:
                    logger.info(
                        "Initial read of EventWatcher.lua, sending first update..."
                    )
                    try:
                        response = requests.post(event_server_url, json=current_data)
                        response.raise_for_status()
                        logger.info("Initial update sent successfully")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Failed to send initial update: {e}")
                elif json.dumps(current_data, sort_keys=True) != json.dumps(
                    last_data, sort_keys=True
                ):
                    logger.info(
                        "Detected changes in EventWatcher.lua, sending update..."
                    )
                    try:
                        response = requests.post(event_server_url, json=current_data)
                        response.raise_for_status()
                        logger.info("Update sent successfully")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Failed to send update: {e}")

                last_data = current_data
                last_modified = current_modified

            time.sleep(1)  # Check every second

        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
            time.sleep(5)  # Wait longer on error before retrying


if __name__ == "__main__":
    Fire(monitor_events)
