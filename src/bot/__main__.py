from bot.bot import RussianRoulette

if __name__ == "__main__":
    bot = RussianRoulette()
    bot.run(bot.settings.discord_token)
