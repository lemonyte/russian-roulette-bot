# class RussianRoulette(Bot):
#     def __init__(self):
#         super().__init__(
#             command_prefix=when_mentioned_or(*config.prefixes),
#             intents=Intents(guilds=True, messages=True),
#             activity=Activity(name=config.activity.text, type=config.activity.type),
#             case_insensitive=True,
#             strip_after_prefix=True,
#         )

from discohook import Client

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


app = RussianRoulette()
