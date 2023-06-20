# class RussianRoulette(Bot):
#     def __init__(self):
#         super().__init__(
#             command_prefix=when_mentioned_or(*config.prefixes),
#             intents=Intents(guilds=True, messages=True),
#             activity=Activity(name=config.activity.text, type=config.activity.type),
#             case_insensitive=True,
#             strip_after_prefix=True,
#         )

# TODO: bot activity

from discohook import ApplicationCommand, Client

from config import config


class RussianRoulette(Client):
    def __init__(self, **kwargs):
        super().__init__(
            application_id=config.application_id,
            public_key=config.public_key,
            token=config.token,
            **kwargs,
        )
        self.load_modules("modules")
        self.commands = {}

    async def fetch_commands(self) -> dict:
        if not self.commands:
            response = await self.http.request("GET", f"/applications/{self.application_id}/commands")
            commands = await response.json()
            self.commands = {f"{command['name']}:{command['type']}": command for command in commands}
        return self.commands

    async def get_command_id(self, command: ApplicationCommand) -> str:
        if not self.commands:
            await self.fetch_commands()
        return self.commands[f"{command.name}:{command.category.value}"]["id"]


app = RussianRoulette()
