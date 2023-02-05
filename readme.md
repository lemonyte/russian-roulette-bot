# Russian Roulette Bot

A Discord bot to play virtual Russian Roulette with your friends.

Thanks to [BranStork](https://github.com/BranStork) for the inspiration.

## Usage

> Note: the terms "server" and "guild" are used interchangeably throughout this document.

### Quick Start

Add the bot to your chosen Discord guild using either [this link](https://discord.com/api/oauth2/authorize?client_id=901284333770383440&permissions=534925208641&scope=bot%20applications.commands) or the "Add to Server" button in the bot's profile in Discord. Mention the bot to receive some basic information including the default prefixes, which are `rr`, `russian-roulette`, and the bot's mention.

### Channel Binding

Once you have added the bot to a guild, you may want to "bind" the bot to a specific channel meant for playing roulette, in order to avoid spamming general chat channels. To bind a specific channel type `rr channel bind #channel-name`, and replace `channel-name` with the mention of the channel you want to bind. Once at least one channel has been bound, the bot will not respond to messages sent in unbound channels. Keep in mind this command requires the "Manage Server" permission. To unbind a channel, simply type `rr channel unbind #channel-name`, following the same steps as above. If no channels are bound, the bot will respond in any channel it has access to.

### Starting a Game

You are now ready to play some games! First, come up with a consequence for the losing player. For example: a profile picture, status, or server nickname (keep it within server rules) that lasts for a set amount of time, like 24 hours. Then, start a new game by typing the command `rr start @user1 @user2 info: game description or consequence instructions duration: 4d17h9m43s`. Replace `@user1 @user2` with mentions of users who wish to participate in the game. `info:` and `duration:` are optional and are parsed by the bot to save information about the current game.

### Playing the Game

Once a game has been started, players take turns typing `rr shoot` in chat, in the order they were mentioned in the `start` command. Every turn has a 1 in 6 chance of losing, indicated by a red bullet positioned in the top slot of the cylinder. The chance is purely random, the bullet does not go in order between the slots. If all players take a turn with no one losing, the game continues from the first player again. Once a player loses, the game ends and the losing player must carry out the consequence stated before the start of the game. Specific rules and exceptions are at the discretion of players and guild staff. To stop a game, type `rr stop`.

### Adding and Removing Players

To add or remove a player from a currently running game, type `rr player add @user` or `rr player remove @user`, and replace `@user` with the mention of the user. A game cannot have less than 2 players. It is also possible to play against the bot itself, however if the bot loses it will not carry out any consequences.

### Custom Prefixes

You can also customize the bot's prefixes in your guild. Type `rr prefix add <prefix>` to add a prefix, or `rr prefix remove <prefix>` to remove a prefix, and replace `<prefix>` with your prefix. If the prefix contains space characters, wrap it in quotes (`" "`). To see a list of prefixes available in the guild, type `rr prefix list`. You cannot remove the bot's mention as a prefix, and you cannot add user or channel mentions as prefixes.

### Full Command List

(Prefixes omitted)

Command|Category|Arguments|Description
--|--|--|--
`about`|Core|None|Show info about the bot
`rules`|Core|None|Show game rules
`start`|Game|User mentions, `info`, `duration`|Start a new game with at least 2 players and an optional description and timer
`stop`|Game|None|Stop the current game
`current`|Game|None|Show info about the current game
`shoot`|Game|None|Take a turn
`gif`|Game|None|Show a GIF version of the game for screenshotting
`player list`|Game|None|List the players in the current game
`player add`|Game|User mention|Add a player to the current game
`player remove`|Game|User mention|Remove a player from the current game
`prefix list`|Settings|None|List the bot's prefixes in the current guild
`prefix add`|Settings|Prefix string|Add a prefix to the bot in the current guild
`prefix remove`|Settings|Prefix string|Remove a prefix from the bot in the current guild
`channel list`|Settings|None|List the bound channels in the current guild
`channel add`|Settings|Channel mention|Bind a channel in the current guild
`channel remove`|Settings|Channel mention|Unbind a channel in the current guild

## Privacy

This bot collects and stores the following information:

- Guild name and ID
- Bound channel IDs
- Prefixes

This information is used to keep per-guild configuration data (custom prefixes, bound channels). This bot does not collect any user information or message content.

## Disclaimer

This bot does not endorse or promote Russian Roulette in the real world in any way. This bot was created purely for virtual entertainment purposes. I am not liable for any data loss, damage, or any other consequences resulting from use of this software. Use at your own risk.

## Hosting

### Requirements

- [Python 3.9](https://www.python.org/downloads/) or higher
- Packages listed in [`requirements.txt`](requirements.txt)

If you wish to host an instance of this bot yourself, follow the instructions below.

1. Create an application in the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a bot for the application
3. Clone this repository
4. Install dependencies with `pip install -r requirements.txt`
5. Create a file named `.env` in the cloned directory
6. Copy the bot token from the Developer Portal and paste it into the `.env` file in this format: `DISCORD_TOKEN="your token here"`
7. Run the bot with `python bot.py`

There is also a "preview mode" which allows for testing changes without affecting the main instance of the bot. To use the preview mode, create another application in the Discord Developer Portal and put the bot token into the `.env` file in this format: `DISCORD_TOKEN_PREVIEW="your token here"`. Start the bot in preview mode using `python bot.py --preview`.

If you are unfamiliar with the [Discord Developer Portal](https://discord.com/developers/applications) or Python, check out [this tutorial](https://realpython.com/how-to-make-a-discord-bot-python/).

## License

[MIT License](license.txt)
