from discord import Guild, Embed, Intents
from discord.ext import commands
from discord.ext.commands import Context, Bot
import utils
from utils import channel_bound


class RussianRoulette(Bot):
    def __init__(self):
        intents = Intents(
            guilds=True,
            messages=True,
            message_content=True,
        )
        super().__init__(
            command_prefix=utils.get_prefixes,
            intents=intents,
            case_insensitive=True,
            strip_after_prefix=True,
        )

    async def setup_hook(self):
        await self.load_extension('settings')
        await self.load_extension('game')

    async def on_ready(self):
        prefixes = utils.DEFAULT_PREFIXES
        if bot.user.mention not in prefixes:
            prefixes.append(bot.user.mention)
        if f'<@!{bot.user.id}>' not in prefixes:
            prefixes.append(f'<@!{bot.user.id}>')
        utils.DEFAULT_PREFIXES = prefixes
        utils.update_guilds(bot)


bot = RussianRoulette()


@bot.event
async def on_guild_join(guild: Guild):
    utils.update_guilds(bot)


@bot.event
async def on_guild_remove(guild: Guild):
    guilds = utils.get_guilds()
    del guilds[str(guild.id)]
    utils.set_guilds(guilds)


@bot.event
async def on_command_error(ctx: Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


@bot.command(aliases=['', 'info'])
@channel_bound
async def about(ctx: Context):
    prefix = utils.get_prefixes(ctx.guild)[0]
    prefixes = [f'**`{p}`**' if not p.startswith('<') else p for p in utils.get_prefixes(ctx.guild)]
    for p in prefixes:
        if p.startswith('<'):
            prefixes.remove(p)
            break
    prefixes = ', '.join(prefixes)
    with open(utils.markdown_path('about'), 'r') as about_file:
        about = about_file.read().format(prefix=prefix, prefixes=prefixes)
    embed = Embed(title=utils.TITLE, description=about, color=0xff0000, url=utils.URL)
    await ctx.send(embed=embed)


@bot.command()
@channel_bound
async def rules(ctx: Context):
    with open(utils.markdown_path('rules'), 'r') as rules_file:
        rules = rules_file.read()
    embed = Embed(title=f"{utils.TITLE} Rules", description=rules, color=0xff0000, url=utils.URL)
    await ctx.send(embed=embed)


if __name__ == '__main__':
    bot.run(utils.DISCORD_TOKEN)
