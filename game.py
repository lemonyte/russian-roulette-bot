import random
import re
import datetime
import functools
from typing import Optional

from discord import Embed, File, Interaction, User
from discord.app_commands import command
from discord.ext.commands import Bot, Cog

from config import config


class Game(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.players = []
        self.channel = None
        self.info = None
        self.duration = None
        self.current_player = None
        self.game_started = False

    @staticmethod
    def game_command(func):
        @functools.wraps(func)
        async def decorator(self, interaction: Interaction, *args, **kwargs):
            if self.game_started:
                await func(self, interaction, *args, **kwargs)
            else:
                await interaction.response.send_message("No game started.", ephemeral=True)
        return decorator

    @command()
    async def start(
        self,
        interaction: Interaction,
        player_1: User,  # Temporary workaround while variadic arguments are not supported.
        player_2: User,
        info: Optional[str] = None,
        duration: Optional[str] = None,
    ):
        """Start a new game."""
        if self.game_started:
            await interaction.response.send_message("Game already started.", ephemeral=True)
            return
        # if len(players) < 2:
        #     await interaction.response.send_message("Must have at least 2 players to start a game.", ephemeral=True)
        #     return
        if info:
            self.info = info
        if duration:
            try:
                self.duration = parse_time(duration)
            except ValueError as exc:
                await interaction.response.send_message(exc.args[0], ephemeral=True)
                return
        self.channel = interaction.channel
        # self.players = players
        self.players = [player_1, player_2]
        self.current_player = self.players[0]
        self.game_started = True
        await interaction.response.send_message(f"Started a new game with {' '.join(player.mention for player in self.players)}.")
        # Workaround to manually call the 'shoot' command if the current player is the bot.
        if self.bot.user.id == self.current_player.id:
            # pylint: disable=protected-access, no-member
            await self.shoot._do_call(interaction, {'player': self.current_player})

    @command()
    @game_command
    async def stop(self, interaction: Interaction):
        """Stop the current game."""
        self.game_started = False
        self.players = []
        self.channel = None
        self.info = None
        self.duration = None
        self.current_player = None
        await interaction.response.send_message("Stopped the current game.")

    @command()
    @game_command
    async def current(self, interaction: Interaction):
        """Show information about the current game."""
        response = (
            "**Current game info**:\n"
            f"Players: {' '.join(player.mention for player in self.players)}\n"
            f"Info: {self.info}\n"
            f"Duration: {self.duration}\n"
            f"Channel: {self.channel.mention}"
        )
        embed = Embed(title=config.name, description=response, color=0xff0000, url=config.url)
        await interaction.response.send_message(embed=embed)

    @command()
    @game_command
    async def shoot(self, interaction: Interaction, player: Optional[User] = None):
        """Pull the trigger."""
        # await interaction.response.defer()
        if interaction.channel != self.channel:
            await interaction.response.send_message(f"This game was started in the {self.channel} channel.", ephemeral=True)
            return
        if player is None:
            player = interaction.user
        if player != self.current_player:
            await interaction.response.send_message(f"It's {self.current_player.mention}'s turn.", ephemeral=True)
        n = random.randint(1, 6)
        file = File(f'assets/images/frame_{n}.png', 'thumbnail.png')
        if n == 1:
            response = random.choice(config.game.death_messages).format(player=player.display_name)
            embed = Embed(title=config.name, description=response, color=0xff0000, url=config.url)
            embed.set_thumbnail(url='attachment://thumbnail.png')
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed, file=file)
            if self.info is not None:
                response = f"{player.mention} {self.info}."
                if self.duration is not None:
                    duration_end = datetime.datetime.utcnow() + self.duration
                    response += f"\nYour timer ends at {duration_end.strftime('%Y-%m-%d %I:%M:%S %p')} UTC."
                await interaction.followup.send(response)
            self.game_started = False
            self.players = []
            self.channel = None
            self.info = None
            self.duration = None
            self.current_player = None
        else:
            response = random.choice(config.game.luck_messages).format(player=player.display_name)
            embed = Embed(title=config.name, description=response, color=0xff0000, url=config.url)
            embed.set_thumbnail(url='attachment://thumbnail.png')
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed, file=file)
            self.players.append(self.players.pop(0))
            self.current_player = self.players[0]
            # Workaround to manually call the 'shoot' command if the current player is the bot.
            if self.bot.user.id == self.current_player.id:
                # pylint: disable=protected-access, no-member
                await self.shoot._do_call(interaction, {'player': self.current_player})

    @command()
    async def gif(self, interaction: Interaction):
        """Send a GIF version of the game for screenshotting."""
        await interaction.response.send_message(file=File('assets/images/spin.gif'))

    @command()
    @game_command
    async def listplayers(self, interaction: Interaction):
        """List the players in the current game."""
        await interaction.response.send_message(f"Players in current game: {' '.join(player.mention for player in self.players)}")

    @command()
    @game_command
    # Temporarily only accepts one user.
    async def addplayer(self, interaction: Interaction, player: User):
        """Add a player to the current game."""
        # self.players.extend([player for player in players if player not in self.players])
        # await interaction.response.send_message(f"Added {' '.join(player.mention for player in players)} to the current game.")
        self.players.append(player)
        await interaction.response.send_message(f"Added {player.mention} to the current game.")

    @command()
    @game_command
    # Temporarily only accepts one user.
    async def removeplayer(self, interaction: Interaction, player: User):
        """Remove a player from the current game."""
        if len(self.players) <= 2:
            await interaction.response.send_message("Cannot have less than 2 players in a game.", ephemeral=True)
            return
        # for player in players:
        while player in self.players:
            self.players.remove(player)
        self.current_player = self.players[0]
        # await interaction.response.send_message(f"Removed {' '.join(player.mention for player in players)} from the current game.")
        await interaction.response.send_message(f"Removed {player.mention} from the current game.")


def parse_time(time_string: str) -> datetime.timedelta:
    regex = re.compile(
        r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$',
    )
    parts = regex.match(time_string)
    if parts is None:
        raise ValueError(
            f"Could not parse time information from '{time_string}'. "
            "Examples of valid strings: '16h', '2d8h5m20s', '7m4s'"
        )
    time_params = {name: float(param) for name, param in parts.groupdict().items() if param}
    return datetime.timedelta(**time_params)


async def setup(bot: Bot):
    await bot.add_cog(Game(bot))
