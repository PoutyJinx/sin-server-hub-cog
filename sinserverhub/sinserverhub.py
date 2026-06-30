import discord
from redbot.core import commands, Config, app_commands
from redbot.core.bot import Red


class SinServerHub(commands.Cog):
    """SIN Corp Server Hub: manual game server info board."""

    __author__ = "Jinx / NODE-13"
    __version__ = "1.0.0"

    VALID_STATUSES = {
        "online": ("🟢", "Online"),
        "offline": ("🔴", "Offline"),
        "maintenance": ("🟡", "Maintenance"),
        "unknown": ("⚫", "Unknown"),
    }

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=918273645001, force_registration=True)
        default_guild = {
            "enabled": False,
            "game": None,
            "server_name": None,
            "ip": None,
            "password": None,
            "status": "unknown",
            "slots": None,
            "workshop": None,
            "notes": None,
            "join_instructions": None,
            "last_updated_by": None,
            "last_updated_at": None,
        }
        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        """No user data is stored globally."""
        return

    async def _is_mod_or_admin(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return False
        if interaction.user.guild_permissions.manage_guild or interaction.user.guild_permissions.administrator:
            return True
        try:
            return await self.bot.is_mod(interaction.user)
        except Exception:
            return False

    def _format_password(self, password: str | None) -> str:
        if not password:
            return "No password set"
        clean = password.strip()
        if clean.startswith("||") and clean.endswith("||"):
            return clean
        return f"||{clean}||"

    def _format_status(self, status: str | None) -> str:
        key = (status or "unknown").lower()
        emoji, label = self.VALID_STATUSES.get(key, self.VALID_STATUSES["unknown"])
        return f"{emoji} **{label}**"

    async def _build_embed(self, guild: discord.Guild) -> discord.Embed:
        data = await self.config.guild(guild).all()

        status_text = self._format_status(data.get("status"))
        title = data.get("server_name") or "SIN Corp Server Hub"
        game = data.get("game") or "No game set"

        embed = discord.Embed(
            title="🏰 SIN Corp Server Hub",
            description=f"**{title}**\nCurrent game server information for the Dwellers.",
            color=discord.Color.purple(),
        )
        embed.add_field(name="Status", value=status_text, inline=True)
        embed.add_field(name="Game", value=game, inline=True)
        embed.add_field(name="Slots", value=data.get("slots") or "Not listed", inline=True)
        embed.add_field(name="IP / Address", value=f"`{data.get('ip')}`" if data.get("ip") else "No IP set", inline=False)
        embed.add_field(name="Password", value=self._format_password(data.get("password")), inline=False)

        if data.get("workshop"):
            embed.add_field(name="📦 Workshop / Modpack", value=data["workshop"], inline=False)
        if data.get("join_instructions"):
            embed.add_field(name="🚪 Join Instructions", value=data["join_instructions"][:1024], inline=False)
        if data.get("notes"):
            embed.add_field(name="📝 Notes", value=data["notes"][:1024], inline=False)

        footer_bits = []
        if data.get("last_updated_by"):
            footer_bits.append(f"Updated by {data['last_updated_by']}")
        if data.get("last_updated_at"):
            footer_bits.append(data["last_updated_at"])
        footer = " • ".join(footer_bits) if footer_bits else "Use /server set to configure this board."
        embed.set_footer(text=footer)
        return embed

    async def _stamp_update(self, interaction: discord.Interaction):
        await self.config.guild(interaction.guild).last_updated_by.set(str(interaction.user))
        await self.config.guild(interaction.guild).last_updated_at.set(discord.utils.utcnow().strftime("%Y-%m-%d %H:%M UTC"))

    server = app_commands.Group(name="server", description="SIN Corp Server Hub commands")

    @server.command(name="show", description="Show the current SIN Corp server information.")
    async def slash_server_show(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
            return
        data = await self.config.guild(interaction.guild).all()
        if not data.get("enabled"):
            await interaction.response.send_message(
                "No SIN Corp server is currently listed. A moderator can set one with `/server set`.",
                ephemeral=True,
            )
            return
        embed = await self._build_embed(interaction.guild)
        await interaction.response.send_message(embed=embed)

    @server.command(name="set", description="Set or update the active SIN Corp server board. Moderator only.")
    @app_commands.describe(
        game="Game name, for example Project Zomboid",
        server_name="Display name of the server",
        ip="Server IP or join address",
        password="Server password. It will be shown as a spoiler.",
        status="online, offline, maintenance, or unknown",
        slots="Optional player slots, for example 16 Players",
        workshop="Optional Steam Workshop/modpack link",
        notes="Optional notes for players",
        join_instructions="Optional instructions for joining",
    )
    async def slash_server_set(
        self,
        interaction: discord.Interaction,
        game: str,
        server_name: str,
        ip: str,
        password: str | None = None,
        status: str = "unknown",
        slots: str | None = None,
        workshop: str | None = None,
        notes: str | None = None,
        join_instructions: str | None = None,
    ):
        if not await self._is_mod_or_admin(interaction):
            await interaction.response.send_message("Only moderators can update the SIN Server Hub.", ephemeral=True)
            return

        status_key = status.lower().strip()
        if status_key not in self.VALID_STATUSES:
            await interaction.response.send_message("Status must be: online, offline, maintenance, or unknown.", ephemeral=True)
            return

        async with self.config.guild(interaction.guild).all() as data:
            data["enabled"] = True
            data["game"] = game
            data["server_name"] = server_name
            data["ip"] = ip
            data["password"] = password
            data["status"] = status_key
            data["slots"] = slots
            data["workshop"] = workshop
            data["notes"] = notes
            data["join_instructions"] = join_instructions
        await self._stamp_update(interaction)

        embed = await self._build_embed(interaction.guild)
        await interaction.response.send_message("SIN Server Hub updated.", embed=embed)

    @server.command(name="status", description="Update only the server status. Moderator only.")
    @app_commands.describe(status="online, offline, maintenance, or unknown")
    async def slash_server_status(self, interaction: discord.Interaction, status: str):
        if not await self._is_mod_or_admin(interaction):
            await interaction.response.send_message("Only moderators can update the SIN Server Hub.", ephemeral=True)
            return
        status_key = status.lower().strip()
        if status_key not in self.VALID_STATUSES:
            await interaction.response.send_message("Status must be: online, offline, maintenance, or unknown.", ephemeral=True)
            return
        await self.config.guild(interaction.guild).status.set(status_key)
        await self.config.guild(interaction.guild).enabled.set(True)
        await self._stamp_update(interaction)
        await interaction.response.send_message(f"Server status set to {self._format_status(status_key)}.", ephemeral=True)

    @server.command(name="notes", description="Update only the notes field. Moderator only.")
    async def slash_server_notes(self, interaction: discord.Interaction, notes: str):
        if not await self._is_mod_or_admin(interaction):
            await interaction.response.send_message("Only moderators can update the SIN Server Hub.", ephemeral=True)
            return
        await self.config.guild(interaction.guild).notes.set(notes)
        await self.config.guild(interaction.guild).enabled.set(True)
        await self._stamp_update(interaction)
        await interaction.response.send_message("Server notes updated.", ephemeral=True)

    @server.command(name="workshop", description="Update only the workshop/modpack link. Moderator only.")
    async def slash_server_workshop(self, interaction: discord.Interaction, link: str):
        if not await self._is_mod_or_admin(interaction):
            await interaction.response.send_message("Only moderators can update the SIN Server Hub.", ephemeral=True)
            return
        await self.config.guild(interaction.guild).workshop.set(link)
        await self.config.guild(interaction.guild).enabled.set(True)
        await self._stamp_update(interaction)
        await interaction.response.send_message("Workshop/modpack link updated.", ephemeral=True)

    @server.command(name="password", description="Update only the password. Moderator only.")
    async def slash_server_password(self, interaction: discord.Interaction, password: str):
        if not await self._is_mod_or_admin(interaction):
            await interaction.response.send_message("Only moderators can update the SIN Server Hub.", ephemeral=True)
            return
        await self.config.guild(interaction.guild).password.set(password)
        await self.config.guild(interaction.guild).enabled.set(True)
        await self._stamp_update(interaction)
        await interaction.response.send_message("Server password updated and will be shown as a spoiler.", ephemeral=True)

    @server.command(name="instructions", description="Update only the join instructions. Moderator only.")
    async def slash_server_instructions(self, interaction: discord.Interaction, instructions: str):
        if not await self._is_mod_or_admin(interaction):
            await interaction.response.send_message("Only moderators can update the SIN Server Hub.", ephemeral=True)
            return
        await self.config.guild(interaction.guild).join_instructions.set(instructions)
        await self.config.guild(interaction.guild).enabled.set(True)
        await self._stamp_update(interaction)
        await interaction.response.send_message("Join instructions updated.", ephemeral=True)

    @server.command(name="clear", description="Clear the current server board. Moderator only.")
    async def slash_server_clear(self, interaction: discord.Interaction):
        if not await self._is_mod_or_admin(interaction):
            await interaction.response.send_message("Only moderators can clear the SIN Server Hub.", ephemeral=True)
            return
        await self.config.guild(interaction.guild).clear()
        await interaction.response.send_message("SIN Server Hub cleared.", ephemeral=True)

    # Prefix fallback commands, because Red bots like having both claws and teeth.
    @commands.group(name="sinserver", aliases=["serverhub"], invoke_without_command=True)
    async def prefix_sinserver(self, ctx: commands.Context):
        """Show the current SIN Corp server information."""
        data = await self.config.guild(ctx.guild).all()
        if not data.get("enabled"):
            await ctx.send("No SIN Corp server is currently listed. A moderator can set one with `/server set`.")
            return
        embed = await self._build_embed(ctx.guild)
        await ctx.send(embed=embed)

    @prefix_sinserver.command(name="clear")
    @commands.mod_or_permissions(manage_guild=True)
    async def prefix_sinserver_clear(self, ctx: commands.Context):
        """Clear the current server board."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("SIN Server Hub cleared.")
