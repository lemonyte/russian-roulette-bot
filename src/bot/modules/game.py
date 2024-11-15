# ruff: noqa: S311
from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

from deta import Base
from discord import (
    ButtonStyle,
    CategoryChannel,
    Embed,
    File,
    ForumChannel,
    Interaction,
    StageChannel,
    TextChannel,
    Thread,
    VoiceChannel,
    app_commands,
    ui,
)
from discord.ext.commands import Bot, Cog

from bot.config import config

if TYPE_CHECKING:
    from collections.abc import Sequence

    from discord.abc import MessageableChannel, User


class GameError(Exception):
    pass


class GameInstance:
    def __init__(self, channel: MessageableChannel, creator: User, players: Sequence[User]) -> None:
        self.channel = channel
        self.creator = creator
        self.players = list(players)
        self.current_player = creator
        self.started = asyncio.Event()
        self.stopped = asyncio.Event()

    @classmethod
    def from_dict(cls, data: dict, bot: Bot) -> GameInstance:
        try:
            channel = bot.get_channel(data["channel"])
            creator = bot.get_user(data["creator"])
            players = [bot.get_user(id) for id in data["players"]]
            current_player = bot.get_user(data["current_player"])
            started = data["started"]
            stopped = data["stopped"]
        except (KeyError, TypeError) as exc:
            msg = "failed to parse game instance from data"
            raise ValueError(msg) from exc
        if not (channel and creator and current_player):
            msg = "failed to parse game instance from data"
            raise ValueError(msg)
        if isinstance(channel, CategoryChannel | ForumChannel):
            msg = "channel cannot be a category or forum channel"
            raise TypeError(msg)
        players = [player for player in players if player]
        game = GameInstance(
            channel=channel,  # type: ignore  # PrivateChannels should always be MessageableChannels
            creator=creator,
            players=players,
        )
        game.current_player = current_player
        if started:
            game.started.set()
        if stopped:
            game.stopped.set()
        return game

    def to_dict(self) -> dict:
        return {
            "channel": self.channel.id,
            "creator": self.creator.id,
            "players": [player.id for player in self.players],
            "current_player": self.current_player.id,
            "started": self.started.is_set(),
            "stopped": self.stopped.is_set(),
        }

    def start(self) -> None:
        if len(self.players) <= 0:
            msg = "No players left in game."
            raise GameError(msg)
        self.current_player = self.players[0]
        self.started.set()

    def stop(self) -> None:
        self.started.set()
        self.stopped.set()

    def next(self) -> None:
        if len(self.players) <= 0:
            self.stop()
            msg = "No players left in game."
            raise GameError(msg)
        self.players.append(self.players.pop(0))
        self.current_player = self.players[0]

    def add_player(self, player: User) -> None:
        if player not in self.players:
            self.players.append(player)

    def remove_player(self, player: User) -> None:
        if player in self.players:
            self.players.remove(player)
        if len(self.players) <= 0 and self.started.is_set():
            self.stop()
        if len(self.players) > 0:
            self.current_player = self.players[0]


class GameDB:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._db = Base("games_preview" if config.preview else "games")

    def get(self, id: int) -> GameInstance | None:
        data = self._db.get(str(id))
        if data is not None:
            return GameInstance.from_dict(data, self.bot)  # type: ignore
        return data

    def put(self, game: GameInstance) -> str:
        key = str(game.channel.id)
        self._db.insert(game.to_dict(), key=key, expire_in=15 * 60)
        return key

    def delete(self, id: int) -> None:
        self._db.delete(str(id))


class View(ui.View):
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item, /) -> None:
        message = ":x: " + str(error)
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return await super().on_error(interaction, error, item)


class StartGameView(View):
    # Interaction tokens are valid for 15 minutes (900 seconds).
    def __init__(self, interaction: Interaction, *, timeout: float | None = 890) -> None:
        super().__init__(timeout=timeout)
        if not interaction.channel:
            msg = "channel must not be None"
            raise ValueError(msg)
        if isinstance(interaction.channel, CategoryChannel | ForumChannel):
            msg = "channel cannot be a category or forum channel"
            raise TypeError(msg)
        self.interaction = interaction
        self.game = GameInstance(
            interaction.channel,
            self.interaction.user,
            [self.interaction.user],
        )

    def stop(self) -> None:
        self.menu_button.disabled = True
        self.game.stop()
        super().stop()

    async def on_timeout(self) -> None:
        self.stop()
        embed = self.create_embed(
            title="Game Timed Out",
            description="Use </start:1045533617910206515> to start a new game.",
        )
        await self.update_embed(embed)

    def create_embed(self, *, title: str | None = None, description: str | None = None) -> Embed:
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

    async def send_embed(self) -> None:
        await self.interaction.response.send_message(embed=self.create_embed(), view=self)

    async def update_embed(self, embed: Embed | None = None, *, view: ui.View | None = None) -> None:
        if embed is None:
            embed = self.create_embed()
        if view is None:
            view = self
        await self.interaction.edit_original_response(embed=embed, view=view)

    @ui.button(label="Menu", style=ButtonStyle.blurple, emoji="📑")
    async def menu_button(self, interaction: Interaction, button: ui.Button) -> None:  # noqa: ARG002
        menu = GameMenuView(self, interaction)
        await interaction.response.send_message("Game Menu", view=menu, ephemeral=True)


class GameMenuView(View):
    def __init__(self, parent: StartGameView, interaction: Interaction, *, timeout: float | None = 180) -> None:
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

    def stop(self) -> None:
        self.join_leave_button.disabled = True
        self.start_stop_button.disabled = True
        self.parent.stop()
        super().stop()

    @ui.button(label="Join Game", style=ButtonStyle.blurple, emoji="📥")
    async def join_leave_button(self, interaction: Interaction, button: ui.Button) -> None:
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
    async def start_stop_button(self, interaction: Interaction, button: ui.Button) -> None:
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
    def __init__(self, game: GameInstance, *, timeout: float | None = 30) -> None:
        super().__init__(timeout=timeout)
        self.game = game
        self.message = None
        self.finished = asyncio.Event()

    def stop(self) -> None:
        self.finished.set()
        super().stop()

    async def on_timeout(self) -> None:
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

    async def send_embed(self) -> None:
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
    async def shoot_button(self, interaction: Interaction, button: ui.Button) -> None:
        if self.message is None:
            return
        player = interaction.user
        if player != self.game.current_player:
            msg = "It's not your turn!"
            raise GameError(msg)
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
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.games = GameDB(self.bot)

    async def cog_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        message = str(error.original) if isinstance(error, app_commands.CommandInvokeError) else str(error)
        message = ":x: " + message
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    def get_game_context(self, interaction: Interaction) -> GameInstance:
        if interaction.channel_id is None:
            msg = "channel id must not be None"
            raise ValueError(msg)
        game = self.games.get(interaction.channel_id)
        if game:
            return game
        msg = "No game has been started yet. Use </start:1045533617910206515> to start a new game."
        raise GameError(msg)

    @app_commands.command()
    async def start(self, interaction: Interaction) -> None:
        """Start a new game."""
        if interaction.channel_id is None:
            msg = "channel id must not be None"
            raise ValueError(msg)
        if self.games.get(interaction.channel_id):
            msg = "A game is already in progress."
            raise GameError(msg)
        view = StartGameView(interaction)
        game = view.game
        self.games.put(game)
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
            self.games.delete(game.channel.id)

    @app_commands.command()
    async def stop(self, interaction: Interaction) -> None:
        """Stop the current game."""
        game = self.get_game_context(interaction)
        game.stop()
        self.games.delete(game.channel.id)
        await interaction.response.send_message("Stopped the current game.")

    @app_commands.command()
    async def info(self, interaction: Interaction) -> None:
        """Show information about the current game."""
        game = self.get_game_context(interaction)
        description = f"Players: {' '.join(player.mention for player in game.players)}\n"
        if isinstance(game.channel, TextChannel | Thread | VoiceChannel | StageChannel):
            description += f"Channel: {game.channel.mention}"
        embed = Embed(title="Current Game Information", description=description, color=config.color, url=config.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def gif(self, interaction: Interaction) -> None:
        """Send a GIF version of the game for screenshotting."""
        await interaction.response.send_message(file=File("assets/images/spin.gif"))


async def setup(bot: Bot) -> None:
    await bot.add_cog(Game(bot))
