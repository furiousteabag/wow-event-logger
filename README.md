# WoW Event Logger

This project aims to help you stay on top of your guild mates' leveling progression via Telegram.

## Installation

Installation is 3-folded:

1. [WoW addon](https://www.curseforge.com/wow/addons/eventwatcher) to dump the most recent Guild Roaster data to file ([more info](https://github.com/furiousteabag/wow-event-logger/tree/master/event-watcher))
2. [Desktop daemon](https://github.com/furiousteabag/wow-event-logger/releases/latest) to read dumped data and send it to the server ([more info](https://github.com/furiousteabag/wow-event-logger/tree/master/event-relay))
3. [Telegram bot](https://t.me/wow_event_logger_bot) to subscribe to specific characters ([more info](https://github.com/furiousteabag/wow-event-logger/tree/master/event-server))

## Usage

Add characters that you would like to monitor in both WoW via `/ewadd <name>` and Telegram via `/add <realm> <name>`.

<!---
## ToDo
- save only on player logout
  - https://wowwiki-archive.fandom.com/wiki/Events_A-Z_(full_list) ("PLAYER_LOGOUT")
- dump all guild book to file
- with event relay actually check if not file has changed, but each individual entity, and leave only the entities which has changed
===
- add simple auth to the data collection endpoint
- https://github.com/tomrus88/BlizzardInterfaceCode/blob/master/Interface/AddOns/Blizzard_APIDocumentationGenerated/BattleNetDocumentation.lua
  - print(C_BattleNet.GetAccountInfoByGUID(UnitGUID("player"))["gameAccountInfo"]["gameAccountID"])
- https://wowwiki-archive.fandom.com/wiki/API_GuildRoster
- watch by battle net tag (all chars), not by char name
- initialize via all friends
-->
