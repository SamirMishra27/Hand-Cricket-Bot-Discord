"""
    Copyright © 2020-2021 SamirMishra27
    all rights reserved
    This file is a part of HandCricket project
"""


import discord
from discord.ext import commands

from datetime import datetime
from os import getenv
from utils import *
import traceback
import aiosqlite
import time
import asyncio
import logging
from json import loads

logging.basicConfig(level=logging.INFO)
config = json.load("config.json")

if config['stage'] == 'Prod':
    default_prefix = config['default_prefix']  
    token = config['token']
else: 
    default_prefix = config['beta_prefix']
    token = config['beta_token']

def get_prefix(bot, message: discord.Message):
    async def __get_prefix(bot, message: discord.Message):

        bot_id = bot.user.id

        if message.guild is None:
            server_prefix = ''
        
        else:
            try:
                server_prefix = bot.guild_settings_cache[message.guild.id]['prefix']
            except Exception as e:
                print("Command Query Error! -> ", e); traceback.print_exc()
                server_prefix = default_prefix[0]

                if bot.db == None:
                    server_prefix = default_prefix[0]

                else:
                    cursor = await bot.db.execute_fetchall("SELECT guild_id, prefix FROM prefixes WHERE guild_id == (?);", (message.guild.id,))

                    if len(cursor) == 0:
                        to_enter = (message.guild.id, default_prefix[0])
                        await bot.db.execute_insert("INSERT INTO prefixes(guild_id, prefix) VALUES (?,?);", to_enter)
                        await bot.db.commit()
                        server_prefix = default_prefix[0]
                    else:
                        server_prefix = cursor[0][1]
                        bot.guild_settings_cache[message.guild.id] = {'prefix':default_prefix[0]}

        list_prefixes = [f'<@{bot_id}> ', f'<@!{bot_id}> ', default_prefix[0], default_prefix[1], server_prefix]
        return list_prefixes
    return __get_prefix(bot, message)


ClientIntents = discord.Intents(guilds= True, members=True, bans=False, 
                                emojis=True, integrations=False, webhooks=False, 
                                invites=False, voice_states=False, presences=False, 
                                messages=True, reactions=True, typing=False)

class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = get_prefix,
            case_insensitive = True,
            description = "I host single and multiplayer games for Hand Cricket!",
            intents = ClientIntents,
            max_messages = 200,
            self_bot = False,
            owner_id = 278094147901194242,
            allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=True),
            activity = discord.Activity(type=discord.ActivityType.listening, name=f'{self.prefix}help'),
            # help_command = CustomHelpCommand()
        )
    
        self.version = '5.0a'
        self.log = logging.getLogger()
        self.games = {}
        self.db = None 
        self.debug_channel = 753194446710898698
        self.bot_extensions = ['defaultcog','ownercog','multiplayer','eventloops',
                                'misccog','runrace','general','helpcommand', 'social' ] 
        self.launched_at = None

        self.invite_link = 'https://discord.com/api/oauth2/authorize?client_id=753191385296928808&permissions=1144388672&scope=bot'
        self.support_server = 'https://discord.gg/Mb9s5sVkSz'

        self.topgg = 'https://top.gg/bot/753191385296928808'
        self.bfd = 'https://botsfordiscord.com/bot/753191385296928808'

        self.help_end_footer = 'For more help on a command, use {}help <command>'.format(self.prefix) +\
                            ' OR {}help <category> for more help about a specific category.'.format(self.prefix)
        self.last_message_cache = {}
        self.user_profile_cache = {}
        
        ext_count = 0
        for extension in self.bot_extensions: 
            try: 
                self.load_extension(extension) 
                print('loaded', extension)
                ext_count += 1  

            except commands.ExtensionError as e: 
                print(f'Extension {extension} could not be loaded:\n', e); 
                traceback.print_exc(); 
                continue
        print(f"Loaded {ext_count} of {len(self.bot_extensions)} Cogs.")

        self.loop.create_task(self.on_bot_start())

    async def on_ready(self):
        print("\n\nWe have successfully logged in as {0.user} \n".format(self) +\
                "Discord.py version info: {}\n".format(discord.version_info) +\
                "Discord.py version: {}\n".format(discord.__version__))

        return ##await self.get_channel(self.debug_channel).send("Successfully loaded all cogs.")

    async def on_bot_start(self):

        self.db = await aiosqlite.connect('data.db')
        print("Succesfully established connection with database")

        self.guild_settings_cache = {}
        prefix_data = await self.db.execute_fetchall("SELECT guild_id, prefix FROM prefixes;")
        for row in prefix_data:
            self.guild_settings_cache[row[0]] = {'prefix': row[1]}
        print("Guild settings successfully cached.")

        self.load_extension('globalevents')
        print("Loaded globalevents cog.")
        
        user_data = await self.db.execute_fetchall("SELECT * FROM profiles;")
        for row in user_data:
            self.user_profile_cache[row[0]] = {
                'name': row[1], 'description': row[2], 'matches_played': row[3], 'matches_won': row[4],
                'matches_lost': row[5], 'runs': row[6], 'balls': row[7], 'wickets': row[8], 
                'wickets_lost': row[9], 'highest_score': row[10], 'hattricks': row[11], 'ducks': row[12],
                'batting_average': row[13], 'match_log': loads(row[14]), 'status': row[15], 'created_at': row[16],
                'field5': row[17], 'field6': row[18], 'field19': row[19], 'field20': row[20]
            }
        print("User profiles successfully cached.")
        return

    @property
    def send_invite_link(self):
        return self.invite_link

    @property
    def send_support_server(self):
        return self.support_server

    @property
    def prefix(self):
        return default_prefix[0]

    def run(self, *args, **kwargs):
        self.launched_at = datetime.now()
        super().run(*args, **kwargs)

    async def on_message(self, message):
        if message.content.replace('!', '') == self.user.mention:
            await message.channel.send("My default prefix is `{}`".format(self.prefix))
        return await super().on_message(message)

    async def on_disconnect(self):
        return print(f"The bot has successfully logged out. @ {datetime.now()}")

    async def get_context(self, message):
        return await super().get_context(message, cls=CustomContext)
        # One manual change in bot.py. Line 862.

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.CommandNotFound): 
            return

        elif isinstance(exception, commands.CheckFailure): 
            return await context.send(exception)
            
        elif isinstance(exception, commands.NotOwner): 
            return

        elif isinstance(exception, commands.CommandOnCooldown): 
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description = ":x: Command on cooldown, try after {} seconds.".format(round(exception.retry_after)))
            )

        elif isinstance(exception, commands.MaxConcurrencyReached): 
            return await context.send("Please wait!")

        elif isinstance(exception, discord.InvalidArgument):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description = exception)
            )

        elif isinstance(exception, commands.MissingRequiredArgument):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description =f":x: Missing one or all arguements. \n\nCommand Usage:\n```{context.command.usage[0]}```")
            )

        elif isinstance(exception, commands.ArgumentParsingError):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description =f":x: Invalid arguements. \n\nCommand Usage:\n```{context.command.usage[0]}```")
            )

        elif isinstance(exception, commands.BadArgument):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description =f":x: Invalid arguements. \n\nCommand Usage:\n```{context.command.usage[0]}```")
            )

        elif isinstance(exception, commands.TooManyArguments):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description =f":x: Too many arguements were given. \n\nCommand Usage:\n```{context.command.usage[0]}```")
            )

        elif isinstance(exception, commands.MessageNotFound):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description ="Member not found!")
            )

        elif isinstance(exception, commands.UserNotFound):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description ="User not found!")
            )

        elif isinstance(exception, commands.ChannelNotFound): 
            return

        elif isinstance(exception, commands.BadUnionArgument):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description =f':x: Invalid arguements. \n\nCommand Usage:\n```{context.command.usage[0]}```')
            )

        elif isinstance(exception, commands.MissingPermissions):
            return await context.send(
                embed = discord.Embed(color = BASICRED,
                description =':x: Missing permissions! {}'.format(exception.missing_perms))
            )

        else: 
            print("Print an error occured with command named", context.invoked_with, "guild_id",
            context.guild.id if context.guild is not None else "None", 
            self.games.get(context.channel.id, None).type if self.games.get(context.channel.id, None) is not None else "None")
            if self.games.get(context.channel.id, None) is not None and self.games.get(context.channel.id, None).type == GameType.MULTI:
                print(self.games.get(context.channel.id, None).__str__())
            return await super().on_command_error(context, exception)

    async def on_reaction_add(self, reaction, user):
        if user.bot == True:
            return
        if not str(reaction.emoji) == misc_emojis['rtj']:
            return
        if reaction.message.channel.id not in self.games:
            return
        game = self.games[reaction.message.channel.id]
        if game.type not in (GameType.MULTI, GameType.RUNRACE):
            return
        to_decline = check_for_other_games(self, user)
        if to_decline == True: return

        if game.debounce == False:
            game.debounce = True
            game.players_queue.append(user)
            await asyncio.sleep(3)

            joined = ""
            for user in game.players_queue:
                if game.type == GameType.MULTI and len(game.players) >= 20: break
                elif game.type == GameType.RUNRACE and len(game.players) >= 10: break

                if user not in game.players:
                    game.players.append(user)
                    if game.type == GameType.MULTI:
                        if game.shuffled == True:
                            if len(game.TeamA) < len(game.TeamB):
                                game.TeamA.append(user)
                            else:
                                game.TeamB.append(user)
                    joined += f"{user.name}, "
                    continue
                else:
                    game.players_queue.remove(user)
                    continue

            game.debounce = False
            game.players_queue = []
            return await game.channel.send(f"**{joined[:-2]} has joined the game. ✅**")
        else: 
            game.players_queue.append(user)
            return 

    async def on_guild_channel_delete(self, channel):
        if channel.id in self.games: 
            self.games.pop(channel.id) 
        return

    async def on_guild_join(self, guild: discord.Guild):
        to_enter = (guild.id, default_prefix[0])
        await self.db.execute_insert("INSERT INTO prefixes(guild_id, prefix) VALUES (?,?);", to_enter)
        await self.db.commit()
        self.guild_settings_cache[guild.id] = {'prefix': default_prefix[0]}

    async def on_guild_remove(self, guild: discord.Guild):
        for channel in guild.channels:
            if channel.id in self.games:
                self.games.pop(channel.id) 

        await self.db.execute("DELETE FROM prefixes WHERE guild_id == (?);", (guild.id,))
        await self.db.commit()
        self.guild_settings_cache.pop(guild.id)
        return

    async def on_member_remove(self, member: discord.Member):
        for game in self.games.values():
            if game.type in (GameType.SINGLE, GameType.DOUBLE, GameType.RUNRACE):
                continue
            if member in game.players:
                game.players.remove(member)

                game.bot_count += 1
                count = game.bot_count
                BOT = FBot(count=count)
                game.players.append(BOT)

                if member.id in game.TeamA:
                    stats = game.TeamA.pop(member.id)

                    game.TeamA[BOT.id] = stats
                    stats['player'] = BOT
                    stats['is_human'] = False
                    for key in ['name', 'runs', 'balls', 'wickets']:
                        game.TeamA[key] = game.TeamA.pop(key)

                    if member.id == game.curr_batsman['player'].id: game.curr_batsman = game.TeamA[BOT.id]
                    elif member.id == game.curr_bowler['player'].id: game.curr_bowler = game.TeamA[BOT.id]
                    else: pass

                elif member.id in game.TeamB:
                    stats = game.TeamB.pop(member.id)

                    game.TeamB[BOT.id] = stats
                    stats['player'] = BOT
                    stats['is_human'] = False
                    for key in ['name', 'runs', 'balls', 'wickets']:
                        game.TeamB[key] = game.TeamB.pop(key)

                    if member.id == game.curr_batsman['player'].id: game.curr_batsman = game.TeamB[BOT.id]
                    elif member.id == game.curr_bowler['player'].id: game.curr_bowler = game.TeamB[BOT.id]
                    else: pass

                return await send_message(bot=self, ctx=game.channel, content=
                f"**{member.name}** has left the server, therefore player has been kicked"
                f"and has been replaced by {BOT.mention}")    

    async def close(self):
        for game in self.games.values():
            await game.channel.send(":warning: All ongoing matches has been abandoned due to bot being shut down! Apologies for the inconvenience.")
        self.games.clear()
        self.unload_extension("globalevents")
        await asyncio.sleep(0.25)

        await self.db.commit()
        await self.db.close()
        return await super().close()

if __name__ == "__main__":
    Client().run(token, reconnect=True)
