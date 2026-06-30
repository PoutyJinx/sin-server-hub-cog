# SIN Server Hub Cog

A Red-DiscordBot cog for managing community game server information through a SIN Corp styled server board.

## Features

- Real `/server` slash command group using Discord app commands
- Prefix fallback commands: `!server` and `!sinserver`
- Multiple saved servers
- Active server board
- Server status: online, offline, maintenance, restarting, unknown
- IP/address field
- Spoilered password field
- Slots field
- Workshop/modpack link
- Notes and join instructions
- Restart announcements with optional role ping
- Moderator-only management commands

## Install

```text
[p]repo add sin-server-hub-cog https://github.com/YOURNAME/sin-server-hub-cog
[p]cog install sin-server-hub-cog sinserverhub
[p]load sinserverhub
[p]slash sync
```

After syncing, Discord may need a few minutes to show `/server`.

## Slash Commands

```text
/server show
/server list
/server info
/server set
/server edit
/server active
/server status
/server restart
/server delete
/server clear
```

## Prefix Commands

```text
!server
!server show
!server list
!server info project
!server set project "Project Zomboid" "SIN Corp Community Server" "51.38.107.44:1025" "password" online "16" "Workshop link" "Notes here"
!server edit project notes "New notes here"
!server restart project @Community "5-10 minutes" "Server restart incoming."
```

For prefix commands, use quotes when a value contains spaces.
Slash commands do not need quotes.

## Permissions

Public commands can be used by everyone.
Setup, edit, delete, status and restart commands require moderator permission or Manage Server.
