from __future__ import annotations

from typing import Optional

import discord
from redbot.core import Config, commands


class SinServerHub(commands.Cog):
    """SIN Corp Server Hub for game server information."""

    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=911300420260630, force_registration=True)
        default_guild = {
            "enabled": False,
            "game": None,
            "server_name": None,
            "ip": None,
            "password": None,
            "status": "Unknown",
            "slots": None,
            "workshop": None,
            "notes": None,
            "instructions": None,
            "restart_role_id": None,
            "restart_channel_id": None,
            "last_updated_by": None,
            "last_updated_at": None,
        }
        self.config.register_guild(**default_guild)

    async def _is_mod_ctx(self, ctx: commands.Context) -> bool:
        return await self.bot.is_mod(ctx.author) or ctx.author.guild_permissions.manage_guild

    async def _touch(self, ctx: commands.Context) -> None:
        await self.config.guild(ctx.guild).last_updated_by.set(ctx.author.id)
        await self.config.guild(ctx.guild).last_updated_at.set(discord.utils.utcnow().isoformat())

    def _status_icon(self, status: Optional[str]) -> str:
        normalized = (status or "unknown").lower()
        if normalized == "online":
            return "🟢"
        if normalized == "offline":
            return "🔴"
        if normalized == "maintenance":
            return "🟡"
        if normalized == "restarting":
            return "🔄"
        return "⚫"

    def _clean_status(self, status: Optional[str]) -> str:
        if not status:
            return "Unknown"
        status = status.strip().lower()
        valid = {
            "online": "Online",
            "offline": "Offline",
            "maintenance": "Maintenance",
            "unknown": "Unknown",
            "restarting": "Restarting",
        }
        return valid.get(status, status.title())

    def _spoiler(self, value: Optional[str]) -> str:
        if not value:
            return "Not listed"
        return f"||{discord.utils.escape_markdown(value)}||"

    def _field_value(self, value: Optional[str], default: str = "Not listed") -> str:
        if value is None or str(value).strip() == "":
            return default
        return str(value)

    async def _make_embed(self, guild: discord.Guild) -> discord.Embed:
        data = await self.config.guild(guild).all()
        status = self._clean_status(data.get("status"))
        icon = self._status_icon(status)

        embed = discord.Embed(
            title="🏰 SIN Corp Server Hub",
            description=f"{icon} **Status:** {status}",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow(),
        )

        embed.add_field(name="🎮 Game", value=self._field_value(data.get("game")), inline=True)
        embed.add_field(name="🏷️ Server Name", value=self._field_value(data.get("server_name")), inline=True)
        embed.add_field(name="👥 Slots", value=self._field_value(data.get("slots")), inline=True)
        embed.add_field(name="🌍 IP / Address", value=f"`{self._field_value(data.get('ip'))}`", inline=False)
        embed.add_field(name="🔑 Password", value=self._spoiler(data.get("password")), inline=False)

        if data.get("workshop"):
            embed.add_field(name="📦 Workshop / Modpack", value=data["workshop"], inline=False)
        if data.get("instructions"):
            embed.add_field(name="📘 Join Instructions", value=data["instructions"], inline=False)
        if data.get("notes"):
            embed.add_field(name="📝 Notes", value=data["notes"], inline=False)

        updated_by = data.get("last_updated_by")
        if updated_by:
            member = guild.get_member(updated_by)
            updater = member.display_name if member else f"User ID {updated_by}"
            embed.set_footer(text=f"Last updated by {updater} • SIN Corp Server Hub v{self.__version__}")
        else:
            embed.set_footer(text=f"SIN Corp Server Hub v{self.__version__}")
        return embed

    async def _send_or_reply(self, ctx: commands.Context, content: Optional[str] = None, **kwargs):
        try:
            await ctx.reply(content, mention_author=False, **kwargs)
        except Exception:
            await ctx.send(content, **kwargs)

    @commands.hybrid_group(name="server", aliases=["sinserver"], invoke_without_command=True)
    async def server_group(self, ctx: commands.Context):
        """Show the current SIN Corp server info."""
        await self.show(ctx)

    @server_group.command(name="show")
    async def show(self, ctx: commands.Context):
        """Show the current SIN Corp server info."""
        if ctx.guild is None:
            return await self._send_or_reply(ctx, "This command can only be used in a server.")
        enabled = await self.config.guild(ctx.guild).enabled()
        if not enabled:
            return await self._send_or_reply(ctx, "No SIN Corp server is currently listed. A moderator can set one with `/server set`.")
        embed = await self._make_embed(ctx.guild)
        await self._send_or_reply(ctx, embed=embed)

    @server_group.command(name="set")
    @commands.mod_or_permissions(manage_guild=True)
    async def set_server(
        self,
        ctx: commands.Context,
        game: str,
        server_name: str,
        ip: str,
        password: Optional[str] = None,
        status: Optional[str] = "Online",
        slots: Optional[str] = None,
        workshop: Optional[str] = None,
        notes: Optional[str] = None,
        instructions: Optional[str] = None,
    ):
        """Set the active server info. Moderator only."""
        if ctx.guild is None:
            return await self._send_or_reply(ctx, "This command can only be used in a server.")
        status = self._clean_status(status)
        async with self.config.guild(ctx.guild).all() as data:
            data["enabled"] = True
            data["game"] = game
            data["server_name"] = server_name
            data["ip"] = ip
            data["password"] = password
            data["status"] = status
            data["slots"] = slots
            data["workshop"] = workshop
            data["notes"] = notes
            data["instructions"] = instructions
            data["last_updated_by"] = ctx.author.id
            data["last_updated_at"] = discord.utils.utcnow().isoformat()
        embed = await self._make_embed(ctx.guild)
        await self._send_or_reply(ctx, "✅ SIN Corp server info updated.", embed=embed)

    @server_group.command(name="status")
    @commands.mod_or_permissions(manage_guild=True)
    async def status(self, ctx: commands.Context, status: str):
        """Update server status: online, offline, maintenance, restarting, unknown."""
        if ctx.guild is None:
            return await self._send_or_reply(ctx, "This command can only be used in a server.")
        await self.config.guild(ctx.guild).enabled.set(True)
        await self.config.guild(ctx.guild).status.set(self._clean_status(status))
        await self._touch(ctx)
        await self._send_or_reply(ctx, f"✅ Server status set to **{self._clean_status(status)}**.")

    @server_group.command(name="ip")
    @commands.mod_or_permissions(manage_guild=True)
    async def ip(self, ctx: commands.Context, *, ip: str):
        """Update the server IP/address. Moderator only."""
        await self.config.guild(ctx.guild).enabled.set(True)
        await self.config.guild(ctx.guild).ip.set(ip)
        await self._touch(ctx)
        await self._send_or_reply(ctx, "✅ Server IP/address updated.")

    @server_group.command(name="password")
    @commands.mod_or_permissions(manage_guild=True)
    async def password(self, ctx: commands.Context, *, password: Optional[str] = None):
        """Update or clear the server password. Moderator only."""
        await self.config.guild(ctx.guild).password.set(password)
        await self._touch(ctx)
        await self._send_or_reply(ctx, "✅ Server password updated. It will be spoilered in the embed.")

    @server_group.command(name="workshop")
    @commands.mod_or_permissions(manage_guild=True)
    async def workshop(self, ctx: commands.Context, *, link: Optional[str] = None):
        """Update or clear the workshop/modpack link. Moderator only."""
        await self.config.guild(ctx.guild).workshop.set(link)
        await self._touch(ctx)
        await self._send_or_reply(ctx, "✅ Workshop/modpack link updated.")

    @server_group.command(name="notes")
    @commands.mod_or_permissions(manage_guild=True)
    async def notes(self, ctx: commands.Context, *, notes: Optional[str] = None):
        """Update or clear server notes. Moderator only."""
        await self.config.guild(ctx.guild).notes.set(notes)
        await self._touch(ctx)
        await self._send_or_reply(ctx, "✅ Server notes updated.")

    @server_group.command(name="instructions")
    @commands.mod_or_permissions(manage_guild=True)
    async def instructions(self, ctx: commands.Context, *, instructions: Optional[str] = None):
        """Update or clear join instructions. Moderator only."""
        await self.config.guild(ctx.guild).instructions.set(instructions)
        await self._touch(ctx)
        await self._send_or_reply(ctx, "✅ Join instructions updated.")

    @server_group.command(name="restartrole")
    @commands.mod_or_permissions(manage_guild=True)
    async def restartrole(self, ctx: commands.Context, role: Optional[discord.Role] = None):
        """Set or clear the role pinged by /server restart. Moderator only."""
        if role is None:
            await self.config.guild(ctx.guild).restart_role_id.set(None)
            await self._touch(ctx)
            return await self._send_or_reply(ctx, "✅ Restart ping role cleared.")
        await self.config.guild(ctx.guild).restart_role_id.set(role.id)
        await self._touch(ctx)
        await self._send_or_reply(ctx, f"✅ Restart ping role set to {role.mention}.", allowed_mentions=discord.AllowedMentions.none())

    @server_group.command(name="restartchannel")
    @commands.mod_or_permissions(manage_guild=True)
    async def restartchannel(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Set or clear the channel used by /server restart. Moderator only."""
        if channel is None:
            await self.config.guild(ctx.guild).restart_channel_id.set(None)
            await self._touch(ctx)
            return await self._send_or_reply(ctx, "✅ Restart notification channel cleared. Restart pings will use the current channel.")
        await self.config.guild(ctx.guild).restart_channel_id.set(channel.id)
        await self._touch(ctx)
        await self._send_or_reply(ctx, f"✅ Restart notification channel set to {channel.mention}.")

    @server_group.command(name="restart")
    @commands.mod_or_permissions(manage_guild=True)
    async def restart(self, ctx: commands.Context, *, reason: Optional[str] = None):
        """Notify the configured role that the server is restarting. Moderator only."""
        if ctx.guild is None:
            return await self._send_or_reply(ctx, "This command can only be used in a server.")
        data = await self.config.guild(ctx.guild).all()
        role = ctx.guild.get_role(data.get("restart_role_id")) if data.get("restart_role_id") else None
        channel = ctx.guild.get_channel(data.get("restart_channel_id")) if data.get("restart_channel_id") else ctx.channel

        await self.config.guild(ctx.guild).status.set("Restarting")
        await self._touch(ctx)

        embed = discord.Embed(
            title="🔄 SIN Corp Server Restart",
            description="The current game server is being restarted. Please save your chaos and prepare for a short interruption.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )
        if data.get("game"):
            embed.add_field(name="🎮 Game", value=data["game"], inline=True)
        if data.get("server_name"):
            embed.add_field(name="🏷️ Server", value=data["server_name"], inline=True)
        if reason:
            embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.set_footer(text=f"Restart notice sent by {ctx.author.display_name}")

        content = role.mention if role else None
        await channel.send(content=content, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        if channel.id != ctx.channel.id:
            await self._send_or_reply(ctx, f"✅ Restart notification sent in {channel.mention}.")

    @server_group.command(name="clear")
    @commands.mod_or_permissions(manage_guild=True)
    async def clear(self, ctx: commands.Context):
        """Clear the active server listing. Moderator only."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await self._touch(ctx)
        await self._send_or_reply(ctx, "✅ SIN Corp server listing cleared.")

    @server_group.command(name="config")
    @commands.mod_or_permissions(manage_guild=True)
    async def config_view(self, ctx: commands.Context):
        """Show current restart notification configuration. Moderator only."""
        data = await self.config.guild(ctx.guild).all()
        role = ctx.guild.get_role(data.get("restart_role_id")) if data.get("restart_role_id") else None
        channel = ctx.guild.get_channel(data.get("restart_channel_id")) if data.get("restart_channel_id") else None
        embed = discord.Embed(title="⚙️ SIN Server Hub Config", color=discord.Color.purple())
        embed.add_field(name="Restart Role", value=role.mention if role else "Not set", inline=False)
        embed.add_field(name="Restart Channel", value=channel.mention if channel else "Current channel", inline=False)
        await self._send_or_reply(ctx, embed=embed, allowed_mentions=discord.AllowedMentions.none())
