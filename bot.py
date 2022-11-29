from discord import Game, Intents
from discord.ext.commands import Bot

from config import config


class RussianRoulette(Bot):
    def __init__(self):
        activity = Game(r"is 83.3% safe!")
        super().__init__(
            command_prefix=config.prefixes,
            intents=Intents(guilds=True),
            activity=activity,
            case_insensitive=True,
            strip_after_prefix=True,
        )

    async def setup_hook(self):
        await self.load_extension('core')
        await self.load_extension('game')
        # await self.tree.sync()


if __name__ == '__main__':
    bot = RussianRoulette()
    bot.run(config.discord_token)
