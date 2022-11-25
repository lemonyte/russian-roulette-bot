from discord import app_commands, Embed, Interaction
from discord.ext.commands import Bot, Cog

import utils


class Core(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print(f"Startup complete - logged in as {self.bot.user}")

    @app_commands.command()
    async def about(self, interaction: Interaction):
        with open(utils.markdown_path('about'), 'r') as about_file:
            about = about_file.read()
        embed = Embed(title=utils.TITLE, description=about, color=0xff0000, url=utils.URL)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def rules(self, interaction: Interaction):
        with open(utils.markdown_path('rules'), 'r') as rules_file:
            rules = rules_file.read()
        embed = Embed(title=f"{utils.TITLE} Rules", description=rules, color=0xff0000, url=utils.URL)
        await interaction.response.send_message(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Core(bot))
