# SIN Server Hub Cog

A Red-DiscordBot cog for managing a community game server board with prefix and slash commands.

## Features

- `/server` slash command group
- `!server` / `!sinserver` prefix fallback
- Moderator-only setup and editing commands
- Multiple saved game servers
- Active server board
- Server status: online, offline, maintenance, restarting, unknown
- IP/address field
- Spoilered password field
- Workshop/modpack link
- Notes and join instructions
- Manual restart announcement with optional role ping
- Purple SIN Corp styled embeds

## Installation

Replace `[p]` with your bot prefix.

```txt
[p]repo add sin-server-hub-cog https://github.com/PoutyJinx/sin-server-hub-cog
[p]cog install sin-server-hub-cog sinserverhub
[p]load sinserverhub
[p]slash enablecog sinserverhub
[p]slash sync
```

After syncing, restart Discord with `Ctrl + R` if slash commands do not appear immediately.

## Commands

### Public

```txt
/server show
/server list
/server info <key>
```

Prefix fallback:

```txt
!server show
!sinserver show
!server list
```

### Moderator only

```txt
/server set <key> <game> <server_name> [ip] [password] [status] [slots] [workshop] [notes]
/server edit <key> [game] [server_name] [ip] [password] [status] [slots] [workshop] [notes] [join] [thumbnail]
/server active <key>
/server status <key> <status>
/server online <key>
/server offline <key>
/server maintenance <key>
/server notes <key> <notes>
/server workshop <key> <link>
/server password <key> <password>
/server restart <key> [role] [downtime] [message]
/server delete <key>
/server clear
```

Valid status values:

```txt
online, offline, maintenance, restarting, unknown
```

## Example

```txt
/server set zomboid "Project Zomboid" "SIN Corp Apocalypse" "123.45.67.89:16261" "brains" online "16 players" "https://steamcommunity.com/sharedfiles/filedetails/?id=123" "Download the mods before joining."
```

Restart ping example:

```txt
/server restart zomboid @Community "5-10 minutes" "The Project Zomboid server is restarting. Hide your snacks and wait for SIN Corp IT."
```

## GitHub Upload Layout

Your GitHub repository root should look like this:

```txt
README.md
info.json
sinserverhub/
```

Do not upload an extra folder inside the repository root.

## Data Storage

This cog stores server board information per Discord server. It does not store personal user data.
