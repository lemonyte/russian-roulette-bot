from discord import Activity, Intents
from discord.ext.commands import Bot, when_mentioned_or

from bot.config import config


class RussianRoulette(Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=when_mentioned_or(*config.prefixes),
            intents=Intents(guilds=True, messages=True),
            activity=Activity(name=config.activity.text, type=config.activity.type),
            case_insensitive=True,
            strip_after_prefix=True,
        )

    async def setup_hook(self) -> None:
        await self.load_extension("modules.core")
        await self.load_extension("modules.game")
        # await self.tree.sync()
