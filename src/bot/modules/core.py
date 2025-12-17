# pyright: reportOptionalMemberAccess=false
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord import Embed, Interaction, app_commands
from discord.ext.commands import Cog

MARKDOWN_ASSETS_PATH = Path("assets/markdown")

if TYPE_CHECKING:
    from bot.bot import RussianRoulette


class Core(Cog):
    def __init__(self, bot: RussianRoulette) -> None:
        self.bot = bot
        self.start_time = datetime.now(tz=UTC)

    @Cog.listener()
    async def on_ready(self) -> None:
        print(f"Startup complete - logged in as {self.bot.user}")

    @app_commands.command()
    async def ping(self, interaction: Interaction) -> None:
        """Check the bot's latency."""
        await interaction.response.send_message(f"Pong! Latency is `{round(self.bot.latency * 1000)}ms`")

    @app_commands.command()
    async def sync(self, interaction: Interaction) -> None:
        """Sync commands with Discord."""
        await interaction.response.defer()
        await self.bot.tree.sync()
        await interaction.followup.send("Commands synced!")

    @app_commands.command()
    async def invite(self, interaction: Interaction) -> None:
        """Get an invite link for the bot."""
        await interaction.response.send_message(f"Invite me to your server: {self.bot.settings.invite}")

    @app_commands.command()
    async def debug(self, interaction: Interaction) -> None:
        """Show debug information."""
        if not self.bot.user:
            msg = "not logged in"
            raise RuntimeError(msg)
        uptime = timedelta(seconds=int((datetime.now(tz=UTC) - self.start_time).total_seconds()))
        description = f"""
        **General**
        ```
        Name: {self.bot.user}
        ID: {self.bot.application_id}
        Preview: {self.bot.settings.preview}
        Command prefixes: {", ".join([*self.bot.settings.prefixes, self.bot.user.mention])}
        URL: {self.bot.settings.url}
        ```

        **Network**
        ```
        Uptime: {uptime}
        Latency: {round(self.bot.latency * 1000)}ms
        Gateway: {self.bot.ws.gateway}
        ```

        **Runtime**
        ```
        Python version: {sys.version.split()[0]}
        discord.py version: {discord.__version__} {discord.version_info.releaselevel}
        Cogs: {", ".join(self.bot.cogs)}
        Flags value: {self.bot.application_flags.value}
        ```
        """
        description = "\n".join(line.strip() for line in description.splitlines())
        embed = Embed(
            title="Debug Info",
            description=description,
            color=self.bot.settings.color,
            url=self.bot.settings.url,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def about(self, interaction: Interaction) -> None:
        """Show information about the bot."""
        about = (MARKDOWN_ASSETS_PATH / "about.md").read_text()
        embed = Embed(
            title=f"About {self.bot.settings.name}",
            description=about,
            color=self.bot.settings.color,
            url=self.bot.settings.url,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def rules(self, interaction: Interaction) -> None:
        """Show the rules of the game."""
        rules = (MARKDOWN_ASSETS_PATH / "rules.md").read_text()
        embed = Embed(
            title=f"{self.bot.settings.name} Rules",
            description=rules,
            color=self.bot.settings.color,
            url=self.bot.settings.url,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: RussianRoulette) -> None:
    await bot.add_cog(Core(bot))
