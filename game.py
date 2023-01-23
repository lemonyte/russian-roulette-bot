# pyright: reportOptionalMemberAccess=false

import datetime
import random
import re
from typing import Optional

from discord import Embed, File, Interaction, TextChannel, User, app_commands
from discord.ext.commands import Bot, Cog

from config import config


class NoGameStarted(Exception):
    def __init__(self, *args):
        super().__init__("No game has been started yet.", *args)


class GameInstance:
    def __init__(
        self,
        channel: TextChannel,
        players: list[User],
        info: Optional[str] = None,
        duration: Optional[str] = None,
    ):
        if len(players) < 2:
            raise ValueError("Must have at least 2 players to start a game.")

        self.channel = channel
        self.players = players
        self.info = info
        self.duration = parse_time(duration) if duration else None
        self.current_player = players[0]


class Game(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.games = {}

    async def cog_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            message = str(error.original)
        else:
            message = str(error)
        message = ":x: " + message
        await interaction.response.send_message(message, ephemeral=True)
        return await super().cog_app_command_error(interaction, error)

    def get_game_context(self, interaction: Interaction) -> GameInstance:
        if interaction.channel_id in self.games:
            return self.games[interaction.channel_id]
        raise NoGameStarted()

    @app_commands.command()
    async def start(
        self,
        interaction: Interaction,
        player_1: User,  # Temporary workaround while variadic arguments are not supported.
        player_2: User,
        info: Optional[str] = None,
        duration: Optional[str] = None,
    ):
        """Start a new game."""
        if interaction.channel_id in self.games:
            await interaction.response.send_message("Game already started.", ephemeral=True)
            return
        game = GameInstance(
            channel=interaction.channel,
            players=[player_1, player_2],
            info=info,
            duration=duration,
        )
        self.games[interaction.channel_id] = game
        await interaction.response.send_message(
            f"Started a new game with {' '.join(player.mention for player in game.players)}.",
        )
        # Workaround to manually call the 'shoot' command if the current player is the bot.
        if self.bot.user.id == game.current_player.id:
            # pylint: disable=protected-access, no-member
            await self.shoot._do_call(interaction, {'player': game.current_player})

    @app_commands.command()
    async def stop(self, interaction: Interaction):
        """Stop the current game."""
        game = self.get_game_context(interaction)
        del self.games[game.channel.id]
        await interaction.response.send_message("Stopped the current game.")

    @app_commands.command()
    async def current(self, interaction: Interaction):
        """Show information about the current game."""
        game = self.get_game_context(interaction)
        response = (
            f"Players: {' '.join(player.mention for player in game.players)}\n"
            f"Info: {game.info}\n"
            f"Duration: {game.duration}\n"
            f"Channel: {game.channel.mention}"
        )
        embed = Embed(title="Current Game Information", description=response, color=config.color, url=config.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def shoot(self, interaction: Interaction, player: Optional[User] = None):
        """Pull the trigger."""
        game = self.get_game_context(interaction)
        if interaction.channel != game.channel:
            await interaction.response.send_message(
                f"This game was started in the {game.channel} channel.",
                ephemeral=True,
            )
            return
        if player is None:
            player = interaction.user
        if player != game.current_player:
            await interaction.response.send_message(f"It's {game.current_player.mention}'s turn.", ephemeral=True)
        chamber = random.randint(1, 6)
        file = File(f'assets/images/frame_{chamber}.png', 'thumbnail.png')
        if chamber == 1:
            response = random.choice(config.game.death_messages).format(player=player.display_name)
            embed = Embed(
                title=f"{player.display_name}'s Turn",
                description=response,
                color=config.color,
                url=config.url,
            )
            embed.set_thumbnail(url='attachment://thumbnail.png')
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed, file=file)
            if game.info is not None:
                response = f"{player.mention} {game.info}."
                if game.duration is not None:
                    duration_end = datetime.datetime.utcnow() + game.duration
                    response += f"\nYour timer ends at {duration_end.strftime('%Y-%m-%d %I:%M:%S %p')} UTC."
                await interaction.followup.send(response)
            del self.games[game.channel.id]
        else:
            response = random.choice(config.game.luck_messages).format(player=player.display_name)
            embed = Embed(
                title=f"{player.display_name}'s Turn",
                description=response,
                color=config.color,
                url=config.url,
            )
            embed.set_thumbnail(url='attachment://thumbnail.png')
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed, file=file)
            game.players.append(game.players.pop(0))
            game.current_player = game.players[0]
            # Workaround to manually call the 'shoot' command if the current player is the bot.
            if self.bot.user.id == game.current_player.id:
                # pylint: disable=protected-access, no-member
                await self.shoot._do_call(interaction, {'player': game.current_player})

    @app_commands.command()
    async def gif(self, interaction: Interaction):
        """Send a GIF version of the game for screenshotting."""
        await interaction.response.send_message(file=File('assets/images/spin.gif'))

    @app_commands.command()
    async def listplayers(self, interaction: Interaction):
        """List the players in the current game."""
        game = self.get_game_context(interaction)
        await interaction.response.send_message(
            f"Players in current game: {' '.join(player.mention for player in game.players)}",
        )

    @app_commands.command()
    # Temporarily only accepts one user.
    async def addplayer(self, interaction: Interaction, player: User):
        """Add a player to the current game."""
        game = self.get_game_context(interaction)
        # self.players.extend([player for player in players if player not in self.players])
        # await interaction.response.send_message(
        #     f"Added {' '.join(player.mention for player in players)} to the current game.",
        # )
        game.players.append(player)
        await interaction.response.send_message(f"Added {player.mention} to the current game.")

    @app_commands.command()
    # Temporarily only accepts one user.
    async def removeplayer(self, interaction: Interaction, player: User):
        """Remove a player from the current game."""
        game = self.get_game_context(interaction)
        if len(game.players) <= 2:
            await interaction.response.send_message("Cannot have less than 2 players in a game.", ephemeral=True)
            return
        # for player in players:
        while player in game.players:
            game.players.remove(player)
        game.current_player = game.players[0]
        # await interaction.response.send_message(
        #     f"Removed {' '.join(player.mention for player in players)} from the current game.",
        # )
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
