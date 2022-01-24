from discord import Guild, File, Embed
from discord.ext import commands
from discord.ext.commands import Context, Bot, has_permissions
import utils
from utils import channel_bound
from game import Game


bot = Bot(command_prefix=utils.get_prefixes, case_insensitive=True, strip_after_prefix=True)
current_game: Game = None


@bot.event
async def on_ready():
    prefixes = utils.DEFAULT_PREFIXES
    if bot.user.mention not in prefixes:
        prefixes.append(bot.user.mention)
    if f'<@!{bot.user.id}>' not in prefixes:
        prefixes.append(f'<@!{bot.user.id}>')
    utils.DEFAULT_PREFIXES = prefixes
    utils.update_guilds(bot)


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


@bot.command()
@channel_bound
async def gif(ctx: Context):
    await ctx.reply(file=File(utils.GIF_PATH), mention_author=False)


@bot.group(aliases=['prefixes'])
@channel_bound
async def prefix(ctx: Context):
    if ctx.invoked_subcommand is None:
        await prefix_list(ctx)


@prefix.command(name='list')
@channel_bound
async def prefix_list(ctx: Context):
    await ctx.reply(f"Prefixes: **`{', '.join(utils.get_prefixes(ctx.guild))}`**", mention_author=False)


@prefix.command(name='add')
@has_permissions(administrator=True)
@channel_bound
async def prefix_add(ctx: Context, prefix: str = None):
    if prefix is None:
        await ctx.reply("Please specify a prefix to add.", mention_author=False)
    prefixes = utils.get_prefixes(ctx.guild)
    if prefix in prefixes:
        await ctx.reply("Prefix is already added.", mention_author=False)
        return
    prefixes.append(prefix)
    utils.set_prefixes(ctx.guild, prefixes)
    await ctx.reply(f"Added prefix **`{prefix}`**.", mention_author=False)


@prefix.command(name='remove')
@has_permissions(administrator=True)
@channel_bound
async def prefix_remove(ctx: Context, prefix: str = None):
    if prefix is None:
        ctx.reply("Please specify a prefix to remove.", mention_author=False)
    prefixes = utils.get_prefixes(ctx.guild)
    if len(prefixes) <= 2:
        await ctx.reply("Cannot have less than 2 prefixes.", mention_author=False)
        return
    if prefix in prefixes:
        prefixes.remove(prefix)
    else:
        await ctx.reply("Cannot remove prefix that does not exist.", mention_author=False)
        return
    utils.set_prefixes(ctx.guild, prefixes)
    await ctx.reply(f"Removed prefix **`{prefix}`**.", mention_author=False)


@bot.group(aliases=['channels'])
@channel_bound
async def channel(ctx: Context):
    if ctx.invoked_subcommand is None:
        await channel_list(ctx)


@channel.command(name='list')
@channel_bound
async def channel_list(ctx: Context):
    await ctx.reply(f"Bound channels: {', '.join(f'<#{channel}>' for channel in utils.get_channels(ctx.guild))}", mention_author=False)


@channel.command(name='bind', aliases=['add'])
@has_permissions(administrator=True)
@channel_bound
async def channel_bind(ctx: Context):
    channels = utils.get_channels(ctx.guild)
    if ctx.message.channel_mentions:
        for channel in ctx.message.channel_mentions:
            if channel.id not in channels:
                channels.append(channel.id)
    else:
        channel = ctx.channel
        if channel.id not in channels:
            channels.append(channel.id)
            await ctx.reply(f"Bound to channel {channel.mention}.", mention_author=False)
        else:
            await ctx.reply("Channel is already bound.", mention_author=False)
            return
    utils.set_channels(ctx.guild, channels)


@channel.command(name='unbind', aliases=['remove'])
@has_permissions(administrator=True)
@channel_bound
async def channel_unbind(ctx: Context):
    channels = utils.get_channels(ctx.guild)
    if ctx.message.channel_mentions:
        for channel in ctx.message.channel_mentions:
            if channel.id in channels:
                channels.remove(channel.id)
    else:
        channel = ctx.channel
        if channel.id in channels:
            channels.remove(channel.id)
            await ctx.reply(f"Unbound from channel {channel.mention}.", mention_author=False)
        else:
            await ctx.reply("Cannot unbind from channel that is not bound.")
            return
    utils.set_channels(ctx.guild, channels)


@bot.group(aliases=['players'])
@channel_bound
async def player(ctx: Context):
    if ctx.invoked_subcommand is None:
        await player_list(ctx)


@player.command(name='list')
@channel_bound
async def player_list(ctx: Context):
    global current_game
    if current_game is None:
        await ctx.reply("No game started.", mention_author=False)
        return
    await ctx.reply(f"Players in current game: {', '.join(player.mention for player in current_game.players)}", mention_author=False)


@player.command(name='add')
@channel_bound
async def player_add(ctx: Context):
    global current_game
    if current_game is None:
        await ctx.reply("No game started.", mention_author=False)
        return
    await current_game.add_players(ctx, ctx.message.mentions)


@player.command(name='remove')
@channel_bound
async def player_remove(ctx: Context):
    global current_game
    if current_game is None:
        await ctx.reply("No game started.", mention_author=False)
        return
    await current_game.remove_players(ctx, ctx.message.mentions)


@bot.command(aliases=['startgame', 'start-game', 'new', 'newgame', 'new-game'])
@channel_bound
async def start(ctx: Context):
    global current_game
    if current_game is not None:
        await ctx.reply("Game already started.", mention_author=False)
        return
    if len(ctx.message.mentions) < 2:
        await ctx.reply("Must have at least 2 players to start a game.", mention_author=False)
        return
    opts = utils.parse_command(ctx.message.content)
    if 'info' in opts.keys():
        opts['info'] = ' '.join(opts['info'])
    if 'duration' in opts.keys():
        opts['duration'] = ''.join(opts['duration'])
    opts['players'] = ctx.message.mentions
    current_game = Game(**opts, channel=ctx.channel)
    await ctx.reply(f"Started a new game with {', '.join(player.mention for player in ctx.message.mentions)}.", mention_author=False)


@bot.command(aliases=['cancelgame', 'cancel-game', 'stop', 'stopgame', 'stop-game', 'end', 'endgame', 'end-game'])
@channel_bound
async def cancel(ctx: Context):
    global current_game
    if current_game is None:
        await ctx.reply("No game started.", mention_author=False)
        return
    current_game = None
    await ctx.reply("Stopped the current game.", mention_author=False)


@bot.command(aliases=['current-game', 'currentgame', 'game-info', 'gameinfo '])
@channel_bound
async def current(ctx: Context):
    global current_game
    if current_game is None:
        await ctx.reply("No game started.", mention_author=False)
        return
    response = (
        "**Current game info**:\n"
        f"Players: {', '.join(player.mention for player in current_game.players)}\n"
        f"Info: {current_game.info}\n"
        f"Duration: {current_game.duration}\n"
        f"Channel: {current_game.channel.mention}"
    )
    embed = Embed(title=utils.TITLE, description=response, color=0xff0000, url=utils.URL)
    await ctx.reply(embed=embed, mention_author=False)


@bot.command(aliases=['fire', 'go', 'spin'])
@channel_bound
async def shoot(ctx: Context):
    global current_game
    if current_game is None:
        await ctx.reply("No game started.", mention_author=False)
        return
    alive = await current_game.turn(ctx)
    if alive is False:
        current_game = None


if __name__ == '__main__':
    bot.run(utils.DISCORD_TOKEN)
