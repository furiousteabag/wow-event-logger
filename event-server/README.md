# event-server

[![event-server | Build and Deploy](https://github.com/furiousteabag/wow-event-logger/actions/workflows/event-server-build-and-deploy.yml/badge.svg)](https://github.com/furiousteabag/wow-event-logger/actions/workflows/event-server-build-and-deploy.yml)

`event-server` is a REST server and a Telegram bot that listens to the changes in the character's data, updates the database, and sends updates to subscribed parties.

It is a part of the project that lets you monitor your friend's character progression in WoW in channels like Telegram, and by itself, `event-server` is not very useful. Full setup instructions are on the [project page](https://github.com/furiousteabag/wow-event-logger).

## Installation

### Telegram

Add [WoW Event Logger bot](https://t.me/wow_event_logger_bot) to the desired chat.

## Usage

### Telegram

#### /add \<realm\> \<name\>

Add character to the watchlist

#### /remove \<realm\> \<name\>

Remove character from the watchlist

#### /list

List all watched characters
