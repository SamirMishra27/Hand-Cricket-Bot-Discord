from utils import *
from time import time
from os import remove
from asyncio import sleep
from random import randint

from discord.ext.commands import Context
from discord import Embed, Forbidden, File, Member

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

class MultiplayerGame:

    def __init__(self, ctx: Context, bot):

        self.type = GameType.MULTI
        self.created_at = None
        self.host = None
        self.game_id = randint(4444, 7777)
        self.innings = 0
        self.game_started = False
        self.shuffled = False
        self.bot_count = 0
        self.overs = None
        self.channel = ctx.channel
        self.bot = bot
        self.result = None
        self.is_updating = False

        self.players: list = []
        self.TeamA: list = []
        self.TeamB: list = []

        self.toss_winner = None
        self.TeamA_turn = None
        self.curr_batsman = None
        self.curr_bowler = None 
        self.batting_team = None
        self.bowling_team = None
        self.batting_team_stats = {}
        self.bowling_team_stats = {}
        self.team_settings = { 'Team A name':'Team A' , 'Team B name':'Team B' }

    @classmethod
    def create(cls, ctx, bot):
        new_game = cls(ctx=ctx, bot=bot)
        new_game.players.append(ctx.author)
        new_game.created_at = time()
        new_game.host = ctx.author.id
        return new_game

    async def update(self):
        if self.game_started == True:
            return

        else:
            diff = time() - self.created_at
            if diff > 15 * 60:## # 
                try:
                    await self.channel.send("Match has been abandoned due to taking too long to start.")
                except Exception as e:
                    return
                finally:
                    self.bot.games.pop(self.channel.id)


            else: return

    def __str__(self):
        
        objstr = ''.join([f'Type={self.type} {self.type.value}, created_at={self.created_at}, host={self.host}, ',
                        f'game_started={self.game_started}, shuffled={self.shuffled}, bot_count={self.bot_count},'
                        f'overs={self.overs}, innings={self.innings} channel={self.channel}, bot={self.bot}, players, TeamA, TeamB,',
                        f'toss_winner={self.toss_winner}, TeamA_turn={self.TeamA_turn}, curr_batsman={self.curr_batsman}, ',
                        f'curr_bowlers={self.curr_bowler}, batting_team={self.batting_team}, bowling_team={self.bowling_team}'
        ]) 
        return objstr

    async def initialise(self):
        self.game_started = True
        dict_a, dict_b = {}, {}

        for player in self.TeamA:
            dict_a[player.id] = {'player': player,
                                 'runs': 0,
                                 'balls': 0,
                                 'wickets': 0,
                                 'runs_given': 0,
                                 'balls_given': 0,
                                 'last_action': 0,
                                 'is_human': True if len(str(player.id)) > 4 else False,
                                 'is_out': False,
                                }

        dict_a.update( {'name': self.team_settings['Team A name'], 'runs': 0, 'balls': 0, 'wickets': 0} )
        self.TeamA = dict_a

        for player in self.TeamB:
            dict_b[player.id] = {'player': player,
                                 'runs': 0,
                                 'balls': 0,
                                 'wickets': 0,
                                 'runs_given': 0,
                                 'balls_given': 0,
                                 'last_action': 0,
                                 'is_human': True if len(str(player.id)) > 4 else False,
                                 'is_out': False,
                                }

        dict_b.update( {'name': self.team_settings['Team B name'], 'runs': 0, 'balls': 0, 'wickets': 0} )
        self.TeamB = dict_b
        self.batting_team = self.TeamA if self.TeamA_turn == 'bat' else self.TeamB
        self.bowling_team = self.TeamA if self.TeamA_turn == 'bowl' else self.TeamB
        self.innings = Innings.ONE #1
        return True

    async def change_innings(self):

        self.innings = Innings.TWO #2
        self.batting_team, self.bowling_team = self.bowling_team, self.batting_team
        return True

    async def check_endgame(self):

        if self.TeamA['runs'] == self.TeamB['runs']:
            self.result = f"This match was a tie!" + " :handshake:"

        elif self.TeamA_turn == 'bat':

            if self.TeamA['runs'] > self.TeamB['runs']:
                diff = self.TeamA['runs'] - self.TeamB['runs']
                self.result = f"{self.team_settings['Team A name']} won the game by {diff} run{pz(diff)}." + " 🎊"

            elif self.TeamA['runs'] < self.TeamB['runs']:
                diff = len(self.TeamB) - self.TeamB['wickets'] - 4
                self.result = f"{self.team_settings['Team B name']} won the game by {diff} wicket{pz(diff)}." + " 🎊"

        elif self.TeamA_turn == 'bowl': 

            if self.TeamA['runs'] > self.TeamB['runs']:
                diff = len(self.TeamA) - self.TeamA['wickets'] - 4
                self.result = f"{self.team_settings['Team A name']} won the game by {diff} wicket{pz(diff)}." + " 🎊"

            elif self.TeamA['runs'] < self.TeamB['runs']:
                diff = self.TeamB['runs'] - self.TeamA['runs']
                self.result = f"{self.team_settings['Team B name']} won the game by {diff} run{pz(diff)}." + " 🎊"

        return True

    async def next_bowler(self, index, keys):

        index += 1
        if index == int( len(self.players)/2 ):
            index = 0
        self.curr_bowler = self.bowling_team[keys[index]]
        return index, keys

    async def send_msg(self, who, msg: str):

        await sleep(0.3)
        if who == 'BATSMAN':
            try: 
                # await self.curr_batsman['player'].send(msg)
                await send_message(bot=self.bot, ctx=None, user=self.curr_batsman['player'], content=msg)
            except Forbidden: 
                return

        elif who == 'BOWLER':
            try: 
                # await self.curr_bowler['player'].send(msg)
                await send_message(bot=self.bot, ctx=None, user=self.curr_bowler['player'], content=msg)
            except Forbidden:
                return

    async def make_scoreboard(self):

        scorecard = "{name}:  {runs}/{wickets}".format(**self.bowling_team_stats) + \
                    "   {} overs\n".format(overs(self.bowling_team_stats['balls'])) + \
                    "{name}:  {runs}/{wickets}".format(**self.batting_team_stats) + \
                    "   {} overs\n".format(overs(self.batting_team_stats['balls']))

        scorecard += "\nMatch Stats:\n\n```"

        for pl_id in self.bowling_team.keys():

            scorecard += "{}".format(spacing(self.bowling_team[pl_id]['player'].name)) + \
                            "{runs}({balls}) || {wickets}-{runs_given}".format(**self.bowling_team[pl_id]) + \
                            " ({})\n".format(overs(self.bowling_team[pl_id]['balls_given']))
        scorecard += "\n\n"

        for pl_id in self.batting_team.keys():

            scorecard += "{}".format(spacing(self.batting_team[pl_id]['player'].name)) + \
                            "{runs}({balls}) || {wickets}-{runs_given}".format(**self.batting_team[pl_id]) + \
                            " ({})\n".format(overs(self.batting_team[pl_id]['balls_given']))

        scorecard += "```"
        return await self.channel.send(embed=Embed(
            title='Match Summary',description=scorecard, colour=MAYABLUE).set_footer(text=self.result ))

    async def increment_runs(self):

        self.curr_batsman['runs'] += self.curr_batsman['last_action']
        self.curr_batsman['balls'] += 1
        self.batting_team['runs'] += self.curr_batsman['last_action']
        self.batting_team['balls'] += 1

        self.curr_bowler['runs_given'] += self.curr_batsman['last_action']
        self.curr_bowler['balls_given'] += 1
        return

    async def increment_wicket(self):

        self.curr_batsman['balls'] += 1
        self.curr_batsman['is_out'] = True
        self.curr_bowler['balls_given'] += 1
        self.curr_bowler['wickets'] += 1

        self.batting_team['balls'] += 1
        self.batting_team['wickets'] += 1
        return

    async def generate_scorecard_image(self):

        for keys in ('name','runs','balls','wickets'):
            self.bowling_team_stats[keys] = self.bowling_team.pop(keys)
            self.batting_team_stats[keys] = self.batting_team.pop(keys)

        if len(self.players) <= 6:
            with Image.open("assets/20201111_024023.jpg") as im:
                sc = im.copy()
                scimage = ImageDraw.Draw(sc)
            num = 3
            template = template1
            
        elif len(self.players) <= 12 and len(self.players) >= 7:
            with Image.open("assets/20201109_225032.jpg") as im:
                sc = im.copy()
                scimage = ImageDraw.Draw(sc)
            num = 6
            template = template2

        elif len(self.players) >= 13:
            with Image.open("assets/20201109_225102.jpg") as im:
                sc = im.copy()
                scimage = ImageDraw.Draw(sc)
            num = 11
            template = template3

        font_sizes = template['font_sizes']
        coordinates = template['coordinates']
        colour = template['colour']
        spacing = template['spacing']
        n = template['newline']

        font_size_1 = ImageFont.truetype("assets/CoreSansD65Heavy.otf", font_sizes[0])
        font_size_2 = ImageFont.truetype("assets/CoreSansD65Heavy.otf", font_sizes[1])
        font_size_3 = ImageFont.truetype("assets/CoreSansD65Heavy.otf", font_sizes[2])

        scimage.multiline_text(xy=coordinates[0], text="MATCH SUMMARY", fill=colour, font=font_size_1, spacing=spacing[0])
        scimage.multiline_text(xy=coordinates[4], text=self.result.strip(' 🎊 :handshake:'), fill=colour, font=font_size_2, spacing=spacing[4])

        scimage.multiline_text(xy=coordinates[1], text=f"{self.bowling_team_stats['name']}{n[0]}{self.batting_team_stats['name']}",
                fill=colour, font=font_size_1, spacing=spacing[1])

        scimage.multiline_text(xy=coordinates[2], 
                text=f"{overs(self.bowling_team_stats['balls'])} OVERS{n[1]}{overs(self.batting_team_stats['balls'])} OVERS",
                fill=colour, font=font_size_3, spacing=spacing[2])

        scimage.multiline_text(xy=coordinates[3], 
                text=f"{self.bowling_team_stats['runs']}/{self.bowling_team_stats['wickets']}{n[2]}{self.batting_team_stats['runs']}/{self.batting_team_stats['wickets']}",
                fill=colour, font=font_size_1, spacing=spacing[3])

        sorted_names, sorted_runs, sorted_balls = '','',''
        for player in sorted(self.bowling_team.items(), key=lambda x: (x[1]['runs'], x[1]['balls']), reverse=True):

            sorted_names += str(player[1]['player'].name) + '\n\n'
            sorted_runs += str(player[1]['runs']) + '\n\n'
            sorted_balls += '({})'.format(player[1]['balls']) + '\n\n'

        sorted_names += (num-len(self.TeamA))*'\n\n'
        sorted_runs += (num-len(self.TeamA))*'\n\n'
        sorted_balls += (num-len(self.TeamA))*'\n\n'
        sorted_names += n[3]; sorted_runs += n[4]; sorted_balls += n[4]

        for player in sorted(self.batting_team.items(), key=lambda x: (x[1]['runs'], x[1]['balls']), reverse=True):

            sorted_names += str(player[1]['player'].name) + '\n\n'
            sorted_runs += str(player[1]['runs']) + '\n\n'
            sorted_balls += '({})'.format(player[1]['balls']) + '\n\n'

        scimage.multiline_text(xy=coordinates[5], text=sorted_names, fill=colour, font=font_size_2, spacing=spacing[5])
        scimage.multiline_text(xy=coordinates[6], text=sorted_runs, fill=colour, font=font_size_2, spacing=spacing[6])
        scimage.multiline_text(xy=coordinates[7], text=sorted_balls, fill=colour, font=font_size_3, spacing=spacing[7])

        sorted_names, sorted_wickets, sorted_balls = '','',''
        for player in sorted(self.batting_team.items(), key=lambda x: 
            (x[1]['wickets'], x[1]['runs_given'], x[1]['balls_given']), reverse=True):
            
            sorted_names += str(player[1]['player'].name) + '\n\n'
            sorted_wickets += str(player[1]['wickets']) + '-' + str(player[1]['runs_given']) + '\n\n'
            sorted_balls += '({})'.format(overs(player[1]['balls_given'])) + '\n\n'

        sorted_names += (num-len(self.TeamA))*'\n\n'
        sorted_wickets += (num-len(self.TeamA))*'\n\n'
        sorted_balls += (num-len(self.TeamA))*'\n\n'
        sorted_names += n[3]; sorted_wickets += n[4]; sorted_balls += n[4]

        for player in sorted(self.bowling_team.items(), key=lambda x:
            (x[1]['wickets'], x[1]['runs_given'], x[1]['balls_given']), reverse=True):

            sorted_names += str(player[1]['player'].name) + '\n\n'
            sorted_wickets += str(player[1]['wickets']) + '-' + str(player[1]['runs_given']) + '\n\n'
            sorted_balls += '({})'.format(overs(player[1]['balls_given'])) + '\n\n'

        scimage.multiline_text(xy=coordinates[8], text=sorted_names, fill=colour, font=font_size_2, spacing=spacing[8])
        scimage.multiline_text(xy=coordinates[9], text=sorted_wickets, fill=colour, font=font_size_2, spacing=spacing[9])
        scimage.multiline_text(xy=coordinates[10], text=sorted_balls, fill=colour, font=font_size_3, spacing=spacing[10])


        sc.save('temporary/{}.jpg'.format(self.channel.id))
        file = File('temporary/{}.jpg'.format(self.channel.id))
        try: 
            await self.channel.send(file=file)
        except Forbidden:
            await self.make_scoreboard()
        sc.close()
        return remove('temporary/{}.jpg'.format(self.channel.id))

class SingleGame:
    def __init__(self, ctx: Context):
        self.type = GameType.SINGLE
        self.player = ctx.author
        self.channel = ctx.channel
        self.player_turn = None
        self.game_id = randint(4444, 7777)
        
        self.game_started = False
        self.innings = None
        self.innings1_runs, self.innings1_bowls, = 0, 0,
        self.innings2_runs, self.innings2_bowls = 0, 0

    @classmethod
    def create(cls, ctx):
        new_game = cls(ctx=ctx)
        return new_game

class DoubleGame:
    def __init__(self, ctx: Context, player: Member):
        self.type = GameType.DOUBLE
        self.players = [ctx.author, player]
        self.channel = ctx.channel
        self.challenger_turn = None
        self.game_id = randint(4444, 7777)

        self.game_started = False
        self.innings = None
        self.stats = {
            ctx.author.id: { 
            'player': ctx.author, 'runs': 0, 'balls': 0, 
            'wickets': 0, 'last_action': 0 
            },
            player.id: { 
                'player': player, 'runs': 0, 'balls': 0, 
                'wickets': 0, 'last_action': 0 
                },
            'curr_batsman': None,
            'curr_bowler': None
            }

    @classmethod
    def create(cls, ctx, player):
        new_game = cls(ctx=ctx, player=player)
        return new_game

class RunRaceGame:
    def __init__(self, ctx: Context, bot):
        self.type = GameType.RUNRACE
        self.created_at = None
        self.started_at = None
        self.host = None
        self.game_id = random.randint(4444,7777)
        self.game_started = False
        self.channel = ctx.channel
        self.overs = None
        self.bot_count = 0
        self.bot = bot

        self.players = []
        self.player_stats = {}

    @classmethod
    def create(cls, ctx, bot):
        new_game = cls(ctx=ctx, bot=bot)
        new_game.players.append(ctx.author)
        new_game.created_at = time()
        new_game.host = ctx.author.id
        return new_game

    async def update(self):
        if self.game_started == True:
            return

        else:
            diff = time() - self.created_at
            if diff > 15 * 60:
                try:
                    await self.channel.send("Match has been abandoned due to taking too long to start.")
                except Exception as e:
                    return
                finally:
                    self.bot.games.pop(self.channel.id)

            else: return

    async def initialise(self):
        self.game_started = True
        self.started_at = time()
        for player in self.players:
            self.player_stats[player.id] = {
                'player': player,
                'runs': 0,
                'balls': 0,
                'last_action': 0,
                'is_human': True if len(str(player.id)) > 4 else False,
                'is_out': False
            }
        return True

    async def send_message(self, player_id: int, message :str):
        try:
            await send_message(bot=self.bot, ctx=None, user=self.player_stats[player_id]['player'], content=message)
        except Forbidden:
            return

    def get_position(self, player_id):
        position = 1
        for player in sorted(self.player_stats.items(), key=lambda x: (x[1]['runs'], x[1]['balls']), reverse=True):
            if player[1]['player'].id == player_id:
                return position
                
            else:
                position += 1 
                continue