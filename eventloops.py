from discord.ext import tasks, commands
from utils import GameType
from asyncio import sleep
from os import getenv
import dbl
from traceback import format_exception

class EventLoops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.token = getenv('TOKEN2')
        # self.dblpy = dbl.DBLClient(self.bot, self.token)
        # print("Successfully logged in to top.gg client.")
        self.topggvotes = 0
        self.inspect.start()
        # self.update_stats.start()

    def cog_unload(self):
        # self.inspect.stop()
        self.inspect.cancel()

    @tasks.loop(minutes=1.0, reconnect=False)
    async def inspect(self):
        for game in list(self.bot.games.values()):
            if game.type in (GameType.SINGLE, GameType.DOUBLE): 
                continue
            else: 
                await game.update()

    @inspect.before_loop
    async def before_inspect(self):
        print("waiting . . .")
        await self.bot.wait_until_ready(); print("started!")

    @inspect.after_loop
    async def after_inspect(self):
        self.inspect.restart()

    @inspect.error
    async def inspect_error(self, error):
        print(format_exception(error, error, error.__traceback__))
        await self.bot.get_channel(self.bot.debug_channel).send("An Error occured in eventloops cog.")

    # @tasks.loop(hours=1.0)
    # async def update_stats(self):
    #     server_count = len(self.bot.guilds)
    #     try:
    #         await self.dblpy.post_guild_count(server_count)
    #         self.topggvotes = len(await self.dblpy.get_bot_upvotes())
    #        print('Updated server count:', server_count)
    #        self.bot.log.info(f'Updated server count: {server_count}.')
    #     except Exception as e:
    #         print('Failed to update server count in top.gg', format_exception(e, e, e.__traceback__))

    # @update_stats.before_loop
    # async def before_update_stats(self):
    #     await self.bot.wait_until_ready()

    # @update_stats.after_loop
    # async def after_update_stats(self):
    #     self.update_stats.restart()

    # @update_stats.error
    # async def update_stats_error(self):
    #     await sleep(5)
    #     self.update_stats.restart()

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        print("Received an upvote:", "\n", data, sep="")

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        print("Received a test upvote:", "\n", data, sep="")

def setup(bot):
    bot.add_cog(EventLoops(bot))