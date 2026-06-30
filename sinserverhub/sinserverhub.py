from __future__ import annotations

from typing import Dict, Optional

import discord
from discord import app_commands
from redbot.core import Config, commands

STATUS_EMOJIS = {
    "online": "🟢",
    "offline": "🔴",
    "maintenance": "🟡",
    "restarting": "🟠",
    "unknown": "⚫",
}
VALID_STATUSES = list(STATUS_EMOJIS.keys())


def clean_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    if value.lower() in {"none", "null", "-", "skip", "empty"}:
        return ""
    return value


class SinServerHub(commands.Cog):
    """SIN Corp Server Hub for game server information."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=924761330816, force_registration=True)
        self.config.register_guild(servers={}, active_server=None)

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        return

    def _normalize_key(self, key: str) -> str:
        return key.strip().lower().replace(" ", "-")[:50]

    def _clean_status(self, status: Optional[str]) -> str:
        if not status:
            return "unknown"
        status = status.strip().lower()
        return status if status in STATUS_EMOJIS else "unknown"

    async def _is_mod(self, user: discord.Member) -> bool:
        try:
            return await self.bot.is_mod(user) or user.guild_permissions.manage_guild
        except Exception:
            return user.guild_permissions.manage_guild

    async def _slash_mod_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
            return False
        if not await self._is_mod(interaction.user):
            await interaction.response.send_message("Only moderators can use this SIN Corp control panel.", ephemeral=True)
            return False
        return True

    async def _get_servers(self, guild: discord.Guild) -> Dict[str, dict]:
        return await self.config.guild(guild).servers()

    async def _get_server_data(self, guild: discord.Guild, key: Optional[str] = None):
        servers = await self._get_servers(guild)
        if not servers:
            return None, None
        if key is None:
            key = await self.config.guild(guild).active_server()
        if not key or key not in servers:
            key = next(iter(servers.keys()))
        return key, servers.get(key)

    def _server_embed(self, key: str, data: dict) -> discord.Embed:
        status = self._clean_status(data.get("status"))
        emoji = STATUS_EMOJIS.get(status, "⚫")
        embed = discord.Embed(
            title=f"{emoji} SIN Corp Server Hub",
            description=data.get("description") or "Current community server information.",
            color=discord.Color.purple(),
        )
        embed.add_field(name="🎮 Game", value=data.get("game") or "Not set", inline=True)
        embed.add_field(name="🏷️ Server Name", value=data.get("name") or key, inline=True)
        embed.add_field(name="📡 Status", value=f"{emoji} {status.title()}", inline=True)
        if data.get("ip"):
            embed.add_field(name="🌍 IP / Address", value=f"`{data['ip']}`", inline=False)
        if data.get("password"):
            embed.add_field(name="🔑 Password", value=f"||{data['password']}||", inline=True)
        if data.get("slots"):
            embed.add_field(name="👥 Slots", value=str(data["slots"]), inline=True)
        if data.get("workshop"):
            embed.add_field(name="📦 Workshop / Modpack", value=data["workshop"][:1024], inline=False)
        if data.get("join"):
            embed.add_field(name="🚪 Join Instructions", value=data["join"][:1024], inline=False)
        if data.get("notes"):
            embed.add_field(name="📝 Notes", value=data["notes"][:1024], inline=False)
        if data.get("thumbnail"):
            embed.set_thumbnail(url=data["thumbnail"])
        embed.set_footer(text=f"Key: {key} • Last updated by {data.get('updated_by', 'SIN Corp Staff')} • {data.get('updated_at', 'Unknown')}")
        return embed

    async def _save_update(self, guild: discord.Guild, author: discord.abc.User, key: str, **updates) -> str:
        key = self._normalize_key(key)
        async with self.config.guild(guild).servers() as servers:
            data = servers.setdefault(key, {})
            for field, value in updates.items():
                value = clean_optional(value)
                if value is not None:
                    data[field] = value
            data["updated_by"] = str(author)
            data["updated_at"] = discord.utils.format_dt(discord.utils.utcnow(), style="f")
            servers[key] = data
        if not await self.config.guild(guild).active_server():
            await self.config.guild(guild).active_server.set(key)
        return key

    async def _set_status_core(self, guild: discord.Guild, author: discord.abc.User, key: str, status: str):
        status = self._clean_status(status)
        key = self._normalize_key(key)
        servers = await self._get_servers(guild)
        if key not in servers:
            return False, key, status
        await self._save_update(guild, author, key, status=status)
        return True, key, status

    def _list_embed(self, guild: discord.Guild, servers: Dict[str, dict], active: Optional[str]) -> discord.Embed:
        lines = []
        for key, data in servers.items():
            status = self._clean_status(data.get("status"))
            marker = "⭐ " if key == active else ""
            lines.append(f"{marker}{STATUS_EMOJIS[status]} **{data.get('name') or key}** `{key}` • {data.get('game', 'Unknown game')}")
        return discord.Embed(title="🏰 SIN Corp Server List", description="\n".join(lines), color=discord.Color.purple())

    # ---------------- Prefix commands ----------------
    @commands.group(name="server", aliases=["sinserver", "serverhub"], invoke_without_command=True)
    async def server_prefix(self, ctx: commands.Context):
        """Show the active SIN Corp server board."""
        await self.show_prefix(ctx)

    @server_prefix.command(name="show")
    async def show_prefix(self, ctx: commands.Context, key: Optional[str] = None):
        """Show the active server, or one by key."""
        found_key, data = await self._get_server_data(ctx.guild, self._normalize_key(key) if key else None)
        if not data:
            await ctx.send("No SIN Corp server is currently listed. A moderator can set one with `/server set` or `!server set`.")
            return
        await ctx.send(embed=self._server_embed(found_key, data))

    @server_prefix.command(name="list")
    async def list_prefix(self, ctx: commands.Context):
        """List all saved servers."""
        servers = await self._get_servers(ctx.guild)
        if not servers:
            await ctx.send("No SIN Corp servers are saved yet.")
            return
        active = await self.config.guild(ctx.guild).active_server()
        await ctx.send(embed=self._list_embed(ctx.guild, servers, active))

    @server_prefix.command(name="info")
    async def info_prefix(self, ctx: commands.Context, key: str):
        """Show a saved server by key."""
        await self.show_prefix(ctx, key)

    @server_prefix.command(name="set")
    @commands.mod_or_permissions(manage_guild=True)
    async def set_prefix(
        self,
        ctx: commands.Context,
        key: str,
        game: str,
        server_name: str,
        ip: Optional[str] = None,
        password: Optional[str] = None,
        status: Optional[str] = "unknown",
        slots: Optional[str] = None,
        workshop: Optional[str] = None,
        *,
        notes: Optional[str] = None,
    ):
        """Create or replace a server. Use quotes around values with spaces."""
        key = await self._save_update(ctx.guild, ctx.author, key, game=game, name=server_name, ip=ip, password=password, status=self._clean_status(status), slots=slots, workshop=workshop, notes=notes)
        await self.config.guild(ctx.guild).active_server.set(key)
        await ctx.send(f"✅ SIN Corp server `{key}` saved and set as active.")

    @server_prefix.command(name="edit")
    @commands.mod_or_permissions(manage_guild=True)
    async def edit_prefix(self, ctx: commands.Context, key: str, field: str, *, value: str):
        """Edit one field. Fields: game, name, ip, password, status, slots, workshop, notes, join, thumbnail."""
        allowed = {"game", "name", "server_name", "ip", "password", "status", "slots", "workshop", "notes", "join", "thumbnail"}
        field = field.lower()
        if field not in allowed:
            await ctx.send("Field must be one of: `game, name, ip, password, status, slots, workshop, notes, join, thumbnail`.")
            return
        if field == "server_name":
            field = "name"
        if field == "status":
            value = self._clean_status(value)
        key = self._normalize_key(key)
        if key not in await self._get_servers(ctx.guild):
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        await self._save_update(ctx.guild, ctx.author, key, **{field: value})
        await ctx.send(f"✅ Updated `{field}` for `{key}`.")

    @server_prefix.command(name="active")
    @commands.mod_or_permissions(manage_guild=True)
    async def active_prefix(self, ctx: commands.Context, key: str):
        key = self._normalize_key(key)
        if key not in await self._get_servers(ctx.guild):
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        await self.config.guild(ctx.guild).active_server.set(key)
        await ctx.send(f"⭐ `{key}` is now the active SIN Corp server.")

    @server_prefix.command(name="status")
    @commands.mod_or_permissions(manage_guild=True)
    async def status_prefix(self, ctx: commands.Context, key: str, status: str):
        ok, key, status = await self._set_status_core(ctx.guild, ctx.author, key, status)
        await ctx.send(f"{STATUS_EMOJIS[status]} `{key}` is now **{status.title()}**." if ok else f"I could not find a server with the key `{key}`.")

    @server_prefix.command(name="restart")
    @commands.mod_or_permissions(manage_guild=True)
    async def restart_prefix(self, ctx: commands.Context, key: str, role: Optional[discord.Role] = None, downtime: str = "5-10 minutes", *, message: Optional[str] = None):
        await self._restart_send(ctx, key, role, downtime, message)

    @server_prefix.command(name="delete")
    @commands.mod_or_permissions(manage_guild=True)
    async def delete_prefix(self, ctx: commands.Context, key: str):
        await self._delete_send(ctx, key)

    @server_prefix.command(name="clear")
    @commands.mod_or_permissions(manage_guild=True)
    async def clear_prefix(self, ctx: commands.Context):
        await self.config.guild(ctx.guild).servers.set({})
        await self.config.guild(ctx.guild).active_server.set(None)
        await ctx.send("🧹 Cleared all SIN Corp server hub data for this Discord server.")

    async def _restart_send(self, ctx: commands.Context, key: str, role: Optional[discord.Role], downtime: str, message: Optional[str]):
        key = self._normalize_key(key)
        servers = await self._get_servers(ctx.guild)
        if key not in servers:
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        await self._save_update(ctx.guild, ctx.author, key, status="restarting")
        data = (await self._get_servers(ctx.guild))[key]
        embed = discord.Embed(title="⚠️ SIN Corp Server Restart", description=message or "The server is restarting. Please wait before reconnecting.", color=discord.Color.orange())
        embed.add_field(name="🎮 Game", value=data.get("game") or "Unknown", inline=True)
        embed.add_field(name="🏷️ Server", value=data.get("name") or key, inline=True)
        embed.add_field(name="⏰ Expected Downtime", value=downtime or "Unknown", inline=False)
        embed.set_footer(text=f"Restart announced by {ctx.author}")
        await ctx.send(content=role.mention if role else "", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))

    async def _delete_send(self, ctx: commands.Context, key: str):
        key = self._normalize_key(key)
        async with self.config.guild(ctx.guild).servers() as servers:
            if key not in servers:
                await ctx.send(f"I could not find a server with the key `{key}`.")
                return
            del servers[key]
        if await self.config.guild(ctx.guild).active_server() == key:
            await self.config.guild(ctx.guild).active_server.set(None)
        await ctx.send(f"🗑️ Deleted SIN Corp server `{key}`.")

    # ---------------- Slash commands ----------------
    server_slash = app_commands.Group(name="server", description="SIN Corp Server Hub")

    @server_slash.command(name="show", description="Show the active SIN Corp server board, or one by key.")
    @app_commands.describe(key="Optional server key, for example project or zomboid")
    async def slash_show(self, interaction: discord.Interaction, key: Optional[str] = None):
        found_key, data = await self._get_server_data(interaction.guild, self._normalize_key(key) if key else None)
        if not data:
            await interaction.response.send_message("No SIN Corp server is currently listed. A moderator can set one with `/server set`.", ephemeral=True)
            return
        await interaction.response.send_message(embed=self._server_embed(found_key, data))

    @server_slash.command(name="list", description="List all saved SIN Corp servers.")
    async def slash_list(self, interaction: discord.Interaction):
        servers = await self._get_servers(interaction.guild)
        if not servers:
            await interaction.response.send_message("No SIN Corp servers are saved yet.", ephemeral=True)
            return
        active = await self.config.guild(interaction.guild).active_server()
        await interaction.response.send_message(embed=self._list_embed(interaction.guild, servers, active))

    @server_slash.command(name="info", description="Show one saved SIN Corp server by key.")
    async def slash_info(self, interaction: discord.Interaction, key: str):
        await self.slash_show(interaction, key)

    @server_slash.command(name="set", description="Create or replace a SIN Corp server board. Mods only.")
    @app_commands.describe(key="Short key, like project or zomboid", game="Game name", server_name="Display name", ip="IP or address", password="Password, shown as spoiler", status="online/offline/maintenance/restarting/unknown", slots="Player slots", workshop="Workshop or modpack link", notes="Notes shown on the board")
    async def slash_set(self, interaction: discord.Interaction, key: str, game: str, server_name: str, ip: Optional[str] = None, password: Optional[str] = None, status: Optional[str] = "unknown", slots: Optional[str] = None, workshop: Optional[str] = None, notes: Optional[str] = None):
        if not await self._slash_mod_check(interaction):
            return
        key = await self._save_update(interaction.guild, interaction.user, key, game=game, name=server_name, ip=ip, password=password, status=self._clean_status(status), slots=slots, workshop=workshop, notes=notes)
        await self.config.guild(interaction.guild).active_server.set(key)
        await interaction.response.send_message(f"✅ SIN Corp server `{key}` saved and set as active.", ephemeral=True)

    @server_slash.command(name="edit", description="Edit one field on a saved server. Mods only.")
    @app_commands.describe(field="game, name, ip, password, status, slots, workshop, notes, join, thumbnail", value="New value")
    async def slash_edit(self, interaction: discord.Interaction, key: str, field: str, value: str):
        if not await self._slash_mod_check(interaction):
            return
        allowed = {"game", "name", "server_name", "ip", "password", "status", "slots", "workshop", "notes", "join", "thumbnail"}
        field = field.lower()
        if field not in allowed:
            await interaction.followup.send("Field must be one of: `game, name, ip, password, status, slots, workshop, notes, join, thumbnail`.", ephemeral=True)
            return
        if field == "server_name":
            field = "name"
        if field == "status":
            value = self._clean_status(value)
        key = self._normalize_key(key)
        if key not in await self._get_servers(interaction.guild):
            await interaction.response.send_message(f"I could not find a server with the key `{key}`.", ephemeral=True)
            return
        await self._save_update(interaction.guild, interaction.user, key, **{field: value})
        await interaction.response.send_message(f"✅ Updated `{field}` for `{key}`.", ephemeral=True)

    @server_slash.command(name="active", description="Set which server appears by default. Mods only.")
    async def slash_active(self, interaction: discord.Interaction, key: str):
        if not await self._slash_mod_check(interaction):
            return
        key = self._normalize_key(key)
        if key not in await self._get_servers(interaction.guild):
            await interaction.response.send_message(f"I could not find a server with the key `{key}`.", ephemeral=True)
            return
        await self.config.guild(interaction.guild).active_server.set(key)
        await interaction.response.send_message(f"⭐ `{key}` is now the active SIN Corp server.", ephemeral=True)

    @server_slash.command(name="status", description="Set server status. Mods only.")
    async def slash_status(self, interaction: discord.Interaction, key: str, status: str):
        if not await self._slash_mod_check(interaction):
            return
        ok, key, status = await self._set_status_core(interaction.guild, interaction.user, key, status)
        await interaction.response.send_message(f"{STATUS_EMOJIS[status]} `{key}` is now **{status.title()}**." if ok else f"I could not find a server with the key `{key}`.", ephemeral=True)

    @server_slash.command(name="restart", description="Announce a manual server restart and ping a role. Mods only.")
    async def slash_restart(self, interaction: discord.Interaction, key: str, role: Optional[discord.Role] = None, downtime: Optional[str] = "5-10 minutes", message: Optional[str] = None):
        if not await self._slash_mod_check(interaction):
            return
        key = self._normalize_key(key)
        servers = await self._get_servers(interaction.guild)
        if key not in servers:
            await interaction.response.send_message(f"I could not find a server with the key `{key}`.", ephemeral=True)
            return
        await self._save_update(interaction.guild, interaction.user, key, status="restarting")
        data = (await self._get_servers(interaction.guild))[key]
        embed = discord.Embed(title="⚠️ SIN Corp Server Restart", description=message or "The server is restarting. Please wait before reconnecting.", color=discord.Color.orange())
        embed.add_field(name="🎮 Game", value=data.get("game") or "Unknown", inline=True)
        embed.add_field(name="🏷️ Server", value=data.get("name") or key, inline=True)
        embed.add_field(name="⏰ Expected Downtime", value=downtime or "Unknown", inline=False)
        embed.set_footer(text=f"Restart announced by {interaction.user}")
        await interaction.response.send_message(content=role.mention if role else "", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))

    @server_slash.command(name="delete", description="Delete one saved server. Mods only.")
    async def slash_delete(self, interaction: discord.Interaction, key: str):
        if not await self._slash_mod_check(interaction):
            return
        key = self._normalize_key(key)
        async with self.config.guild(interaction.guild).servers() as servers:
            if key not in servers:
                await interaction.response.send_message(f"I could not find a server with the key `{key}`.", ephemeral=True)
                return
            del servers[key]
        if await self.config.guild(interaction.guild).active_server() == key:
            await self.config.guild(interaction.guild).active_server.set(None)
        await interaction.response.send_message(f"🗑️ Deleted SIN Corp server `{key}`.", ephemeral=True)

    @server_slash.command(name="clear", description="Clear all server hub data. Mods only.")
    async def slash_clear(self, interaction: discord.Interaction):
        if not await self._slash_mod_check(interaction):
            return
        await self.config.guild(interaction.guild).servers.set({})
        await self.config.guild(interaction.guild).active_server.set(None)
        await interaction.response.send_message("🧹 Cleared all SIN Corp server hub data for this Discord server.", ephemeral=True)
