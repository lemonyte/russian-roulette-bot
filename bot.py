import os
import json
import random
import re
import shlex
import datetime
import itertools
# import discord
from discord import Message, Guild, Member, File
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX_FILE_PATH = 'data/prefixes.json'
DEFAULT_PREFIXES = ['rr', 'russian-roulette']
TIME_REGEX = re.compile(r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$')
FRAMES_PATH = 'data/images/frames/{size}x{size}/{frame}.png'
GIF_PATH = 'data/images/spin.gif'


def get_prefixes() -> dict:
    with open(PREFIX_FILE_PATH, 'r') as file:
        prefixes = json.load(file)
    return prefixes


def get_prefixes_for_guild(ctx: Context, message: Message) -> list[str]:
    prefixes = get_prefixes()
    return prefixes.get(str(message.guild.id), DEFAULT_PREFIXES)


def set_prefixes_for_guild(guild: Guild, new_prefixes: list):
    prefixes = get_prefixes()
    prefixes[str(guild.id)] = new_prefixes
    with open(PREFIX_FILE_PATH, 'w') as file:
        json.dump(prefixes, file, indent=4)


def parse_time(time_string: str):
    parts = TIME_REGEX.match(time_string)
    assert parts is not None, f"Could not parse any time information from '{time_string}'.  Examples of valid strings: '8h', '2d8h5m20s', '2m4s'"
    time_params = {name: float(param) for name, param in parts.groupdict().items() if param}
    return datetime.timedelta(**time_params)


class Game:
    def __init__(self, players: list[Member], info: str = None, duration: str = None, image_size: str = '128'):
        self.players = players
        self.info = info
        self.duration = duration
        self.image_size = image_size
        if self.duration is not None:
            self.duration = parse_time(self.duration)
        self.luck_messages = [
            "{user} got lucky.",
            "{user} is having a good day.",
            "{user} lives on to the next round.",
            "{user} survived the odds.",
            "{user} rigged the game."
        ]
        self.death_messages = [
            "{user} wasn't lucky enough.",
            "{user} took too many chances.",
            "{user} took one for the team.",
            "{user} lost the game, and their life.",
            "{user} left their brains behind."
        ]
        self.player_cycle = itertools.cycle(self.players)
        self.current_player = next(self.player_cycle)

    async def turn(self, ctx: Context):
        global current_game
        if ctx.author != self.current_player:
            await ctx.send(f"It's {self.current_player.mention}'s turn")
            return
        n = random.randint(1, 6)
        file = File(FRAMES_PATH.format(frame=str(n), size=self.image_size))
        if n == 1:
            response = random.choice(self.death_messages).format(user=ctx.message.author.display_name)
            if self.info is not None:
                response += '\n' + self.info
            await ctx.send(response, file=file)
            if self.duration is not None:
                duration_end = datetime.datetime.now() + self.duration
                response = await ctx.send(f"{ctx.message.author.mention} your timer ends at {duration_end.strftime('%Y-%m-%d %H:%M:%S')}")
                await response.pin()
            current_game = None
        else:
            response = random.choice(self.luck_messages).format(user=ctx.message.author.display_name)
            await ctx.send(response, file=file)
            self.current_player = next(self.player_cycle)


def parse_command(command: str) -> dict:
    args = shlex.split(command)
    keys = []
    values = []
    for arg in args:
        if arg.endswith(':'):
            keys.append(arg)
    x = []
    for arg in args[args.index(keys[0]) + 1:]:
        if arg not in keys:
            x.append(arg)
        if arg in keys or args.index(arg) == len(args) - 1:
            if x:
                values.append(x)
                x = []
            continue
    opts = {k.strip(':'): v for k, v in zip(keys, values)}
    return opts


current_game: Game = None
bound_channel = None
bot = commands.Bot(command_prefix=get_prefixes_for_guild, case_insensitive=True, strip_after_prefix=True)


@bot.event
async def on_ready():
    DEFAULT_PREFIXES.append(bot.user.mention)
    DEFAULT_PREFIXES.append(f"<@!{bot.user.mention.replace('<', '').replace('>', '').replace('@', '').replace('!', '')}>")


# @bot.event
# async def on_message(message: Message):
#     if message.author == bot.user:
#         return
#     if bot.user.mentioned_in(message):
#         response = f"Hi! I'm the Russian Roulette Bot. My prefixes are: `{', '.join(get_prefixes_for_guild(ctx, ctx.message))}`. For a full list of commands type `rr help`"
#         await message.channel.send(response)


@bot.event
async def on_guild_join(guild: Guild):
    prefixes = get_prefixes()
    prefixes[str(guild.id)] = DEFAULT_PREFIXES
    with open(PREFIX_FILE_PATH, 'w') as file:
        json.dump(prefixes, file, indent=4)


@bot.event
async def on_guild_remove(guild: Guild):
    prefixes = get_prefixes()
    prefixes.pop(str(guild.id), None)
    with open(PREFIX_FILE_PATH, 'w') as file:
        json.dump(prefixes, file, indent=4)


@bot.command(aliases=[''])
async def about(ctx: Context):
    response = f"Hi! I'm the Russian Roulette Bot. My prefixes are: `{', '.join(get_prefixes_for_guild(ctx, ctx.message))}`. For a full list of commands type `rr help`"
    await ctx.send(response)


# @bot.command()
# @commands.has_permissions(administrator=True)
# async def context(ctx: Context, obj: str = ''):
#     obj = getattr(ctx, obj) if obj else ctx
#     response = [f'{attr}: {getattr(obj, attr)}' for attr in dir(obj) if not attr.startswith('_') and not callable(getattr(obj, attr))]
#     response.insert(0, "Context:")
#     await ctx.send('\n'.join(response))


# @bot.command()
# @commands.has_permissions(administrator=True)
# async def self(ctx: Context):
#     message = [f'{x}: {getattr(bot, x)}' for x in dir(bot) if not x.startswith('_') and not callable(getattr(bot, x))]
#     message.insert(0, "Bot:")
#     await ctx.send('\n'.join(message))


# @bot.command()
# async def this(ctx: Context):
#     with open('dump.txt', 'w') as f:
#         f.write(ctx.message.content)
#     print(ctx.message.content)
#     await ctx.send(ctx.message.content)


# @bot.group(pass_context=True)
# async def channel(ctx: Context)


# @channel.command()
# async def bind(ctx: Context, channel: str):
#     global bound_channel
#     bound_channel = channel
#     await ctx.send(f"Successfully bound to channel **`{channel}`**")


# @channel.command()
# async def unbind(ctx: Context, channel: str):


@bot.group(pass_context=True)
async def prefix(ctx: Context):
    if ctx.invoked_subcommand is None:
        await ctx.send("Invalid subcommand")


@prefix.command(name='list')
async def prefix_list(ctx: Context):
    await ctx.send(f"Prefixes: **`{', '.join(get_prefixes_for_guild(ctx, ctx.message))}`**")


@prefix.command(name='add')
@commands.has_permissions(administrator=True)
async def prefix_add(ctx: Context, prefix: str = None):
    if prefix is None:
        ctx.send("Invalid args")
    prefixes = get_prefixes_for_guild(ctx, ctx.message)
    prefixes.append(prefix)
    set_prefixes_for_guild(ctx.guild, prefixes)
    await ctx.send(f'Successfully added the prefix **`{prefix}`**')


@prefix.command(name='remove')
@commands.has_permissions(administrator=True)
async def prefix_remove(ctx: Context, prefix: str = None):
    if prefix is None:
        ctx.send("Invalid args")
    prefixes = get_prefixes_for_guild(ctx, ctx.message)
    if len(prefixes) <= 2:
        await ctx.send("Cannot have less than 2 prefixes")
        return
    prefixes.remove(prefix)
    set_prefixes_for_guild(ctx.guild, prefixes)
    await ctx.send(f'Successfully removed the prefix **`{prefix}`**')


@bot.command()
async def gif(ctx: Context):
    await ctx.send(file=File(GIF_PATH))


# @bot.group(pass_context=True)
# async def players(ctx: Context):
# players list
# players add
# players remove


@bot.command(aliases=['new-game', 'newgame', 'start', 'start-game', 'startgame'])
async def new(ctx: Context):
    global current_game
    opts = parse_command(ctx.message.content)
    if 'info' in opts.keys():
        opts['info'] = ' '.join(opts['info'])
    if 'duration' in opts.keys():
        opts['duration'] = ''.join(opts['duration'])
    opts['players'] = ctx.message.mentions
    current_game = Game(**opts)
    await ctx.send(f"Started a new game with {', '.join(x.display_name for x in ctx.message.mentions)}")


@bot.command()
async def fire(ctx: Context):
    global current_game
    if current_game is None:
        await ctx.send("No game started")
        return
    await current_game.turn(ctx)


if __name__ == '__main__':
    bot.run(TOKEN)
