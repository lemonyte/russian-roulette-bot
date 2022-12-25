import os
import sys

import yaml

try:
    import dotenv

    dotenv.load_dotenv()
except ModuleNotFoundError:
    pass

PREVIEW = '--preview' in sys.argv or '-p' in sys.argv


class ConfigMeta(type):
    """Metaclass for populating config classes.

    Config classes define fields with type annotations, and optionally a default value.
    Fields will be populated with values from a YAML file, or the default value if no value is found.
    If a field is missing from the YAML file and no default value is provided, an exception is raised.

    Note:
        Parsing objects inside lists is not supported and will be returned as dictionaries.
        Parameterized types such as `list[str]` are not supported.
        If the type annotation is another config class, do not provide a default value.

    Args:
        obj_path (str): A dot-separated path to an object in the YAML file that contains the class's fields.
            If not provided, the class's fields are assumed to be at the root of the YAML file.

    Raises:
        ValueError: If 'obj_path' does not point to an existing object in the YAML file.
        ValueError: If a field is missing from the YAML file and no default value is provided.
        TypeError: If a field's value in the YAML file is not of the correct type.
    """

    def __new__(cls, name, bases, attrs, *, obj_path: str = ''):
        file_path = 'config_preview.yaml' if PREVIEW else 'config.yaml'

        if os.path.isfile(file_path):
            with open(file_path, 'r') as config_file:
                config_data = yaml.safe_load(config_file)
        else:
            config_data = {}

        if obj_path:
            try:
                for path in obj_path.split('.'):
                    config_data = config_data[path]
            except KeyError:
                config_data = {}

        for attr, type in attrs['__annotations__'].items():
            attr_path = f'{obj_path}.{attr}' if obj_path else attr

            if type.__class__ is cls:
                # If the annotation's type is ConfigMeta, it's a nested config class.
                # Directly assign the class object to the attribute.
                attrs[attr] = type
            else:
                # If a value is provided in the YAML file, use it.
                # Otherwise, if no default value is provided, raise an exception.
                if attr in config_data:
                    attrs[attr] = config_data[attr]
                elif attr not in attrs:
                    raise ValueError(f"no value provided for required config field '{attr_path}'")

                # Check that the value is of the correct type.
                if not isinstance(attrs[attr], type):
                    raise TypeError(
                        f"config field '{attr_path}' must be of type '{type.__name__}'"
                        f", found '{attrs[attr].__class__.__name__}'"
                    )

        return super().__new__(cls, name, bases, attrs)


class _ActivityConfig(metaclass=ConfigMeta, obj_path='activity'):
    text: str = r"is 83.3% safe!"
    # 0 = playing, 1 = streaming, 2 = listening, 3 = watching
    type: int = 0


class _GameConfig(metaclass=ConfigMeta, obj_path='game'):
    luck_messages: list = [
        "{player} got lucky.",
        "{player} is having a good day.",
        "{player} lives on to the next round.",
        "{player} survived the odds.",
        "{player} rigged the game.",
        "{player} cheated death.",
    ]
    death_messages: list = [
        "{player} died.",
        "{player} wasn't lucky enough.",
        "{player} took too many chances.",
        "{player} took one for the team.",
        "{player} lost the game, and their life.",
        "{player} left their brains behind.",
    ]


class _Config(metaclass=ConfigMeta):
    name: str = "Russian Roulette"
    url: str = 'https://github.com/LemonPi314/russian-roulette-bot'
    color: int = 0xFF0000
    prefixes: list = ['rr', 'russian-roulette']
    invite: str = (
        r'https://discord.com/api/oauth2/authorize?client_id=901284333770383440'
        r'&permissions=137506374720&scope=applications.commands%20bot'
    )
    preview: bool = PREVIEW
    token: str = os.getenv('DISCORD_TOKEN_PREVIEW' if PREVIEW else 'DISCORD_TOKEN') or ''
    activity: _ActivityConfig
    game: _GameConfig


config = _Config  # pylint: disable=invalid-name
