import random
import datetime
from discord import Member, Embed, File, TextChannel
from discord.ext.commands import Context
import utils


class Game:
    def __init__(self, players: list[Member], channel: TextChannel, info: str = None, duration: str = None, image_size: str = '128'):
        self.players = players
        self.channel = channel
        self.info = info
        self.duration = duration
        self.image_size = image_size
        if self.duration is not None:
            self.duration = utils.parse_time(self.duration)
        self.luck_messages = [
            "{user} got lucky.",
            "{user} is having a good day.",
            "{user} lives on to the next round.",
            "{user} survived the odds.",
            "{user} rigged the game."
        ]
        self.death_messages = [
            "{user} wasn't lucky enough.",
            "{user} took too many chances.",
            "{user} took one for the team.",
            "{user} lost the game, and their life.",
            "{user} left their brains behind."
        ]
        self.current_player = self.players[0]

    async def add_players(self, ctx: Context, players: list[Member]):
        self.players.extend([player for player in players if player not in self.players])
        await ctx.reply(f"Added {', '.join(player.mention for player in players)} to the current game.", mention_author=False)

    async def remove_players(self, ctx: Context, players: list[Member]):
        if len(self.players) <= 2:
            await ctx.reply("Cannot have less than 2 players in a game.", mention_author=False)
            return
        for player in players:
            while player in self.players:
                self.players.remove(player)
        self.current_player = self.players[0]
        await ctx.reply(f"Removed {', '.join(player.mention for player in players)} from the current game.", mention_author=False)

    async def turn(self, ctx: Context) -> bool:
        if ctx.channel != self.channel:
            await ctx.reply(f"This game was started in the {self.channel} channel.", mention_author=False)
            return
        if ctx.author != self.current_player:
            await ctx.reply(f"It's {self.current_player.mention}'s turn.", mention_author=False)
            return
        n = random.randint(1, 6)
        file = File(utils.frame_path(n, self.image_size), 'thumbnail.png')
        if n == 1:
            response = random.choice(self.death_messages).format(user=ctx.message.author.display_name)
            embed = Embed(title=utils.TITLE, description=response, color=0xff0000, url=utils.URL)
            embed.set_thumbnail(url='attachment://thumbnail.png')
            await ctx.reply(embed=embed, file=file, mention_author=False)
            if self.info is not None:
                response = f"{ctx.message.author.mention} {self.info}."
                if self.duration is not None:
                    duration_end = datetime.datetime.utcnow() + self.duration
                    response += f"\nYour timer ends at {duration_end.strftime('%Y-%m-%d %I:%M:%S %p')} UTC."
                message = await ctx.reply(response, mention_author=False)
                await message.pin()
            return False
        else:
            response = random.choice(self.luck_messages).format(user=ctx.message.author.display_name)
            embed = Embed(title=utils.TITLE, description=response, color=0xff0000, thumbnail='attachment://thumbnail.png', url=utils.URL)
            embed.set_thumbnail(url='attachment://thumbnail.png')
            await ctx.reply(embed=embed, file=file, mention_author=False)
            self.players.append(self.players.pop(0))
            self.current_player = self.players[0]
            return True
