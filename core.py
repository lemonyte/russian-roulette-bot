import sys

from discohook import Client, Embed, Interaction, __version__, command

from config import config


class Core:
    def __init__(self, client: Client):
        self.client = client
        self.client.on_error(self.error_handler)
        self.client.add_commands(self.invite, self.debug, self.about, self.rules)

    async def error_handler(self, interaction: Interaction, exception: Exception):
        if interaction.responded:
            await interaction.followup(f"```py\nError: {exception}\n```", ephemeral=True)
        else:
            await interaction.response(f"```py\nError: {exception}\n```", ephemeral=True)
        raise exception
        # FIXME: the above is not recommended as it might leak secret tokens

    @command(name="ping", description="Check if the bot is online.")
    async def ping(self, interaction: Interaction):
        # TODO: latency
        await interaction.response("Pong!")

    @command(name="invite", description="Get an invite link for the bot.")
    async def invite(self, interaction: Interaction):
        await interaction.response(f"Invite me to your server: {config.invite}")

    @command(name="debug", description="Show debug information.")
    async def debug(self, interaction: Interaction):
        user = await interaction.client.as_user()
        # TODO: permissions, scopes
        description = f"""
        **General**
        ```
        Name: {user.name}
        ID: {user.id}
        Permissions: {None}
        Scopes: {None}
        Preview: {config.preview}
        URL: {config.url}
        ```

        **Runtime**
        ```
        Python version: {sys.version.split()[0]}
        discohook version: {__version__}
        ```
        """
        description = "\n".join(line.strip() for line in description.splitlines())
        embed = Embed(title="Debug Info", description=description, color=config.color, url=config.url)
        await interaction.response(embed=embed)

    @command(name="about", description="Show information about the bot.")
    async def about(self, interaction: Interaction):
        with open("assets/markdown/about.md", "r") as about_file:
            embed = Embed(
                title=f"About {config.name}",
                description=about_file.read(),
                color=config.color,
                url=config.url,
            )
        await interaction.response(embed=embed)

    @command(name="rules", description="Show the rules of the game.")
    async def rules(self, interaction: Interaction):
        with open("assets/markdown/rules.md", "r") as rules_file:
            embed = Embed(
                title=f"{config.name} Rules",
                description=rules_file.read(),
                color=config.color,
                url=config.url,
            )
        await interaction.response(embed=embed)


def setup(client: Client):
    Core(client)
