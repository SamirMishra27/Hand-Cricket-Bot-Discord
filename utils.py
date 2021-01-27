import random
from enum import Enum, IntEnum, auto
from discord import Member, Embed
from discord.ext import commands
from datetime import datetime

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

class Innings(IntEnum):
    ONE = auto()
    TWO = auto()

MAYABLUE = 0x73C2FB
SPRINGGREEN = 0x00FA9A


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
            'There is no multiplayer hand cricket match going here.'
            '`To host one, use the command create first!`')
            
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

        if game.shuffled == False:
            raise commands.CheckFailure('You have not shuffuled the players yet. use .shuffle to shuffle the players first.')
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
            raise commands.CheckFailure('This is a Multiplayer match only command.')
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
    'spacing' : (0, 8, 8, 8, 0, -1.2, -0.2, 5.5, -1.2, -0.2, 5.5),
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

class CustomHelpCommand(commands.DefaultHelpCommand):

    def __init__(self):
        super().__init__(
            indent = 8,
            verify_checks=False
        )

    async def send_bot_help(self, mapping):
        bot = self.context.bot
        embed = Embed()
        embed.colour = MAYABLUE
        embed.set_thumbnail(url=str(bot.user.avatar_url))
        row_1 = (
            f'My prefix in this server is `{self.context.guild_prefix}`'
            f'My default prefix is `{bot.prefix}`'
            f'\nYou can also mention me instead.'
        )
        row_5 = (
            f'[Invite Link]({bot.send_invite_link}) to add the bot to your server!'
            f'\n[Support Server Link]({bot.send_support_server}) for more help and suggestions and feedback.'
   )
     
        for cog, commands in mapping.items():
            cog_name = getattr(cog, '__cog_name__', 'Other')
            if cog_name in ('Owner','EventLoops','Six'):
                continue
            
            cmd_list = ''
            if cog_name in ('Multiplayer', 'Default', 'Misc'):
                cmd_list += f'*{cog.cog_brief}*\n'
            for command in commands:
                if command.hidden == True:
                    continue
                cmd_list += f"{bot.prefix}{spacing(command.name)}  -  `{command.brief}`\n"
            embed.add_field(name=cog_name, value=cmd_list, inline=False)

        row_6 = bot.help_end_footer
        embed.set_footer(text=row_6) 
        embed.description = row_1+'\n\n'+row_5
        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        if command.hidden:
            return

        bot = self.context.bot
        usage = self.get_command_signature(command)
        embed = Embed(title=f'command {command.name}')
        embed.set_author(name=bot.user.name,icon_url=str(bot.user.avatar_url))
        embed.description = (
            f":label: | **Usage:** \n`{command.usage[0]}`"
            f"\n\n:page_with_curl: | **Description:**\n {command.help}" #command.brief
        )
        if command.usage[1] is not None:
            embed.description += f"\n\n:speech_balloon: | **Example:**\n"
            for eg in command.usage[1]:
                embed.description += f"→ *{eg}*\n"

        embed.colour = MAYABLUE
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        bot = self.context.bot
        if cog.qualified_name in ('Owner','EventLoops'):
            return

        cmd_list = ''
        for command in cog.walk_commands():
            if command.hidden: continue
            cmd_list += f'{self.context.bot.prefix}{command.name} - {command.brief}\n'
        embed = Embed(title=cog.qualified_name)
        embed.set_author(name=bot.user.name, icon_url=str(bot.user.avatar_url))
        embed.description = (
            f"{cog.cog_description}\n\n"
            f"{cmd_list}"
        )
        embed.colour = MAYABLUE
        return await self.get_destination().send(embed=embed)

async def log_game(ctx, type):
    to_enter = (ctx.guild.id if ctx.guild is not None else 'Private context', f'{type}', str(datetime.now()))
    with ctx.bot.db as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO matches VALUES (?,?,?)", to_enter)
        conn.commit()

class CustomContext(commands.Context):

    @property
    def guild_prefix(self):
        if self.guild is None:
            return self.bot.prefix
        with self.bot.db as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM prefixes WHERE guild_id == (?)", (self.guild.id,))
            return cur.fetchone()[1]

# class UtilsCog(commands.Cog):
#     pass
# def setup(bot):
#     bot.add_cog(UtilsCog(bot)),'utils'
def check_for_other_games(bot, author): 
    to_decline = False
    for game in bot.games.values():
        if game.type == GameType.SINGLE and author.id == game.player:
            to_decline = True
        if game.type == GameType.DOUBLE and author.id in game.players:
            to_decline = True
        if game.type == GameType.MULTI and author in game.players:
            to_decline = True
    return to_decline