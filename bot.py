from discord import Activity, Intents
from discord.ext.commands import Bot, when_mentioned_or

from config import config


class RussianRoulette(Bot):
    def __init__(self):
        super().__init__(
            command_prefix=when_mentioned_or(*config.prefixes),
            intents=Intents(guilds=True, messages=True),
            activity=Activity(name=config.activity.text, type=config.activity.type),
            case_insensitive=True,
            strip_after_prefix=True,
        )

    async def setup_hook(self):
        await self.load_extension("core")
        await self.load_extension("game")
        # await self.tree.sync()


if __name__ == "__main__":
    bot = RussianRoulette()
    bot.run(config.token)
