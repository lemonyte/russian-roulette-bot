from bot.bot import RussianRoulette
from bot.config import config

if __name__ == "__main__":
    bot = RussianRoulette()
    bot.run(config.token)
