from discord import Activity, Intents
from discord.ext.commands import Bot, when_mentioned_or

from bot.settings import Settings


class RussianRoulette(Bot):
    def __init__(self) -> None:
        self.settings = Settings.model_validate({})
        super().__init__(
            command_prefix=when_mentioned_or(*self.settings.prefixes),
            intents=Intents(guilds=True, messages=True),
            activity=Activity(name=self.settings.activity.text, type=self.settings.activity.type),
            case_insensitive=True,
            strip_after_prefix=True,
        )

    async def setup_hook(self) -> None:
        await self.load_extension("bot.modules.core")
        await self.load_extension("bot.modules.game")
