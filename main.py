"""
    Copyright © 2020-2021 SamirMishra27
    This file is a part of HandCricket project
"""


import discord
from discord.ext import commands

from datetime import datetime
from os import getenv
from utils import FBot, CustomHelpCommand, CustomContext, GameType, check_for_other_games
import traceback
import sqlite3

# from keep_alive import keep_alive

# default_prefix = "h!", "H!"
default_prefix = ("..", "...")

def get_prefix(bot, message: discord.Message):
    bot_id = bot.user.id

    if message.guild is None:
        server_prefix = ''
    
    else:
        try:
            with bot.db as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM prefixes WHERE guild_id == (?)", (message.guild.id,))
                server_prefix = cur.fetchone()[1]
        except Exception as e:
            print("Command Query Error! -> ", e); traceback.print_exc()
            server_prefix = default_prefix[0]

    list_prefixes = [f'<@{bot_id}> ', f'<@!{bot_id}> ', default_prefix[0], default_prefix[1], server_prefix]
    return tuple(list_prefixes)

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
            max_messages = 100,
            self_bot = False,
            owner_id = 278094147901194242,
            allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=True),
            activity = discord.Activity(type=discord.ActivityType.listening, name=f'{self.prefix}help'),
            help_command = CustomHelpCommand()
        )
    
        self.version = '2.0' 
        self.games = {}
        self.db = sqlite3.connect('data.db')
        self.debug_channel = 753194446710898698
        self.bot_extensions = ['defaultcog','ownercog','misccog','eventloops','multiplayer'] 
        self.launched_at = None
        self.invite_link = 'https://discord.com/api/oauth2/authorize?client_id=753191385296928808&permissions=1144388672&scope=bot'
        self.support_server = 'https://discord.gg/Mb9s5sVkSz'
        self.topgg = 'https://top.gg/bot/753191385296928808'
        self.bfd = 'https://botsfordiscord.com/bot/753191385296928808'
        self.help_end_footer = 'For more help on a command, use {}help <command>'.format(self.prefix) +\
                            ' OR {}help <category> for more help about a specific category.'.format(self.prefix)

    async def on_ready(self):
        print("\n\nWe have successfully logged in as {0.user} \n".format(self) +\
                "Discord.py version info: {}\n".format(discord.version_info) +\
                "Discord.py version: {}\n".format(discord.__version__))
        
        ext_count = 0
        for extension in self.bot_extensions: 
            try: 
                self.load_extension(extension) 
                print('loaded', extension)
                ext_count += 1  
            except commands.ExtensionError as e: 
                print('Extension {extension} could not be loaded:\n', e); traceback.print_exc(); 
                continue
        print(f"Loaded {ext_count} of {len(self.bot_extensions)} Cogs.")
        return await self.get_channel(self.debug_channel).send("Successfully loaded all cogs.")

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

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.CommandNotFound): 
            return

        elif isinstance(exception, commands.CheckFailure): 
            return await context.send(exception)
            
        elif isinstance(exception, commands.NotOwner): 
            return

        elif isinstance(exception, commands.CommandOnCooldown): 
            return await context.send(":x: Command on cooldown, try after {} seconds.".format(round(exception.retry_after)))

        elif isinstance(exception, commands.MaxConcurrencyReached): 
            return await context.send("Please wait!")

        elif isinstance(exception, discord.InvalidArgument):
            return await context.send(exception)

        elif isinstance(exception, commands.MissingRequiredArgument):
            return await context.send(":x: Missing one or all arguements.")

        elif isinstance(exception, commands.ArgumentParsingError):
            return await context.send(":x: Invalid arguements.")

        elif isinstance(exception, commands.BadArgument):
            return await context.send(":x: Invalid arguements.")

        elif isinstance(exception, commands.TooManyArguments):
            return await context.send(":x: Too many arguements were given.")

        elif isinstance(exception, commands.MessageNotFound):
            return await context.send("Member not found!")

        elif isinstance(exception, commands.UserNotFound):
            return await context.send("User not found!")

        elif isinstance(exception, commands.ChannelNotFound): 
            return

        elif isinstance(exception, commands.BadUnionArgument):
            return await context.send(':x: Invalid arguements.')

        elif isinstance(exception, commands.MissingPermissions):
            return await context.send(':x: Missing permissions! {}'.format(exception.missing_perms))

        else: return await super().on_command_error(context, exception)

    async def on_reaction_add(self, reaction, user):
        if user.bot == True:
            return
        if not str(reaction.emoji) == '✅':
            return
        if reaction.message.channel.id not in self.games:
            return
        game = self.games[reaction.message.channel.id]
        to_decline = check_for_other_games(self, user)
        if to_decline == True: return
        if user not in game.players:
            game.players.append(user)
            if game.shuffled == True:
                if len(game.TeamA) < len(game.TeamB):
                    game.TeamA.append(user)
                else:
                    game.TeamB.append(user)
            return await game.channel.send(f"**{user.name} has joined the game. ✅**")
        else: return 

    async def on_guild_channel_delete(self, channel):
        if channel.id in self.games: 
            self.games.pop(channel.id) 
        return

    async def on_guild_join(self, guild: discord.Guild):
        to_enter = (guild.id, default_prefix[0])
        with self.db as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO prefixes VALUES (?,?)", to_enter)
            self.db.commit()

    async def on_guild_remove(self, guild: discord.Guild):
        for channel in guild.channels:
            if channel.id in self.games:
                self.games.pop(channel.id) 

        with self.db as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM prefixes WHERE guild_id == (?)", (guild.id,))
            self.db.commit()
        return

    async def on_member_remove(self, member: discord.Member):
        for game in self.games.values():
            if game.type in (GameType.SINGLE, GameType.DOUBLE):
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

                return await game.channel.send(
                    f"**{member.name}** has left the server, therefore player has been kicked"
                    f"and has been replaced by {BOT.mention}")


if __name__ == "__main__":
    Token = getenv('TOKEN')
    keep_alive()
    Client().run(Token, reconnect=True)