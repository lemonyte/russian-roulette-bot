import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix=['rr', 'russian-roulette'], case_insensitive=True, strip_after_prefix=True)


@bot.event
async def on_ready():
    bot.command_prefix.append(bot.user.mention)
    for attr in dir(bot):
        if not attr.startswith('_') and not callable(getattr(bot, attr)):
            print(f"{attr}\t\t{getattr(bot, attr)}")


@bot.command()
async def context(ctx: commands.Context):
    response = [f'{x}: {getattr(ctx, x)}' for x in dir(ctx) if not x.startswith('_') and not callable(getattr(ctx, x))]
    response.insert(0, "Context:")
    await ctx.send('\n'.join(response))


@bot.command()
async def about(ctx: commands.Context):
    message = [f'{x}: {getattr(bot, x)}' for x in dir(bot) if not x.startswith('_') and not callable(getattr(bot, x))]
    message.insert(0, "Bot:")
    await ctx.send('\n'.join(message))

if __name__ == '__main__':
    bot.run(TOKEN)
