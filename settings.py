from discord.ext.commands import Bot, Cog, Context, has_permissions, group
import utils


class Settings(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(aliases=['prefixes'])
    async def prefix(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await self.prefix_list(ctx)

    @prefix.command(name='list')
    async def prefix_list(self, ctx: Context):
        await ctx.reply(f"Prefixes: **`{', '.join(utils.get_prefixes(ctx.guild))}`**", mention_author=False)

    @prefix.command(name='add')
    @has_permissions(manage_guild=True)
    async def prefix_add(self, ctx: Context, prefix: str = None):
        if prefix is None:
            await ctx.reply("Please specify a prefix to add.", mention_author=False)
        prefixes = utils.get_prefixes(ctx.guild)
        if prefix in prefixes:
            await ctx.reply("Prefix is already added.", mention_author=False)
            return
        prefixes.append(prefix)
        utils.set_prefixes(ctx.guild, prefixes)
        await ctx.reply(f"Added prefix **`{prefix}`**.", mention_author=False)

    @prefix.command(name='remove')
    @has_permissions(manage_guild=True)
    async def prefix_remove(self, ctx: Context, prefix: str = None):
        if prefix is None:
            ctx.reply("Please specify a prefix to remove.", mention_author=False)
        prefixes = utils.get_prefixes(ctx.guild)
        if len(prefixes) <= 2:
            await ctx.reply("Cannot have less than 2 prefixes.", mention_author=False)
            return
        if prefix in prefixes:
            prefixes.remove(prefix)
        else:
            await ctx.reply(f"Prefix **`{prefix}`** does not exist.", mention_author=False)
            return
        utils.set_prefixes(ctx.guild, prefixes)
        await ctx.reply(f"Removed prefix **`{prefix}`**.", mention_author=False)

    @group(aliases=['channels'])
    async def channel(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await self.channel_list(ctx)

    @channel.command(name='list')
    async def channel_list(self, ctx: Context):
        await ctx.reply(f"Bound channels: {' '.join(f'<#{channel}>' for channel in utils.get_channels(ctx.guild))}", mention_author=False)

    @channel.command(name='add', aliases=['bind'])
    @has_permissions(manage_guild=True)
    async def channel_add(self, ctx: Context):
        channels = utils.get_channels(ctx.guild)
        if ctx.message.channel_mentions:
            for channel in ctx.message.channel_mentions:
                if channel.id not in channels:
                    channels.append(channel.id)
            await ctx.reply(f"Bound to channels {' '.join([channel.mention for channel in ctx.message.channel_mentions])}.", mention_author=False)
        else:
            channel = ctx.channel
            if channel.id not in channels:
                channels.append(channel.id)
                await ctx.reply(f"Bound to channel {channel.mention}.", mention_author=False)
            else:
                await ctx.reply("Channel is already bound.", mention_author=False)
                return
        utils.set_channels(ctx.guild, channels)

    @channel.command(name='remove', aliases=['unbind'])
    @has_permissions(manage_guild=True)
    async def channel_remove(self, ctx: Context):
        channels = utils.get_channels(ctx.guild)
        if ctx.message.channel_mentions:
            for channel in ctx.message.channel_mentions:
                if channel.id in channels:
                    channels.remove(channel.id)
        else:
            channel = ctx.channel
            if channel.id in channels:
                channels.remove(channel.id)
                await ctx.reply(f"Unbound from channel {channel.mention}.", mention_author=False)
            else:
                await ctx.reply("Cannot unbind from channel that is not bound.")
                return
        utils.set_channels(ctx.guild, channels)


async def setup(bot: Bot):
    await bot.add_cog(Settings(bot))
