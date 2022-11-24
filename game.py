import random
import datetime
import functools
from discord import Embed, File
from discord.ext.commands import Bot, Cog, Context, command, group
import utils


class Game(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.players = []
        self.channel = None
        self.info = None
        self.duration = None
        self.current_player = None
        self.game_started = False
        self.image_size = '128'
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

    def game_command(func):
        @functools.wraps(func)
        async def decorator(self, ctx: Context, *args, **kwargs):
            if self.game_started:
                await func(self, ctx, *args, **kwargs)
            else:
                await ctx.reply("No game started.", mention_author=False)
        return decorator

    @command(aliases=['startgame', 'start-game', 'new', 'newgame', 'new-game'])
    async def start(self, ctx: Context):
        if self.game_started:
            await ctx.reply("Game already started.", mention_author=False)
            return
        if len(ctx.message.mentions) < 2:
            await ctx.reply("Must have at least 2 players to start a game.", mention_author=False)
            return
        opts = utils.parse_command(ctx.message.content)
        if 'info' in opts.keys():
            self.info = ' '.join(opts['info'])
        if 'duration' in opts.keys():
            try:
                self.duration = utils.parse_time(''.join(opts['duration']))
            except ValueError as exc:
                await ctx.reply(exc.args[0], mention_author=False)
                return
        self.channel = ctx.channel
        self.players = ctx.message.mentions
        self.current_player = self.players[0]
        self.game_started = True
        await ctx.reply(f"Started a new game with {' '.join(player.mention for player in self.players)}.", mention_author=False)
        if self.bot.user.id == self.current_player.id:
            await self.shoot(ctx, self.bot.user)

    @command(aliases=['cancelgame', 'cancel-game', 'stop', 'stopgame', 'stop-game', 'end', 'endgame', 'end-game'])
    @game_command
    async def cancel(self, ctx: Context):
        self.game_started = False
        self.players = []
        self.channel = None
        self.info = None
        self.duration = None
        self.current_player = None
        await ctx.reply("Stopped the current game.", mention_author=False)

    @command(aliases=['current-game', 'currentgame', 'game-info', 'gameinfo '])
    @game_command
    async def current(self, ctx: Context):
        response = (
            "**Current game info**:\n"
            f"Players: {' '.join(player.mention for player in self.players)}\n"
            f"Info: {self.info}\n"
            f"Duration: {self.duration}\n"
            f"Channel: {self.channel.mention}"
        )
        embed = Embed(title=utils.TITLE, description=response, color=0xff0000, url=utils.URL)
        await ctx.reply(embed=embed, mention_author=False)

    @command(aliases=['fire', 'go', 'spin', 'pull'])
    @game_command
    async def shoot(self, ctx: Context, player=None):
        if ctx.channel != self.channel:
            await ctx.reply(f"This game was started in the {self.channel} channel.", mention_author=False)
            return
        if player is None:
            player = ctx.message.author
        if player != self.current_player:
            await ctx.reply(f"It's {self.current_player.mention}'s turn.", mention_author=False)
            return
        n = random.randint(1, 6)
        file = File(utils.frame_path(n, self.image_size), 'thumbnail.png')
        if n == 1:
            response = random.choice(self.death_messages).format(user=player.display_name)
            embed = Embed(title=utils.TITLE, description=response, color=0xff0000, url=utils.URL)
            embed.set_thumbnail(url='attachment://thumbnail.png')
            await ctx.reply(embed=embed, file=file, mention_author=False)
            if self.info is not None:
                response = f"{player.mention} {self.info}."
                if self.duration is not None:
                    duration_end = datetime.datetime.utcnow() + self.duration
                    response += f"\nYour timer ends at {duration_end.strftime('%Y-%m-%d %I:%M:%S %p')} UTC."
                message = await ctx.reply(response, mention_author=False)
                await message.pin()
            self.game_started = False
            self.players = []
            self.channel = None
            self.info = None
            self.duration = None
            self.current_player = None
        else:
            response = random.choice(self.luck_messages).format(user=player.display_name)
            embed = Embed(title=utils.TITLE, description=response, color=0xff0000, url=utils.URL)
            embed.set_thumbnail(url='attachment://thumbnail.png')
            await ctx.reply(embed=embed, file=file, mention_author=False)
            self.players.append(self.players.pop(0))
            self.current_player = self.players[0]
            if self.bot.user.id == self.current_player.id:
                await self.shoot(ctx, self.bot.user)

    @command()
    async def gif(self, ctx: Context):
        await ctx.reply(file=File(utils.GIF_PATH), mention_author=False)

    @group(aliases=['players'])
    async def player(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await self.player_list(ctx)

    @player.command(name='list')
    @game_command
    async def player_list(self, ctx: Context):
        await ctx.reply(f"Players in current game: {' '.join(player.mention for player in self.players)}", mention_author=False)

    @player.command(name='add')
    @game_command
    async def player_add(self, ctx: Context):
        players = ctx.message.mentions
        self.players.extend([player for player in players if player not in self.players])
        await ctx.reply(f"Added {' '.join(player.mention for player in players)} to the current game.", mention_author=False)

    @player.command(name='remove')
    @game_command
    async def player_remove(self, ctx: Context):
        players = ctx.message.mentions
        if len(self.players) <= 2:
            await ctx.reply("Cannot have less than 2 players in a game.", mention_author=False)
            return
        for player in players:
            while player in self.players:
                self.players.remove(player)
        self.current_player = self.players[0]
        await ctx.reply(f"Removed {' '.join(player.mention for player in players)} from the current game.", mention_author=False)


async def setup(bot: Bot):
    await bot.add_cog(Game(bot))
