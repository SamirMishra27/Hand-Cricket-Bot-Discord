import random
from enum import Enum, IntEnum, auto
from discord import Member, Embed, ChannelType
from discord.ext import commands
from datetime import datetime
import time
import asyncio
import json

def cointoss(message):
    if message.content.lower() == random.choice(['heads','tails']):
        player_won = True 
        coin_result = "You won the toss! Choose bat or bowl? ( bat / bowl )"
    
    else:
        player_won = False
        coin_result = "You lost the toss!"

    return player_won, coin_result

class GameType(Enum):
    SINGLE = 'Player vs Bot'
    DOUBLE = 'Player vs Player'
    MULTI  = 'Multiplayer'
    RUNRACE = 'Run Race'

class Innings(IntEnum):
    ONE = auto()
    TWO = auto()

class Status(Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive" 

MAYABLUE = 0x73C2FB
SPRINGGREEN = 0x00FA9A
BASICRED = 0xe74c3c

action_emojis = {'0️⃣': 0, '1️⃣':1, '2️⃣':2, '3️⃣':3, '4️⃣':4, '5️⃣':5, '6️⃣':6}
misc_emojis = {
    'rtj':'<:emoji_3:813094554378567740>',
    'load':'<a:emoji_2:781233777258004540>',
    'town':'<:emoji_1:756240523177623575>'  
    }
live_gif = "https://cdn.discordapp.com/attachments/663324452934778880/817117402071302174/ezgif-4-515aefdc0865.gif"    

with open("strings.json") as f:
    strings = json.load(f)

class FBot:
    def __init__(self, count):
        self.name = f'Bot' + f'{str(count)}'
        self.id = 100 + count

    def __str__(self):
        return f'name={self.name}, id={self.id}'

    @property
    def mention(self):
        return f"**{self.name}**"

    async def send(self, *args): pass

def game_only():
    async def predicate(ctx):
        if not ctx.guild: 
            raise commands.CheckFailure('This command can only be used in server channels.')

        if ctx.channel.id not in ctx.bot.games:
            raise commands.CheckFailure(
            'There is no multiplayer or run race hand cricket match going here.'
            '`To host one, use the command create / runrace first!`')
            
        return True

    return commands.check(predicate)

def host_only():
    async def predicate(ctx):
        game = ctx.bot.games[ctx.channel.id]
        
        if ctx.author.id != game.host:
            raise commands.CheckFailure('Only match hosts can use this command.')
        return True

    return commands.check(predicate)

def participants_only():
    async def predicate(ctx):
        game = ctx.bot.games[ctx.channel.id]

        if game.type in (GameType.SINGLE, GameType.DOUBLE):
            return True
        if ctx.author not in game.players:
            raise commands.CheckFailure('You are not participating in this match.')
        return True
    
    return commands.check(predicate)

def before_game_only():
    async def predicate(ctx):
        game = ctx.bot.games[ctx.channel.id]

        if game.game_started == True or game.game_started == 'pregame':
            raise commands.CheckFailure('Cannot use this command after the game has started.')
        return True

    return commands.check(predicate=predicate)

def after_game_only():
    async def predicate(ctx):
        game = ctx.bot.games[ctx.channel.id]

        if game.game_started == False or game.game_started == 'pregame':
            raise commands.CheckFailure('Match has not started yet!')
        return True
    
    return commands.check(predicate=predicate)

def shuffled_only():
    async def predicate(ctx):
        game = ctx.bot.games[ctx.channel.id]

        if game.type == GameType.RUNRACE:
            return True
        if game.shuffled == False:
            raise commands.CheckFailure('You have not shuffuled the players yet. use command shuffle to shuffle the players first.')
        return True

    return commands.check(predicate)

def min_four_players_only():
    async def predicate(ctx):
        game = ctx.bot.games[ctx.channel.id]

        if len(game.players) < 4:
            raise commands.CheckFailure('At least 4 players are needed to use this command.')
        return True

    return commands.check(predicate=predicate)

def multiplayer_game_only():
    async def predicate(ctx):
        if ctx.bot.games[ctx.channel.id].type in (GameType.SINGLE, GameType.DOUBLE):
            raise commands.CheckFailure('This is a Multiplayer match and Run Race only command.')
        return True

    return commands.check(predicate)

def multiplayer_mode_only():
    async def predicate(ctx):
        if ctx.bot.games[ctx.channel.id].type != GameType.MULTI:
            raise commands.CheckFailure('This is a Multiplayer match only command.')
        return True

    return commands.check(predicate)

def runrace_mode_only():
    async def predicate(ctx):
        if ctx.bot.games[ctx.channel.id].type != GameType.RUNRACE:
            raise commands.CheckFailure('This is a Run Race match only command.')
        return True    

    return commands.check(predicate)

def overs(balls):
    return f"{int(balls / 6)}.{balls % 6}"

def spacing(name):    
    return name + (10-len(name))*' '

def pz(number): #Pluralise
    return 's' if number > 1 else ''
    
## 1 1 3 1 2 font_sizes
## 2 2 3 2 2 3 font_sizes

template1 = {
    'font_sizes' : (60, 50, 36, 30),
    'coordinates' : (
        (60,30), (65,150), (780, 170), (1040, 150), (320, 1180),
        (60,280), (480,280), (560,290), (660,280), (1080,280), (1160,333)
        ),
    'colour' : (255,255,255),
    'spacing' : (0, 7, 0, 16, 0, 16.8, 16, 29, 16.8, 16, 30),
    'newline' : ('\n'*8, '\n'*15, '\n'*7, '\n'*2, '\n'*2)
}

template2 = {
    'font_sizes' : (48, 34, 28, 26),
    'coordinates' : (
        (60,30), (60,140), (780,160), (1040,140), (400,1140),
        (60,225), (470,230), (530,240), (660, 225), (1080,230), (1170,240)
    ),
    'colour' : (255,255,255),
    # 'spacing' : (0, 8, 8, 8, 0, -1.2, -0.2, 5.5, -1.2, -0.2, 5.5),5.4
    'spacing' : (0, 8, 8, 8, 0, -1.4, 0.0, 6.0, -1.4, -0.4, 5.3),
    'newline' : ('\n'*9, '\n'*14, '\n'*9, '\n'*4, '\n'*3)
}

template3 = {
    'font_sizes' : (40, 28, 24, 22),
    'coordinates' : (
        (60,30), (60,115), (800,130), (1100,115), (460,1220),
        (60,175), (480,175), (540, 175), (660,175), (1080,175), (1160,175)
    ),
    'colour' : (255,255,255),
    'spacing' : (0, 0.8, 8.6, 0.8, 0, -7.2, -7.2, -4.15, -7.2, -7.2, -4.15),
    'newline' : ('\n'*14, '\n'*17, '\n'*14, '\n'*6, '\n'*6)
}

async def log_game(ctx, type):
    to_enter = (ctx.guild.id if ctx.guild is not None else 'Private context', f'{type}', str(datetime.now()))

    await ctx.bot.db.execute_insert("INSERT INTO matches(guild_id, game_type, date_time) VALUES (?,?,?);", to_enter)
    await ctx.bot.db.commit()

class CustomContext(commands.Context):

    @property
    def guild_prefix(self):
        prefix = self.bot.guild_settings_cache[self.guild.id]['prefix']
        print(prefix, self.channel.id)
        return prefix

    async def send(
        self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, 
        nonce=None, allowed_mentions=None, reference=None, mention_author=None, view=None
    ):
        # if self.guild is not None:
        if self.guild is not None:
            last_timestamp = self.bot.last_message_cache.get(self.guild.id, 0)
            curr_time = time.time()
            if curr_time - last_timestamp > 1.0:
                
                self.bot.last_message_cache[self.guild.id] = curr_time
                return await super().send(
                    content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, 
                    nonce=nonce, allowed_mentions=allowed_mentions, mention_author=mention_author, view=view
                )
            else:    
                await asyncio.sleep(curr_time - last_timestamp + 0.800)
                
                curr_time = time.time()
                self.bot.last_message_cache[self.guild.id] = curr_time
                return await super().send(
                    content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, 
                    nonce=nonce, allowed_mentions=allowed_mentions, mention_author=mention_author, view=view
                )
        else:
            last_timestamp = self.bot.last_message_cache.get(self.channel.id, 0)
            curr_time = time.time()
            if curr_time - last_timestamp > 1.0:
                
                self.bot.last_message_cache[self.channel.id] = curr_time
                return await super().send(
                    content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, 
                    nonce=nonce, allowed_mentions=allowed_mentions, mention_author=mention_author, view=view
                )
            else:
                await asyncio.sleep(curr_time - last_timestamp + 0.800)
                
                curr_time = time.time()
                self.bot.last_message_cache[self.channel.id] = curr_time
                return await super().send(
                    content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, 
                    nonce=nonce, allowed_mentions=allowed_mentions, mention_author=mention_author, view=view
                )

def check_for_other_games(bot, author): 
    to_decline = False
    for game in bot.games.values():
        if game.type == GameType.SINGLE and author.id == game.player.id:
            to_decline = True
        if game.type == GameType.DOUBLE and author.id in game.players:
            to_decline = True
        if game.type == GameType.MULTI and author in game.players:
            to_decline = True
        if game.type == GameType.RUNRACE and author in game.players:
            to_decline = True
    return to_decline

    
async def send_message(bot, ctx=None, user=None, content='_____', embed=None, file=None):
    if user == None:
        # if ctx.guild is not None:
        if hasattr(ctx, 'guild'):
            last_timestamp = bot.last_message_cache.get(ctx.guild.id, 0)
            curr_time = time.time()
            if curr_time - last_timestamp > 1.0:
                await ctx.send(content=content, embed=embed, file=file)
                bot.last_message_cache[ctx.guild.id] = curr_time
            else:    
                await asyncio.sleep(curr_time - last_timestamp + 0.800)
                await ctx.send(content=content, embed=embed, file=file)
                curr_time = time.time()
                bot.last_message_cache[ctx.guild.id] = curr_time
        else:
            last_timestamp = bot.last_message_cache.get(ctx.channel.id, 0)
            curr_time = time.time()
            if curr_time - last_timestamp > 1.0:
                await ctx.send(content=content, embed=embed, file=file)
                bot.last_message_cache[ctx.channel.id] = curr_time
            else:
                await asyncio.sleep(curr_time - last_timestamp + 0.800)
                await ctx.send(content=content, embed=embed, file=file)
                curr_time = time.time()
                bot.last_message_cache[ctx.channel.id] = curr_time
                
            
    elif ctx == None:
        last_timestamp = bot.last_message_cache.get(user.id, 0)
        curr_time = time.time()
        if curr_time - last_timestamp > 1.0:
            await user.send(content)
            bot.last_message_cache[user.id] = curr_time
        else:    
            await asyncio.sleep(curr_time - last_timestamp + 0.800)
            await user.send(content)
            curr_time = time.time()
            bot.last_message_cache[user.id] = curr_time
            

async def check_for_milestone(player, destination, last_score, curr_score, bot):
    if curr_score >= 50 and last_score < 50:
        milestone = "FIFTY!"
    elif curr_score >= 100 and last_score < 100:
        milestone = "CENTURY!"
    elif curr_score >= 150 and last_score < 150:
        milestone = "ONE FIFTY!"
    else:
        return

    gif = random.choice(strings["milestone_runs"])
    await send_message(bot=bot, ctx=None, user=destination, 
    content=f"**{player}** got a **{milestone}!**\n{gif}")

async def check_for_hattrick(player, timeline, destination, wickets, to_count=True, bot="bot"):
    hattrick = False
    message = ""
    gif = random.choice(strings["milestone_wickets"])
    if timeline[5] == "W" and timeline[4] == "W" and timeline[3] == "W":
        message = f"**{player} got a Hat-trick!!**\n{gif}"
        hattrick = True

    if to_count == True:
        if wickets == 3 or wickets == 5:
            message += f"\n**{player}{' also' if hattrick == True else ''} got {3 if wickets == 3 else 5} Wickets!!**"

    if message != "":
        await send_message(bot=bot, ctx=None, user=destination, content=message)
    return hattrick