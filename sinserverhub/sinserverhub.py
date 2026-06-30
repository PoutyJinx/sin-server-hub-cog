from __future__ import annotations

from typing import Dict, Optional

import discord
from redbot.core import Config, commands


STATUS_EMOJIS = {
    "online": "🟢",
    "offline": "🔴",
    "maintenance": "🟡",
    "restarting": "🟠",
    "unknown": "⚫",
}
VALID_STATUSES = ", ".join(STATUS_EMOJIS.keys())


class SinServerHub(commands.Cog):
    """SIN Corp Server Hub for game server information."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=924761330815, force_registration=True)
        self.config.register_guild(servers={}, active_server=None)

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        # This cog stores server information only, not user data.
        return

    def _normalize_key(self, key: str) -> str:
        return key.strip().lower().replace(" ", "-")[:50]

    def _clean_status(self, status: Optional[str]) -> str:
        if not status:
            return "unknown"
        status = status.strip().lower()
        return status if status in STATUS_EMOJIS else "unknown"

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

    def _server_embed(self, guild: discord.Guild, key: str, data: dict) -> discord.Embed:
        status = self._clean_status(data.get("status"))
        emoji = STATUS_EMOJIS.get(status, "⚫")
        title = f"{emoji} SIN Corp Server Hub"
        embed = discord.Embed(
            title=title,
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
            embed.add_field(name="📦 Workshop / Modpack", value=data["workshop"], inline=False)
        if data.get("join"):
            embed.add_field(name="🚪 Join Instructions", value=data["join"][:1024], inline=False)
        if data.get("notes"):
            embed.add_field(name="📝 Notes", value=data["notes"][:1024], inline=False)
        if data.get("thumbnail"):
            embed.set_thumbnail(url=data["thumbnail"])

        updated_by = data.get("updated_by") or "SIN Corp Staff"
        updated_at = data.get("updated_at") or "Unknown"
        embed.set_footer(text=f"Key: {key} • Last updated by {updated_by} • {updated_at}")
        return embed

    async def _save_update(
        self,
        ctx: commands.Context,
        key: str,
        **updates,
    ):
        key = self._normalize_key(key)
        async with self.config.guild(ctx.guild).servers() as servers:
            data = servers.setdefault(key, {})
            for field, value in updates.items():
                if value is not None:
                    data[field] = value
            data["updated_by"] = str(ctx.author)
            data["updated_at"] = discord.utils.format_dt(discord.utils.utcnow(), style="f")
            servers[key] = data
        if not await self.config.guild(ctx.guild).active_server():
            await self.config.guild(ctx.guild).active_server.set(key)
        return key

    async def _set_status(self, ctx: commands.Context, key: str, status: str) -> bool:
        status = status.strip().lower()
        if status not in STATUS_EMOJIS:
            await ctx.send(f"Status must be one of: `{VALID_STATUSES}`")
            return False
        key = self._normalize_key(key)
        servers = await self._get_servers(ctx.guild)
        if key not in servers:
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return False
        await self._save_update(ctx, key, status=status)
        await ctx.send(f"{STATUS_EMOJIS[status]} `{key}` is now **{status.title()}**.")
        return True

    @commands.hybrid_group(name="server", aliases=["sinserver", "serverhub"], invoke_without_command=True)
    async def server(self, ctx: commands.Context):
        """Show the current SIN Corp server information."""
        if ctx.invoked_subcommand is None:
            await self.show(ctx)

    @server.command(name="show")
    async def show(self, ctx: commands.Context, key: Optional[str] = None):
        """Show the active server board, or a specific server by key."""
        key = self._normalize_key(key) if key else None
        found_key, data = await self._get_server_data(ctx.guild, key)
        if not data:
            await ctx.send("No SIN Corp server is currently listed. A moderator can set one with `/server set`.")
            return
        await ctx.send(embed=self._server_embed(ctx.guild, found_key, data))

    @server.command(name="list")
    async def list_servers(self, ctx: commands.Context):
        """List all saved SIN Corp servers."""
        servers = await self._get_servers(ctx.guild)
        if not servers:
            await ctx.send("No SIN Corp servers are saved yet.")
            return
        active = await self.config.guild(ctx.guild).active_server()
        lines = []
        for key, data in servers.items():
            status = self._clean_status(data.get("status"))
            marker = "⭐ " if key == active else ""
            lines.append(f"{marker}{STATUS_EMOJIS[status]} **{data.get('name') or key}** `/{key}` • {data.get('game', 'Unknown game')}")
        embed = discord.Embed(title="🏰 SIN Corp Server List", description="\n".join(lines), color=discord.Color.purple())
        await ctx.send(embed=embed)

    @server.command(name="info")
    async def info(self, ctx: commands.Context, key: str):
        """Show one saved server by key."""
        await self.show(ctx, key)

    @server.command(name="set")
    @commands.mod_or_permissions(manage_guild=True)
    async def set_server(
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
        notes: Optional[str] = None,
    ):
        """Create or replace a server board. Mods only."""
        status = self._clean_status(status)
        key = await self._save_update(
            ctx,
            key,
            game=game,
            name=server_name,
            ip=ip,
            password=password,
            status=status,
            slots=slots,
            workshop=workshop,
            notes=notes,
        )
        await self.config.guild(ctx.guild).active_server.set(key)
        await ctx.send(f"✅ SIN Corp server `{key}` saved and set as active.")

    @server.command(name="edit")
    @commands.mod_or_permissions(manage_guild=True)
    async def edit_server(
        self,
        ctx: commands.Context,
        key: str,
        game: Optional[str] = None,
        server_name: Optional[str] = None,
        ip: Optional[str] = None,
        password: Optional[str] = None,
        status: Optional[str] = None,
        slots: Optional[str] = None,
        workshop: Optional[str] = None,
        notes: Optional[str] = None,
        join: Optional[str] = None,
        thumbnail: Optional[str] = None,
    ):
        """Edit parts of a saved server. Mods only."""
        key = self._normalize_key(key)
        servers = await self._get_servers(ctx.guild)
        if key not in servers:
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        if status is not None:
            status = self._clean_status(status)
        await self._save_update(
            ctx,
            key,
            game=game,
            name=server_name,
            ip=ip,
            password=password,
            status=status,
            slots=slots,
            workshop=workshop,
            notes=notes,
            join=join,
            thumbnail=thumbnail,
        )
        await ctx.send(f"✅ SIN Corp server `{key}` updated.")

    @server.command(name="active")
    @commands.mod_or_permissions(manage_guild=True)
    async def active(self, ctx: commands.Context, key: str):
        """Set which server appears by default. Mods only."""
        key = self._normalize_key(key)
        servers = await self._get_servers(ctx.guild)
        if key not in servers:
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        await self.config.guild(ctx.guild).active_server.set(key)
        await ctx.send(f"⭐ `{key}` is now the active SIN Corp server.")

    @server.command(name="status")
    @commands.mod_or_permissions(manage_guild=True)
    async def status(self, ctx: commands.Context, key: str, status: str):
        """Set a server status. Mods only. online/offline/maintenance/restarting/unknown"""
        await self._set_status(ctx, key, status)

    @server.command(name="online")
    @commands.mod_or_permissions(manage_guild=True)
    async def online(self, ctx: commands.Context, key: str):
        """Mark a server as online. Mods only."""
        await self._set_status(ctx, key, "online")

    @server.command(name="offline")
    @commands.mod_or_permissions(manage_guild=True)
    async def offline(self, ctx: commands.Context, key: str):
        """Mark a server as offline. Mods only."""
        await self._set_status(ctx, key, "offline")

    @server.command(name="maintenance")
    @commands.mod_or_permissions(manage_guild=True)
    async def maintenance(self, ctx: commands.Context, key: str):
        """Mark a server as maintenance. Mods only."""
        await self._set_status(ctx, key, "maintenance")

    @server.command(name="notes")
    @commands.mod_or_permissions(manage_guild=True)
    async def notes(self, ctx: commands.Context, key: str, notes: str):
        """Update server notes. Mods only."""
        key = self._normalize_key(key)
        servers = await self._get_servers(ctx.guild)
        if key not in servers:
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        await self._save_update(ctx, key, notes=notes)
        await ctx.send(f"📝 Notes updated for `{key}`.")

    @server.command(name="workshop")
    @commands.mod_or_permissions(manage_guild=True)
    async def workshop(self, ctx: commands.Context, key: str, link: str):
        """Update workshop or modpack link. Mods only."""
        key = self._normalize_key(key)
        servers = await self._get_servers(ctx.guild)
        if key not in servers:
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        await self._save_update(ctx, key, workshop=link)
        await ctx.send(f"📦 Workshop/modpack link updated for `{key}`.")

    @server.command(name="password")
    @commands.mod_or_permissions(manage_guild=True)
    async def password(self, ctx: commands.Context, key: str, password: str):
        """Update server password. Mods only."""
        key = self._normalize_key(key)
        servers = await self._get_servers(ctx.guild)
        if key not in servers:
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        await self._save_update(ctx, key, password=password)
        await ctx.send(f"🔑 Password updated for `{key}`. It will be shown as a spoiler.")

    @server.command(name="restart")
    @commands.mod_or_permissions(manage_guild=True)
    async def restart(
        self,
        ctx: commands.Context,
        key: str,
        role: Optional[discord.Role] = None,
        downtime: Optional[str] = "5-10 minutes",
        message: Optional[str] = None,
    ):
        """Announce a manual server restart and mark it as restarting. Mods only."""
        key = self._normalize_key(key)
        servers = await self._get_servers(ctx.guild)
        if key not in servers:
            await ctx.send(f"I could not find a server with the key `{key}`.")
            return
        await self._save_update(ctx, key, status="restarting")
        data = servers[key]
        ping = role.mention if role else ""
        description = message or "The server is restarting. Please wait before reconnecting."
        embed = discord.Embed(
            title="⚠️ SIN Corp Server Restart",
            description=description,
            color=discord.Color.orange(),
        )
        embed.add_field(name="🎮 Game", value=data.get("game") or "Unknown", inline=True)
        embed.add_field(name="🏷️ Server", value=data.get("name") or key, inline=True)
        embed.add_field(name="⏰ Expected Downtime", value=downtime or "Unknown", inline=False)
        embed.set_footer(text=f"Restart announced by {ctx.author}")
        await ctx.send(content=ping, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))

    @server.command(name="delete")
    @commands.mod_or_permissions(manage_guild=True)
    async def delete(self, ctx: commands.Context, key: str):
        """Delete one saved server. Mods only."""
        key = self._normalize_key(key)
        async with self.config.guild(ctx.guild).servers() as servers:
            if key not in servers:
                await ctx.send(f"I could not find a server with the key `{key}`.")
                return
            del servers[key]
        active = await self.config.guild(ctx.guild).active_server()
        if active == key:
            await self.config.guild(ctx.guild).active_server.set(None)
        await ctx.send(f"🗑️ Deleted SIN Corp server `{key}`.")

    @server.command(name="clear")
    @commands.mod_or_permissions(manage_guild=True)
    async def clear(self, ctx: commands.Context):
        """Clear the current server board. Mods only."""
        await self.config.guild(ctx.guild).servers.set({})
        await self.config.guild(ctx.guild).active_server.set(None)
        await ctx.send("🧹 Cleared all SIN Corp server hub data for this Discord server.")
