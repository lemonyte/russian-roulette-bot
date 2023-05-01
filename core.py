# pyright: reportOptionalMemberAccess=false

import sys
from datetime import datetime, timedelta

import discord
from discord import Embed, Interaction, app_commands
from discord.ext.commands import Bot, Cog

from config import config


class Core(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.start_time = datetime.utcnow()

    @Cog.listener()
    async def on_ready(self):
        print(f"Startup complete - logged in as {self.bot.user}")

    @app_commands.command()
    async def ping(self, interaction: Interaction):
        """Check the bot's latency."""
        await interaction.response.send_message(f"Pong! Latency is `{round(self.bot.latency * 1000)}ms`")

    @app_commands.command()
    async def invite(self, interaction: Interaction):
        """Get an invite link for the bot."""
        await interaction.response.send_message(f"Invite me to your server: {config.invite}")

    @app_commands.command()
    async def debug(self, interaction: Interaction):
        """Show debug information."""
        uptime = timedelta(seconds=int((datetime.utcnow() - self.start_time).total_seconds()))
        description = f"""
        **General**
        ```
        Name: {self.bot.user}
        ID: {self.bot.application_id}
        Preview: {config.preview}
        Command prefixes: {', '.join(config.prefixes + [self.bot.user.mention])}
        URL: {config.url}
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
        Cogs: {', '.join(self.bot.cogs)}
        Flags value: {self.bot.application_flags.value}
        ```
        """
        description = "\n".join(line.strip() for line in description.splitlines())
        embed = Embed(title="Debug Info", description=description, color=config.color, url=config.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def about(self, interaction: Interaction):
        """Show information about the bot."""
        with open("assets/markdown/about.md", "r") as about_file:
            about = about_file.read()
        embed = Embed(title=f"About {config.name}", description=about, color=config.color, url=config.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def rules(self, interaction: Interaction):
        """Show the rules of the game."""
        with open("assets/markdown/rules.md", "r") as rules_file:
            rules = rules_file.read()
        embed = Embed(title=f"{config.name} Rules", description=rules, color=config.color, url=config.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Core(bot))
