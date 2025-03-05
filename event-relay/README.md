# wow-event-relay

[![event-relay | Build and Release](https://github.com/furiousteabag/wow-event-logger/actions/workflows/event-relay-build-and-release.yml/badge.svg)](https://github.com/furiousteabag/wow-event-logger/actions/workflows/event-relay-build-and-release.yml)

`wow-event-relay` is a CLI & daemon program that monitors the changes in characters' data in World of Warcraft Classic files and sends them to the server.

It is a part of the project that lets you monitor your friend's character progression in WoW in channels like Telegram, and by itself, `wow-event-relay` is not very useful. Full setup instructions are on the [project page](https://github.com/furiousteabag/wow-event-logger).

## Installation

Grab an executable for your OS from the [latest release](https://github.com/furiousteabag/wow-event-logger/releases/latest) and run it in the terminal.

## Usage

Control the WoW folder with a `WOWEVENTRELAY_WOW_FOLDER` environment variable and start listening to the changes:

```bash
wow-event-relay start
```

How to set envs check in the [ollama faq](https://github.com/ollama/ollama/blob/main/docs/faq.md#how-do-i-configure-ollama-server).

### Linux

On Linux, it is more convenient to create a systemd daemon:

```
cat <<EOF | tee $HOME/.config/systemd/user/wow-event-relay.service >/dev/null
[Unit]
Description=WoW Event Relay Service

[Service]
Type=simple
ExecStart=/usr/bin/wow-event-relay start
Environment="WOWEVENTRELAY_WOW_FOLDER=%h/.local/share/wineprefixes/battlenet/drive_c/Program Files (x86)/World of Warcraft"

[Install]
WantedBy=default.target
EOF
```

You can control it like this:

```
systemctl --user daemon-reload
systemctl --user start wow-event-relay
systemctl --user status wow-event-relay
journalctl --user -u wow-event-relay --output=cat -f
```
