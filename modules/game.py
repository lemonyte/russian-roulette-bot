import random
from io import BytesIO
from typing import Optional, Sequence

from deta import Base
from discohook import (
    Button,
    ButtonStyle,
    Embed,
    File,
    Interaction,
    Member,
    Message,
    PartialChannel,
    PartialEmoji,
    User,
    View,
    button,
    command,
)

from config import config
from main import RussianRoulette, app

# TODO: make this work

# def with_game(func):
#     @functools.wraps(func)
#     async def wrapper(interaction: Interaction, *args, **kwargs):
#         with await games.get(interaction.channel.id, interaction.client) as game:
#             await func(interaction, game, *args, **kwargs)

#     return wrapper


class GameError(Exception):
    pass


class GameInstance:
    def __init__(self, channel: PartialChannel, message: Message, creator: User, players: Sequence[User]):
        self.channel = channel
        self.message = message
        self.creator = creator
        self.players = list(players)
        self.current_player = self.creator
        self.started = False
        self.stopped = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            if self.stopped:
                await games.delete(self.channel.id)
            else:
                await games.update(self)

    @classmethod
    def from_dict(cls, data: dict):
        try:
            channel = PartialChannel({"id": data["channel"]}, app)
            message = Message(data["message"], app)
            creator = User(data["creator"], app)
            players = [User(id, app) for id in data["players"]]
            current_player = User(data["current_player"], app)
            started = data["started"]
            stopped = data["stopped"]
        except (KeyError, TypeError) as exc:
            raise ValueError("failed to parse game instance from data") from exc
        if not (channel and creator and current_player):
            raise ValueError("failed to parse game instance from data")
        players = [player for player in players if player]
        game = GameInstance(
            channel=channel,
            message=message,
            creator=creator,
            players=players,
        )
        game.current_player = current_player
        game.started = started
        game.stopped = stopped
        return game

    def to_dict(self) -> dict:
        return {
            "channel": self.channel.id,
            "message": self.message.data,
            "creator": self.creator.data,
            "players": [player.data for player in self.players],
            "current_player": self.current_player.data,
            "started": self.started,
            "stopped": self.stopped,
        }

    def start(self):
        if len(self.players) <= 0:
            raise GameError("No players left in game.")
        self.current_player = self.players[0]
        self.started = True

    def stop(self):
        self.started = True
        self.stopped = True

    def next(self):
        if len(self.players) <= 0:
            self.stop()
            raise GameError("No players left in game.")
        self.players.append(self.players.pop(0))
        self.current_player = self.players[0]

    def add_player(self, player: User):
        if player not in self.players:
            self.players.append(player)

    def remove_player(self, player: User):
        if player in self.players:
            self.players.remove(player)
        if len(self.players) <= 0 and self.started:
            self.stop()
        if len(self.players) > 0:
            self.current_player = self.players[0]


class GameDB:
    def __init__(self):
        self._db = Base("games_preview" if config.preview else "games")
        self._cache = {}

    async def check(self, id: str) -> bool:
        return self._db.get(id) is not None

    async def get(self, id: str) -> GameInstance:
        if id in self._cache:
            return self._cache[id]
        data = self._db.get(id)
        if data is not None:
            game = GameInstance.from_dict(data)  # type: ignore
            self._cache[id] = game
            return game
        raise GameError("Game not found.")

    async def put(self, game: GameInstance) -> str:
        self._db.insert(game.to_dict(), key=game.channel.id, expire_in=15 * 60)
        self._cache[game.channel.id] = game
        return game.channel.id

    async def update(self, game: GameInstance) -> str:
        self._db.update(game.to_dict(), key=game.channel.id)
        self._cache[game.channel.id] = game
        return game.channel.id

    async def delete(self, id: str):
        self._db.delete(id)
        del self._cache[id]


async def start_game_view() -> View:
    view = View()
    view.add_buttons(menu_button)
    return view


async def menu_view(interaction: Interaction) -> View:
    async with await games.get(interaction.channel.id) as game:
        if interaction.author in game.players:
            join_leave_button.label = "Leave Game"
            join_leave_button.emoji = PartialEmoji(name="📤")
        else:
            join_leave_button.label = "Join Game"
            join_leave_button.emoji = PartialEmoji(name="📥")
        if game.started:
            start_stop_button.label = "Stop Game"
            start_stop_button.style = ButtonStyle.red
            start_stop_button.emoji = PartialEmoji(name="🛑")
        else:
            start_stop_button.label = "Start Game"
            start_stop_button.style = ButtonStyle.green
            start_stop_button.emoji = PartialEmoji(name="✅")
        if interaction.author != game.creator or len(game.players) <= 0:
            start_stop_button.disabled = True
        else:
            start_stop_button.disabled = False
        if game.stopped:
            join_leave_button.disabled = True
            start_stop_button.disabled = True
        else:
            join_leave_button.disabled = False
            start_stop_button.disabled = False
        view = View()
        view.add_buttons(join_leave_button, start_stop_button)
        return view


async def shoot_view(btn: Optional[Button] = None) -> View:
    if btn is None:
        btn = ShootButton()
    view = View()
    view.add_buttons(btn)
    return view


# class StartGameView(View):
#     # Interaction tokens are valid for 15 minutes (900 seconds).
#     def stop(self):
#         self.menu_button.disabled = True
#         self.game.stop()
#         super().stop()

#     async def on_timeout(self):
#         self.stop()
#         embed = self.create_embed(
#             title="Game Timed Out",
#             description="Use </start:1045533617910206515> to start a new game.",
#         )
#         await self.update_embed(embed)


async def create_init_embed(
    players: Sequence[User],
    title: str = "Starting Game",
    description: str = "Click the Menu button below to join or start the game.",
) -> Embed:
    embed = Embed(
        title=title,
        description=description,
        color=config.color,
        url=config.url,
    )
    embed.add_field(
        name="Players",
        value="\n".join(player.mention for player in players),
    )
    return embed


async def update_init_embed(interaction: Interaction, embed: Optional[Embed] = None, view: Optional[View] = None):
    async with await games.get(interaction.channel.id) as game:
        if embed is None:
            embed = await create_init_embed(game.players)
        if view is None:
            view = await start_game_view()
        await game.message.edit(embed=embed, view=view)


@button(label="Menu", style=ButtonStyle.blurple, emoji="📑")
async def menu_button(interaction: Interaction):
    await interaction.response("Game Menu", view=await menu_view(interaction), ephemeral=True)


# class GameMenuView(View):
#     def stop(self):
#         self.join_leave_button.disabled = True
#         self.start_stop_button.disabled = True
#         self.parent.stop()
#         super().stop()


@button(label="Join Game", style=ButtonStyle.blurple, emoji="📥")
async def join_leave_button(interaction: Interaction):
    async with await games.get(interaction.channel.id) as game:
        if interaction.author not in game.players:
            game.add_player(interaction.author)
        else:
            game.remove_player(interaction.author)
        # if game.stopped:
        #     self.stop()
        await interaction.update_message(view=await menu_view(interaction))
        await update_init_embed(interaction)


@button(label="Start Game", style=ButtonStyle.green, emoji="✅")
async def start_stop_button(interaction: Interaction):
    async with await games.get(interaction.channel.id) as game:
        if not game.started:
            game.start()
            title = "Game Started"
        else:
            # self.stop()
            game.stop()
            title = "Game Stopped"
        await interaction.update_message(view=await menu_view(interaction))
        await update_init_embed(interaction, await create_init_embed(game.players, title))
        await send_shoot_message(interaction)


# class ShootView(View):
#     def stop(self):
#         self.finished.set()
#         super().stop()

#     async def on_timeout(self):
#         if self.message is None:
#             return
#         self.shoot_button.disabled = True
#         self.shoot_button.label = "Timed out"
#         self.shoot_button.emoji = "⌛"
#         self.shoot_button.style = ButtonStyle.grey
#         response = random.choice(config.game.timeout_responses).format(player=self.game.current_player.display_name)
#         embed = Embed(
#             title=f"{self.game.current_player.display_name}'s Turn",
#             description=response,
#             color=config.color,
#             url=config.url,
#         )
#         embed.set_thumbnail(url="attachment://spin.gif")
#         await self.message.edit(embed=embed, view=self)
#         self.game.remove_player(self.game.current_player)
#         self.stop()


async def send_shoot_message(interaction: Interaction):
    async with await games.get(interaction.channel.id) as game:
        embed = Embed(
            title=f"{game.current_player.name}'s Turn",
            # description=f"Click the button below to shoot.\nYou have {self.timeout} seconds.",
            description="Click the button below to shoot.",
            color=config.color,
            url=config.url,
        )
        embed.thumbnail(url="attachment://spin.gif")
        with open("assets/images/spin.gif", "rb") as image:
            file = File("spin.gif", content=BytesIO(image.read()))
        await game.channel.send(embed=embed, view=await shoot_view(), file=file)


class ShootButton(Button):
    def __init__(
        self,
        label: str = "Shoot",
        *,
        style=ButtonStyle.blurple,
        disabled: bool = False,
        emoji: str = "🔫",
        **kwargs,
    ):
        super().__init__(label=label, style=style, disabled=disabled, emoji=emoji, **kwargs)
        self.on_interaction(self.callback)

    async def callback(self, interaction: Interaction):
        async with await games.get(interaction.channel.id) as game:
            player = interaction.author
            if player != game.current_player:
                raise GameError("It's not your turn!")
            player_name = player.nick if isinstance(player, Member) else player.name
            btn = ShootButton(disabled=True)
            if game.stopped:
                await interaction.update_message(view=await shoot_view(btn))
                await interaction.followup("Game has been stopped.", ephemeral=True)
                # await self.on_timeout()
                return
            chamber = random.randint(1, 6)
            dead = chamber == 1
            if dead:
                btn.label = "Bang!"
                btn.emoji = PartialEmoji(name="☠")
                btn.style = ButtonStyle.red
                response = random.choice(config.game.death_responses).format(player=player_name)
            else:
                btn.label = "*Click*"
                btn.emoji = PartialEmoji(name="✅")
                btn.style = ButtonStyle.green
                response = random.choice(config.game.luck_responses).format(player=player_name)
            with open(f"assets/images/frame_{chamber}.png", "rb") as image:
                file = File(f"frame_{chamber}.png", content=BytesIO(image.read()))
            embed = Embed(
                title=f"{player_name}'s Turn",
                description=response,
                color=config.color,
                url=config.url,
            )
            embed.thumbnail(url=f"attachment://frame_{chamber}.png")
            await interaction.update_message(embed=embed, view=await shoot_view(btn), file=file)
            if dead:
                game.stop()
                embed = Embed(
                    title="Game Over",
                    description="Use </start:1045533617910206515> to play again.",
                    color=config.color,
                    url=config.url,
                )
                await game.channel.send(embed=embed)
            else:
                game.next()
                await send_shoot_message(interaction)
            # self.stop()


# class Game(Cog):
#     async def cog_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
#         if isinstance(error, app_commands.CommandInvokeError):
#             message = str(error.original)
#         else:
#             message = str(error)
#         message = ":x: " + message
#         if interaction.response.is_done():
#             await interaction.followup.send(message, ephemeral=True)
#         else:
#             await interaction.response.send_message(message, ephemeral=True)

#     def get_game_context(self, interaction: Interaction) -> GameInstance:
#         if interaction.channel_id is None:
#             raise ValueError("channel id must not be None")
#         game = self.games.get(interaction.channel_id)
#         if game:
#             return game
#         raise GameError("No game has been started yet. Use </start:1045533617910206515> to start a new game.")


@command(name="start", description="Start a new game.")
async def start(interaction: Interaction):
    if await games.check(interaction.channel.id):
        raise GameError("A game is already in progress.")
    await interaction.response(embed=await create_init_embed([interaction.author]), view=await start_game_view())
    message = await interaction.original_response()
    if not message:
        raise ValueError("failed to get original response message")
    game = GameInstance(
        channel=interaction.channel,
        message=message,
        creator=interaction.author,
        players=[interaction.author],
    )
    await games.put(game)


@command(name="stop", description="Stop the current game.")
async def stop(interaction: Interaction):
    async with await games.get(interaction.channel.id) as game:
        game.stop()
        await interaction.response("Stopped the current game.")


@command(name="info", description="Show information about the current game.")
async def info(interaction: Interaction):
    async with await games.get(interaction.channel.id) as game:
        description = f"Players: {' '.join(player.mention for player in game.players)}\n"
        if hasattr(game.channel, "mention"):
            description += f"Channel: {game.channel.mention}"
        embed = Embed(title="Current Game Information", description=description, color=config.color, url=config.url)
        await interaction.response(embed=embed)


@command(name="gif", description="Send a GIF version of the game for screenshotting.")
async def gif(interaction: Interaction):
    with open("assets/images/spin.gif", "rb") as image:
        file = File("spin.gif", content=BytesIO(image.read()))
    await interaction.response(file=file)


def setup(client: RussianRoulette):
    client.add_commands(start, stop, info, gif)


games = GameDB()
