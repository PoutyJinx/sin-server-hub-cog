# SIN Server Hub Cog

A Red-DiscordBot cog for gaming communities that need one clean place to show the current active game server.

Moderators can update the game, server name, IP address, spoilered password, status, slots, workshop/modpack link, notes, and join instructions. The cog also includes a manual restart notification command that can ping a configured role.

## Features

- Slash commands and prefix commands
- Public `/server show` command
- Moderator-only setup and edit commands
- Spoilered server password
- Workshop or modpack link field
- Notes and join instructions fields
- Manual status options: Online, Offline, Maintenance, Restarting, Unknown
- Manual restart notification with role ping
- Optional restart notification channel
- Per-server/guild configuration

## Installation

Replace `[p]` with your bot prefix.

```text
[p]repo add sin-server-hub-cog https://github.com/PoutyJinx/sin-server-hub-cog
[p]cog install sin-server-hub-cog sinserverhub
[p]load sinserverhub
```

Then enable and sync slash commands:

```text
[p]slash enablecog sinserverhub
[p]slash sync
```

Discord can take a few minutes to show new slash commands.

## Main Commands

### Public

```text
/server
/server show
```

Shows the current SIN Corp Server Hub embed.

### Moderator-only

```text
/server set
/server status
/server ip
/server password
/server workshop
/server notes
/server instructions
/server restartrole
/server restartchannel
/server restart
/server config
/server clear
```

Prefix aliases also work:

```text
[p]server show
[p]sinserver show
```

## Recommended First Setup

```text
/server set game:Project Zomboid server_name:SIN Corp Apocalypse ip:123.45.67.89:16261 password:brains status:Online slots:16 workshop:https://steamcommunity.com/sharedfiles/filedetails/?id=123456789 notes:New players welcome. Read the rules first. instructions:Download the Workshop collection before joining.
```

Set the restart ping role:

```text
/server restartrole role:@Community
```

Optional: set a dedicated notification channel:

```text
/server restartchannel channel:#server-info
```

Send a restart ping:

```text
/server restart reason:Updating mods and restarting the server.
```

## Permissions

All setup and edit commands require the user to be a Red moderator or have the Discord `Manage Server` permission.

`/server show` is available to everyone.

## Data Storage

This cog stores manually entered server information per Discord server, including server names, IPs, passwords, links, notes, configured role IDs, and configured channel IDs. It does not store personal user data.

## License

MIT License
