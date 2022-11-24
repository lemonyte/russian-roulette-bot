from discord import app_commands, Embed, Interaction
from discord.ext.commands import Bot, Cog

import utils
from utils import channel_bound


class Core(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        prefixes = utils.DEFAULT_PREFIXES
        if self.bot.user.mention not in prefixes:
            prefixes.append(self.bot.user.mention)
        if f'<@!{self.bot.user.id}>' not in prefixes:
            prefixes.append(f'<@!{self.bot.user.id}>')
        utils.DEFAULT_PREFIXES = prefixes
        utils.update_guilds(self.bot)
        print(f"Startup complete - logged in as {self.bot.user}")

    @Cog.listener()
    async def on_guild_join(self, guild):
        utils.update_guilds(self.bot)

    @Cog.listener()
    async def on_guild_remove(self, guild):
        guilds = utils.get_guilds()
        del guilds[str(guild.id)]
        utils.set_guilds(guilds)

    @app_commands.command()
    @channel_bound
    async def about(self, interaction: Interaction):
        with open(utils.markdown_path('about'), 'r') as about_file:
            about = about_file.read()
        embed = Embed(title=utils.TITLE, description=about, color=0xff0000, url=utils.URL)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @channel_bound
    async def rules(self, interaction: Interaction):
        with open(utils.markdown_path('rules'), 'r') as rules_file:
            rules = rules_file.read()
        embed = Embed(title=f"{utils.TITLE} Rules", description=rules, color=0xff0000, url=utils.URL)
        await interaction.response.send_message(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Core(bot))
