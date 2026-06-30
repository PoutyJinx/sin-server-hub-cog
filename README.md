# SIN Server Hub Cog

A Red-DiscordBot cog for a manual **SIN Corp Server Hub**.

It lets your Discord community see the currently active game server, including:

- Game
- Server name
- IP/address
- Spoilered password
- Status
- Slots
- Workshop/modpack link
- Notes
- Join instructions

## Repository name suggestion

Use this as the GitHub repository name:

```txt
sin-server-hub-cog
```

This should not collide with your earlier SIN cogs like `sinpurge` or `sinoffice`.

## Install with Red

Replace `<your-github-url>` with your actual repo URL.

```txt
[p]repo add sin-server-hub-cog <your-github-url>
[p]cog install sin-server-hub-cog sinserverhub
[p]load sinserverhub
```

If slash commands do not show up:

```txt
[p]slash sync
```

Then restart Discord or wait a little. Discord slash commands can be dramatic.

## Slash commands

Public:

```txt
/server show
```

Moderator/admin only:

```txt
/server set
/server status
/server notes
/server workshop
/server password
/server instructions
/server clear
```

## Prefix fallback

```txt
[p]sinserver
[p]sinserver clear
```

## Notes

The password is automatically wrapped in Discord spoiler tags.

Example:

```txt
||yourpassword||
```
