import random
import datetime
import functools
from typing import Optional

from discord import Embed, File, Interaction, User
from discord.app_commands import command
from discord.ext.commands import Bot, Cog
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
                self.duration = utils.parse_time(duration)
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
        response = (
            "**Current game info**:\n"
            f"Players: {' '.join(player.mention for player in self.players)}\n"
            f"Info: {self.info}\n"
            f"Duration: {self.duration}\n"
            f"Channel: {self.channel.mention}"
        )
        embed = Embed(title=utils.TITLE, description=response, color=0xff0000, url=utils.URL)
        await interaction.response.send_message(embed=embed)

    @command()
    @game_command
    async def shoot(self, interaction: Interaction, player: Optional[User] = None):
        # await interaction.response.defer()
        if interaction.channel != self.channel:
            await interaction.response.send_message(f"This game was started in the {self.channel} channel.", ephemeral=True)
            return
        if player is None:
            player = interaction.user
        if player != self.current_player:
            await interaction.response.send_message(f"It's {self.current_player.mention}'s turn.", ephemeral=True)
        n = random.randint(1, 6)
        file = File(utils.frame_path(n, self.image_size), 'thumbnail.png')
        if n == 1:
            response = random.choice(self.death_messages).format(user=player.display_name)
            embed = Embed(title=utils.TITLE, description=response, color=0xff0000, url=utils.URL)
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
            response = random.choice(self.luck_messages).format(user=player.display_name)
            embed = Embed(title=utils.TITLE, description=response, color=0xff0000, url=utils.URL)
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
        await interaction.response.send_message(file=File(utils.GIF_PATH))

    @command()
    @game_command
    async def list_players(self, interaction: Interaction):
        await interaction.response.send_message(f"Players in current game: {' '.join(player.mention for player in self.players)}")

    @command()
    @game_command
    # Temporarily only accepts one user.
    async def add_player(self, interaction: Interaction, player: User):
        # self.players.extend([player for player in players if player not in self.players])
        # await interaction.response.send_message(f"Added {' '.join(player.mention for player in players)} to the current game.")
        self.players.append(player)
        await interaction.response.send_message(f"Added {player.mention} to the current game.")

    @command()
    @game_command
    # Temporarily only accepts one user.
    async def remove_player(self, interaction: Interaction, player: User):
        if len(self.players) <= 2:
            await interaction.response.send_message("Cannot have less than 2 players in a game.", ephemeral=True)
            return
        # for player in players:
        while player in self.players:
            self.players.remove(player)
        self.current_player = self.players[0]
        # await interaction.response.send_message(f"Removed {' '.join(player.mention for player in players)} from the current game.")
        await interaction.response.send_message(f"Removed {player.mention} from the current game.")


async def setup(bot: Bot):
    await bot.add_cog(Game(bot))
