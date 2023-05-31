import asyncio
import random
from typing import Optional, Union

from discord import (
    ButtonStyle,
    Embed,
    File,
    Interaction,
    Member,
    User,
    app_commands,
    ui,
)
from discord.ext.commands import Bot, Cog

from config import config


class GameError(Exception):
    pass


class GameInstance:
    def __init__(self, channel, creator: Union[User, Member], players: list[Union[User, Member]]):
        self.channel = channel
        self.creator = creator
        self.players = players
        self.current_player = creator
        self.started = asyncio.Event()
        self.stopped = asyncio.Event()

    def start(self):
        if len(self.players) <= 0:
            raise GameError("No players left in game.")
        self.current_player = self.players[0]
        self.started.set()

    def stop(self):
        self.started.set()
        self.stopped.set()

    def next(self):
        if len(self.players) <= 0:
            self.stop()
            raise GameError("No players left in game.")
        self.players.append(self.players.pop(0))
        self.current_player = self.players[0]

    def add_player(self, player: Union[User, Member]):
        if player not in self.players:
            self.players.append(player)

    def remove_player(self, player: Union[User, Member]):
        if player in self.players:
            self.players.remove(player)
        if len(self.players) <= 0 and self.started.is_set():
            self.stop()
        if len(self.players) > 0:
            self.current_player = self.players[0]


class View(ui.View):
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item, /):
        message = ":x: " + str(error)
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return await super().on_error(interaction, error, item)


class StartGameView(View):
    # Interaction tokens are valid for 15 minutes (900 seconds).
    def __init__(self, interaction: Interaction, *, timeout: Optional[float] = 890):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.game = GameInstance(
            interaction.channel,
            self.interaction.user,
            [self.interaction.user],
        )

    def stop(self):
        self.menu_button.disabled = True
        self.game.stop()
        super().stop()

    async def on_timeout(self):
        self.stop()
        embed = self.create_embed(
            title="Game Timed Out",
            description="Use </start:1045533617910206515> to start a new game.",
        )
        await self.update_embed(embed)

    def create_embed(self, *, title: Optional[str] = None, description: Optional[str] = None) -> Embed:
        if title is None:
            title = "Starting Game"
        if description is None:
            description = "Click the Menu button below to join the game."
        embed = Embed(
            title=title,
            description=description,
            color=config.color,
            url=config.url,
        )
        embed.add_field(
            name="Players",
            value="\n".join(player.mention for player in self.game.players),
        )
        return embed

    async def send_embed(self):
        await self.interaction.response.send_message(embed=self.create_embed(), view=self)

    async def update_embed(self, embed: Optional[Embed] = None, *, view: Optional[ui.View] = None, **kwargs):
        if embed is None:
            embed = self.create_embed()
        if view is None:
            view = self
        await self.interaction.edit_original_response(embed=embed, view=view, **kwargs)

    @ui.button(label="Menu", style=ButtonStyle.blurple, emoji="📑")
    async def menu_button(self, interaction: Interaction, button: ui.Button):  # pylint: disable=unused-argument
        menu = GameMenuView(self, interaction)
        await interaction.response.send_message("Game Menu", view=menu, ephemeral=True)


class GameMenuView(View):
    def __init__(self, parent: StartGameView, interaction: Interaction, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.parent = parent
        if interaction.user in self.parent.game.players:
            self.join_leave_button.label = "Leave Game"
            self.join_leave_button.emoji = "📤"
        else:
            self.join_leave_button.label = "Join Game"
            self.join_leave_button.emoji = "📥"
        if self.parent.game.started.is_set():
            self.start_stop_button.label = "Stop Game"
            self.start_stop_button.style = ButtonStyle.red
            self.start_stop_button.emoji = "🛑"
        else:
            self.start_stop_button.label = "Start Game"
            self.start_stop_button.emoji = "✅"
        if self.parent.game.stopped.is_set():
            self.join_leave_button.disabled = True
            self.start_stop_button.disabled = True
        if interaction.user != self.parent.game.creator or len(self.parent.game.players) <= 0:
            self.start_stop_button.disabled = True

    def stop(self):
        self.join_leave_button.disabled = True
        self.start_stop_button.disabled = True
        self.parent.stop()
        super().stop()

    @ui.button(label="Join Game", style=ButtonStyle.blurple, emoji="📥")
    async def join_leave_button(self, interaction: Interaction, button: ui.Button):
        if interaction.user not in self.parent.game.players:
            self.parent.game.add_player(interaction.user)
            button.label = "Leave Game"
            button.emoji = "📤"
        else:
            self.parent.game.remove_player(interaction.user)
            button.label = "Join Game"
            button.emoji = "📥"
        if len(self.parent.game.players) <= 0:
            self.start_stop_button.disabled = True
        else:
            self.start_stop_button.disabled = False
        if self.parent.game.stopped.is_set():
            self.stop()
        await interaction.response.edit_message(view=self)
        await self.parent.update_embed()

    @ui.button(label="Start Game", style=ButtonStyle.green, emoji="✅", row=1)
    async def start_stop_button(self, interaction: Interaction, button: ui.Button):
        if not self.parent.game.started.is_set():
            self.parent.game.start()
            button.label = "Stop Game"
            button.style = ButtonStyle.red
            button.emoji = "🛑"
            title = "Game Started"
        else:
            self.stop()
            button.disabled = True
            title = "Game Stopped"
        await interaction.response.edit_message(view=self)
        await self.parent.update_embed(self.parent.create_embed(title=title))


class ShootView(View):
    def __init__(self, game: GameInstance, *, timeout: Optional[float] = 30):
        super().__init__(timeout=timeout)
        self.game = game
        self.message = None
        self.finished = asyncio.Event()

    def stop(self):
        self.finished.set()
        super().stop()

    async def on_timeout(self):
        if self.message is None:
            return
        self.shoot_button.disabled = True
        self.shoot_button.label = "Timed out"
        self.shoot_button.emoji = "⌛"
        self.shoot_button.style = ButtonStyle.gray
        response = random.choice(config.game.timeout_responses).format(player=self.game.current_player.display_name)
        embed = Embed(
            title=f"{self.game.current_player.display_name}'s Turn",
            description=response,
            color=config.color,
            url=config.url,
        )
        embed.set_thumbnail(url="attachment://spin.gif")
        await self.message.edit(embed=embed, view=self)
        self.game.remove_player(self.game.current_player)
        self.stop()

    async def send_embed(self):
        embed = Embed(
            title=f"{self.game.current_player.display_name}'s Turn",
            description=f"Click the button below to shoot.\nYou have {self.timeout} seconds.",
            color=config.color,
            url=config.url,
        )
        embed.set_thumbnail(url="attachment://spin.gif")
        self.message = await self.game.channel.send(
            embed=embed,
            view=self,
            file=File("assets/images/spin.gif", "spin.gif"),
        )

    @ui.button(label="Shoot", style=ButtonStyle.blurple, emoji="🔫")
    async def shoot_button(self, interaction: Interaction, button: ui.Button):
        if self.message is None:
            return
        player = interaction.user
        if player != self.game.current_player:
            raise GameError("It's not your turn!")
        button.disabled = True
        if self.game.stopped.is_set():
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("Game has been stopped.", ephemeral=True)
            await self.on_timeout()
            return
        chamber = random.randint(1, 6)
        if chamber == 1:
            button.label = "Bang!"
            button.emoji = "☠"
            button.style = ButtonStyle.red
            response = random.choice(config.game.death_responses).format(player=player.display_name)
            self.game.stop()
        else:
            button.label = "*Click*"
            button.emoji = "✅"
            button.style = ButtonStyle.green
            response = random.choice(config.game.luck_responses).format(player=player.display_name)
            self.game.next()
        file = File(f"assets/images/frame_{chamber}.png", f"frame_{chamber}.png")
        embed = Embed(
            title=f"{player.display_name}'s Turn",
            description=response,
            color=config.color,
            url=config.url,
        )
        embed.set_thumbnail(url=f"attachment://frame_{chamber}.png")
        await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
        self.stop()


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
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    def get_game_context(self, interaction: Interaction) -> GameInstance:
        if interaction.channel_id in self.games:
            game = self.games[interaction.channel_id]
            return game
        raise GameError("No game has been started yet. Use </start:1045533617910206515> to start a new game.")

    @app_commands.command()
    async def start(self, interaction: Interaction):
        """Start a new game."""
        if interaction.channel_id in self.games:
            raise GameError("A game is already in progress.")
        view = StartGameView(interaction)
        game = view.game
        self.games[game.channel.id] = game
        await view.send_embed()
        await view.game.started.wait()
        try:
            while not game.stopped.is_set():
                view = ShootView(game)
                await view.send_embed()
                await view.finished.wait()
            embed = Embed(
                title="Game Over",
                description="Use </start:1045533617910206515> to play again.",
                color=config.color,
                url=config.url,
            )
            await game.channel.send(embed=embed)
        finally:
            if game.channel.id in self.games:
                del self.games[game.channel.id]

    @app_commands.command()
    async def stop(self, interaction: Interaction):
        """Stop the current game."""
        game = self.get_game_context(interaction)
        game.stop()
        del self.games[game.channel.id]
        await interaction.response.send_message("Stopped the current game.")

    @app_commands.command()
    async def info(self, interaction: Interaction):
        """Show information about the current game."""
        game = self.get_game_context(interaction)
        description = f"Players: {' '.join(player.mention for player in game.players)}\n"
        if hasattr(game.channel, "mention"):
            description += f"Channel: {game.channel.mention}"
        embed = Embed(title="Current Game Information", description=description, color=config.color, url=config.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def gif(self, interaction: Interaction):
        """Send a GIF version of the game for screenshotting."""
        await interaction.response.send_message(file=File("assets/images/spin.gif"))


async def setup(bot: Bot):
    await bot.add_cog(Game(bot))
