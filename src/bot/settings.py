import sys
from collections.abc import Sequence
from enum import IntEnum

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

PREVIEW = "--preview" in sys.argv or "-p" in sys.argv


class ActivityType(IntEnum):
    PLAYING = 0
    STREAMING = 1
    LISTENING = 2
    WATCHING = 3


class ActivitySettings(BaseModel):
    text: str = r"is 83.3% safe!"
    # 0 = playing, 1 = streaming, 2 = listening, 3 = watching
    type: ActivityType = ActivityType.PLAYING


class GameSettings(BaseModel):
    luck_responses: Sequence[str] = (
        "{player} got lucky.",
        "{player} is having a good day.",
        "{player} lives on to the next round.",
        "{player} survived the odds.",
        "{player} rigged the game.",
        "{player} cheated death.",
    )
    death_responses: Sequence[str] = (
        "{player} died.",
        "{player} wasn't lucky enough.",
        "{player} took too many chances.",
        "{player} took one for the team.",
        "{player} lost the game, and their life.",
        "{player} left their brains behind.",
        "{player} hit a dead end.",
        "{player} shot themselves. If this was real life you'd be dead.",
        "RIP {player}.",
    )
    timeout_responses: Sequence[str] = (
        "{player} took too long to decide.",
        "{player} couldn't pull the trigger.",
        "{player} wasn't brave enough.",
    )


class Settings(BaseSettings):
    name: str = "Russian Roulette"
    url: str = "https://github.com/lemonyte/russian-roulette-bot"
    color: int = 0xFF0000
    prefixes: Sequence[str] = ("rr", "russian-roulette")
    invite: str = (
        r"https://discord.com/api/oauth2/authorize?client_id=901284333770383440"
        r"&permissions=412384282688&scope=applications.commands%20bot"
    )
    preview: bool = PREVIEW
    discord_token: str
    activity: ActivitySettings = ActivitySettings()
    game: GameSettings = GameSettings()

    model_config = SettingsConfigDict(
        yaml_file="settings_preview.yaml" if PREVIEW else "settings.yaml",
        env_file=".env",
        env_prefix="preview_" if PREVIEW else "",
        extra="ignore",
    )
