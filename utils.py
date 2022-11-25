import os
import sys
import re
import datetime
from dotenv import load_dotenv

load_dotenv()

PREVIEW = '-p' in sys.argv or '--preview' in sys.argv
if PREVIEW:
    DEFAULT_PREFIXES = ['rrp', 'russian-roulette-preview']
    FRAME_PATH = 'static/images/png/{size}x{size}/preview/{frame}.png'
    MARKDOWN_PATH = 'static/markdown/{name}.md'
    GIF_PATH = 'static/images/gif/spin.gif'
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN_PREVIEW')
    TITLE = "Russian Roulette [PREVIEW]"
    URL = 'https://github.com/LemonPi314/russian-roulette-bot'
else:
    DEFAULT_PREFIXES = ['rr', 'russian-roulette']
    FRAME_PATH = 'static/images/png/{size}x{size}/{frame}.png'
    MARKDOWN_PATH = 'static/markdown/{name}.md'
    GIF_PATH = 'static/images/gif/spin.gif'
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    TITLE = "Russian Roulette"
    URL = 'https://github.com/LemonPi314/russian-roulette-bot'


def frame_path(frame: int, size: int) -> str:
    return FRAME_PATH.format(frame=str(frame), size=str(size))


def markdown_path(name: str) -> str:
    return MARKDOWN_PATH.format(name=name)


def parse_time(time_string: str, regex: str = None) -> datetime.timedelta:
    if regex:
        regex: re.Pattern = re.compile(regex)
    else:
        regex: re.Pattern = re.compile(r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$')
    parts = regex.match(time_string)
    if parts is None:
        raise ValueError(
            f"Could not parse time information from '{time_string}'. "
            "Examples of valid strings: '16h', '2d8h5m20s', '7m4s'"
        )
    time_params = {name: float(param) for name, param in parts.groupdict().items() if param}
    return datetime.timedelta(**time_params)
