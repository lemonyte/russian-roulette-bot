import os
import sys
import json
import shlex
import re
import datetime
import functools
from dotenv import load_dotenv
from discord import Guild, Message
from discord.ext.commands import Context, Bot

load_dotenv()

PREVIEW = '-p' in sys.argv or '--preview' in sys.argv
if PREVIEW:
    SETTINGS_PATH = 'resources/settings/settings_preview.json'
    DEFAULT_PREFIXES = ['rrp', 'russian-roulette-preview']
    FRAME_PATH = 'resources/images/png/{size}x{size}/preview/{frame}.png'
    MARKDOWN_PATH = 'resources/markdown/{name}.md'
    GIF_PATH = 'resources/images/gif/spin.gif'
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN_PREVIEW')
    TITLE = "Russian Roulette [PREVIEW]"
    URL = 'https://github.com/LemonPi314/russian-roulette-bot'
else:
    SETTINGS_PATH = 'resources/settings/settings.json'
    DEFAULT_PREFIXES = ['rr', 'russian-roulette']
    FRAME_PATH = 'resources/images/png/{size}x{size}/{frame}.png'
    MARKDOWN_PATH = 'resources/markdown/{name}.md'
    GIF_PATH = 'resources/images/gif/spin.gif'
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    TITLE = "Russian Roulette"
    URL = 'https://github.com/LemonPi314/russian-roulette-bot'


def frame_path(frame: int, size: int) -> str:
    return FRAME_PATH.format(frame=str(frame), size=str(size))


def markdown_path(name: str) -> str:
    return MARKDOWN_PATH.format(name=name)


def get_guilds() -> dict:
    with open(SETTINGS_PATH, 'r') as file:
        settings = json.load(file)
    return settings['guilds']


def set_guilds(guilds: dict):
    with open(SETTINGS_PATH, 'r') as file:
        settings = json.load(file)
    settings['guilds'] = guilds
    with open(SETTINGS_PATH, 'w') as file:
        json.dump(settings, file, indent=4)


def get_prefixes(guild: Guild, message: Message = None) -> list[str]:
    if isinstance(guild, Guild):
        id = guild.id
    else:
        id = message.guild.id
    return get_guilds().get(str(id), {}).get('prefixes', DEFAULT_PREFIXES)


def set_prefixes(guild: Guild, prefixes: list[str]):
    guilds = get_guilds()
    guilds[str(guild.id)]['prefixes'] = prefixes
    set_guilds(guilds)


def get_channels(guild: Guild) -> list[int]:
    return get_guilds().get(str(guild.id), {}).get('channels', [])


def set_channels(guild: Guild, channels: list[int]):
    guilds = get_guilds()
    guilds[str(guild.id)]['channels'] = channels
    set_guilds(guilds)


def is_channel_bound(ctx: Context) -> bool:
    channels = get_channels(ctx.guild)
    return ctx.channel.id in channels or not channels


def update_guilds(bot: Bot):
    guilds = get_guilds()
    guild_ids = list(guilds.keys())
    if 'default' in guild_ids:
        guild_ids.remove('default')
    for guild_id in guild_ids:
        guild_obj = bot.get_guild(int(guild_id))
        if not guild_obj:
            guilds.pop(guild_id)
        else:
            guilds[guild_id]['name'] = guild_obj.name
    for guild_obj in bot.guilds:
        if str(guild_obj.id) not in guild_ids:
            guilds[str(guild_obj.id)] = {'name': guild_obj.name}
            set_prefixes(guild_obj, DEFAULT_PREFIXES)
            set_channels(guild_obj, [])
    set_guilds(guilds)


def parse_time(time_string: str, regex: str = None) -> datetime.timedelta:
    if regex:
        regex: re.Pattern = re.compile(regex)
    else:
        regex: re.Pattern = re.compile(r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$')
    parts = regex.match(time_string)
    assert parts is not None, f"Could not parse any time information from '{time_string}'.  Examples of valid strings: '16h', '2d8h5m20s', '7m4s'"
    time_params = {name: float(param) for name, param in parts.groupdict().items() if param}
    return datetime.timedelta(**time_params)


def parse_command(command: str) -> dict:
    args = shlex.split(command)
    keys = []
    values = []
    for arg in args:
        if arg.endswith(':'):
            keys.append(arg)
    if not keys:
        return {}
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


def channel_bound(func):
    @functools.wraps(func)
    async def decorator(ctx: Context, *args, **kwargs):
        if is_channel_bound(ctx):
            await func(ctx, *args, **kwargs)
    return decorator


def preview_command(func):
    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        if PREVIEW:
            await func(*args, **kwargs)
    return decorator
