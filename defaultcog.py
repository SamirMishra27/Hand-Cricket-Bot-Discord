import discord
from discord import message
from discord.ext import commands

import asyncio
import random

from utils import *
from game import SingleGame, DoubleGame
from collections import deque

class Tie:
    def __init__(self):
        self.id = 1

class Default(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog_brief = 'Single and Double player commands.'
        self.cog_description = "This category lists two commands, player vs bot and player vs player."
        self.match_end_footer = "*Like the bot? Upvote it on [Top.gg]({})\nNew update is out! see h!news*".format(self.bot.topgg)

    @commands.command(hidden=True, usage = ['h!hello', None])
    async def hello(self, ctx):
        """No description available"""
        return await ctx.send("Hello!")

    @commands.command(
        self_bot=False, 
        brief='Play against the bot.', 
        usage = ['h! play', None], 
        description="".join(strings['play_desc']),
        aliases = ['p'])
    @commands.cooldown(1, 2.0, type=commands.BucketType.channel)
    async def play(self, ctx):
        
        if ctx.channel.id in self.bot.games: return await ctx.send(f"A game is already running here.")
        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or channel.")

        await ctx.send("Starting Player vs Bot game!\n\nCoin toss, choose heads or tails?")
        game = SingleGame.create(ctx=ctx, bot=self.bot)
        self.bot.games[ctx.channel.id] = game

        def check01(message): return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ('heads','tails')
        def check02(message_2): return message_2.channel == ctx.channel and message_2.author == ctx.author and message_2.content.lower() in ('bat','bowl')
        def check03(message_3): return message_3.channel == ctx.channel and message_3.author == ctx.author and message_3.content in ('0','1','2','3','4','5','6')
        
        try:
            message = await self.bot.wait_for('message', timeout=60, check=check01)
            player_won, coin_result = cointoss(message)

        except asyncio.TimeoutError: 
            self.bot.games.pop(ctx.channel.id)
            return await ctx.send("No response!")

        await ctx.send(coin_result)
        bot_msg = ''

        if player_won == True:
            try:
                message_2 = await self.bot.wait_for('message', timeout=60, check=check02)

            except asyncio.TimeoutError: 
                self.bot.games.pop(ctx.channel.id)
                return await ctx.send("No response!")

            if message_2.content.lower() == "bat":
                player_turn = 'batting'

            elif message_2.content.lower() == "bowl":
                player_turn = 'bowling'

        elif player_won == False:
            choice = random.choice(['batting', 'bowling'])

            player_turn = 'batting' if choice == 'bowling' else 'bowling'
            bot_msg = f"I've decided to let you **{player_turn}**.\n" 

        game.player_turn = player_turn
        l3as = deque(['','',''], maxlen=3)
        extra_msg = ""

        await ctx.send(bot_msg + "Tell me how many overs you want to keep? Select between 2 - 20, Select 1 for unlimited overs.")
        try:
            message = await self.bot.wait_for('message', timeout=60, check=lambda x: x.channel == ctx.channel and x.author == ctx.author and x.content.isnumeric() and int(x.content) <= 20)

        except asyncio.TimeoutError:
            self.bot.games.pop(ctx.channel.id)
            return await ctx.send("No response!")

        if int(message.content) != 1:
            game.overs = int(message.content)

        await ctx.send("Tell me how many wickets you want to keep each side? Select between 1 - 10.")
        try:
            message = await self.bot.wait_for('message', timeout=60, check=lambda x: x.channel == ctx.channel and x.author == ctx.author and x.content.isnumeric() and int(x.content) <= 10)

        except asyncio.TimeoutError:
            self.bot.games.pop(ctx.channel.id)
            return await ctx.send("No response!")

        game.wickets = int(message.content)
        _prev_wicket_score = 0
        _last_score = 0

        game.innings = Innings.ONE
        game.game_started = True
        print(self.bot.games[ctx.channel.id])
        await ctx.send("Game has started! start sending your actions, send a number between 0 - 6 in this channel.")

        while True:

            try:
                message_3 = await self.bot.wait_for('message', timeout=120, check=check03)
            except asyncio.TimeoutError:
                if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: return
                await ctx.send("No response received for 120 seconds, forfeiting the match. The game was a no result.")
                return self.bot.games.pop(ctx.channel.id)

            if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: return

            pl_msg = int(message_3.content)
            l3as.append(pl_msg)

            if l3as[0] == l3as[1] == l3as[2]:
                if player_turn == 'batting':
                    bot_msg = pl_msg
                elif player_turn == 'bowling': 
                    _d = [0,1,2,3,4,5,6]
                    _d.remove(pl_msg)
                    bot_msg = random.choice(_d)
            else:
                bot_msg = random.randint(0,6)

            if pl_msg != bot_msg:

                _last_score = game.innings1_runs
                if player_turn == 'batting': 
                    game.innings1_runs += int(pl_msg); 
                    game.innings1_bowls += 1
                    game.timeline.append(pl_msg)

                elif player_turn == 'bowling': 
                    game.innings1_runs += bot_msg; 
                    game.innings1_bowls += 1
                    game.timeline.append(bot_msg)
                await check_for_milestone(
                    game.player.name if player_turn == 'batting' else 'Bot', game.channel, _last_score, game.innings1_runs, self.bot
                )

                if game.overs != None and game.innings1_bowls == game.overs*6:
                    extra_msg = ("**Innings over!**\n"
                                f"Target -> **{game.innings1_runs+1}** run{pz(game.innings1_runs)}.\n{'Bot' if player_turn == 'batting' else 'You'} "
                                f"need {game.innings1_runs+1} run{pz(game.innings1_runs+1)} to win!")
                await ctx.send(f"{bot_msg}!\n`Current score {game.innings1_runs}/{game.innings1_wicks} ({game.innings1_bowls})`\n" + extra_msg)
                if game.overs != None and game.innings1_bowls == game.overs*6:
                    break
                continue

            elif pl_msg == bot_msg:

                if player_turn == 'batting':
                    if game.innings1_runs - _prev_wicket_score >= game.highest_score:
                        game.highest_score = game.innings1_runs - _prev_wicket_score
                        _prev_wicket_score = game.innings1_runs
                    if game.innings1_runs == 0:
                        game.duck = True
                        
                game.innings1_bowls += 1
                game.innings1_wicks += 1
                game.timeline.append("W")
                out_msg = f"{bot_msg}!\n{'You are' if player_turn == 'batting' else 'Bot is'} {'out!' if game.innings1_runs != 0 else 'DUCK out! :joy: :duck:'}  "

                if game.innings1_wicks == game.wickets:
                    out_msg += (
                        f"Target -> **{game.innings1_runs+1}** run{pz(game.innings1_runs)}.\n{'Bot' if player_turn == 'batting' else 'You'} "
                        f"need {game.innings1_runs+1} run{pz(game.innings1_runs+1)} to win!"
                    )
                else:
                    wicks_left = game.wickets - game.innings1_wicks
                    out_msg += (f"\n{'You have' if player_turn == 'batting' else 'bot has'} `{wicks_left} wicket{pz(wicks_left)}` left now!\n"
                                f"Current score: {game.innings1_runs}/{game.innings1_wicks} ({game.innings1_bowls})")
                    if game.overs != None and game.innings1_bowls == game.overs*6:
                        out_msg += ('\n\n' + "**Innings over!**\n"
                                    f"Target -> **{game.innings1_runs+1}** run{pz(game.innings1_runs)}.\n{'Bot' if player_turn == 'batting' else 'You'} "
                                    f"need {game.innings1_runs+1} run{pz(game.innings1_runs+1)} to win!")

                await ctx.send(out_msg)
                hattrick = await check_for_hattrick(
                    game.player.name if player_turn == 'bowling' else 'Bot', game.timeline, game.channel, game.innings1_wicks, True, self.bot
                )
                if hattrick == True:
                    game.hattrick = True
                if game.innings1_wicks == game.wickets:
                    break
                if game.overs != None and game.innings1_bowls == game.overs*6:
                    break
                continue

        if player_turn == 'batting':
            if game.innings1_runs - _prev_wicket_score >= game.highest_score:
                game.highest_score = game.innings1_runs - _prev_wicket_score
                _prev_wicket_score = game.innings1_runs

        game.innings = Innings.TWO
        l3as = deque(['','',''], maxlen=3)
        game.timeline = deque(['','','','','',''], maxlen=6)
        await asyncio.sleep(3)
        await ctx.send("Innings 2 has started! start sending your actions, send a number between 0 - 6 in this channel.")

        while True:

            try: 
                message_3 = await self.bot.wait_for('message', timeout=120, check=check03)
            except asyncio.TimeoutError: 
                if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: return
                await ctx.send("No response received for 120 seconds, forfeiting the match. The game was a no result.")
                return self.bot.games.pop(ctx.channel.id)

            if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: return
            pl_msg = int(message_3.content)
            l3as.append(pl_msg)
            if l3as[0] == l3as[1] == l3as[2]:
                if player_turn == 'batting':
                    _d = [0,1,2,3,4,5,6]
                    _d.remove(pl_msg)
                    bot_msg = random.choice(_d)
                elif player_turn == 'bowling': 
                    bot_msg = pl_msg
            else:
                bot_msg = random.randint(0,6)

            if pl_msg != bot_msg:

                _last_score = game.innings2_runs
                if player_turn == 'batting': 
                    game.innings2_runs += bot_msg; 
                    game.innings2_bowls += 1
                    game.timeline.append(bot_msg)

                elif player_turn == 'bowling': 
                    game.innings2_runs += int(pl_msg); 
                    game.innings2_bowls += 1
                    game.timeline.append(pl_msg)
                await check_for_milestone(
                    'Bot' if player_turn == 'batting' else game.player.name, game.channel, _last_score, game.innings2_runs, self.bot
                )

                _msg = f"{bot_msg}!\n`Current score {game.innings2_runs}/{game.innings2_wicks} ({game.innings2_bowls})`"
                if game.innings2_runs > game.innings1_runs: 
                    _msg += "\nScore has been chased!"
                    await ctx.send(_msg)
                    break; 
                elif game.overs != None and game.innings2_bowls == game.overs*6:
                    _msg += "\nInnings over!"
                    await ctx.send(_msg)
                    break
                else: 
                    await ctx.send(_msg)
                    continue
            
            elif pl_msg == bot_msg:
                
                if player_turn == 'bowling':
                    if game.innings2_runs - _prev_wicket_score >= game.highest_score:
                        game.highest_score = game.innings2_runs - _prev_wicket_score
                        _prev_wicket_score = game.innings2_runs
                    if game.innings2_runs == 0:
                        game.duck = True

                game.innings2_bowls += 1
                game.innings2_wicks += 1
                game.timeline.append("W")
                out_msg = f"{bot_msg}!\n{'You are' if player_turn == 'bowling' else 'Bot is'} {'out!' if game.innings2_runs != 0 else 'DUCK out! :joy: :duck:'}  "

                if game.wickets == game.innings2_wicks:
                    out_msg += ("**Innings over!**"
                                f"\nFinal score is {game.innings2_runs} run{pz(game.innings2_runs)}! `{game.innings2_runs}/{game.innings2_wicks} ({game.innings2_bowls})`")

                else:
                    wicks_left = game.wickets - game.innings2_wicks
                    out_msg += f"\n{'You have' if player_turn == 'bowling' else 'bot has'} `{wicks_left} wicket{pz(wicks_left)}` left now!"
                    
                    if game.overs != None and game.innings2_bowls == game.overs*6:
                        out_msg += "\n\nInnings over!"
                await ctx.send(out_msg)
                hattrick = await check_for_hattrick(
                    'Bot' if player_turn == 'bowling' else game.player.name, game.timeline, game.channel, game.innings2_wicks, True, self.bot
                )
                if hattrick == True:
                    game.hattrick = True
                if game.innings2_wicks == game.wickets:
                    break
                if game.overs != None and game.innings2_bowls == game.overs*6:
                    break
                continue

        if player_turn == 'bowling':
            if game.innings2_runs - _prev_wicket_score >= game.highest_score:
                game.highest_score = game.innings2_runs - _prev_wicket_score
                _prev_wicket_score = game.innings2_runs

        if game.innings1_runs > game.innings2_runs: 

            diff = game.innings1_runs - game.innings2_runs
            if player_turn == 'batting':
                final_result = f"You won the game by {diff} run{pz(diff)}!" + ' :confetti_ball:'
                game.won = True

            elif player_turn == 'bowling':
                final_result = f"You lost the game, bot won by {diff} run{pz(diff)}." 
                game.won = False

        elif game.innings1_runs < game.innings2_runs: 

            diff2 = game.wickets - game.innings2_wicks
            if player_turn == 'batting':
                final_result = f"You lost the game, bot won by {diff2} wicket{pz(diff2)}." 
                game.won = False

            elif player_turn == 'bowling':
                final_result = f"You won the game by {diff2} wicket{pz(diff2)}!" + ' :confetti_ball:'
                game.won = True

        elif game.innings1_runs == game.innings2_runs: 
            final_result = f"**The game ended in a draw! :O**"
            game.won = "TIE"

        stats = [f"```\n『 1st Innings 』\n", 
                f"⫸ {ctx.author.name if player_turn == 'batting' else 'Bot'} - {game.innings1_runs}/{game.innings1_wicks} ({game.innings1_bowls})\n",
                f"\n『 2nd Innings 』\n",
                f"⫸ {'Bot' if player_turn == 'batting' else ctx.author.name } - {game.innings2_runs}/{game.innings2_wicks} ({game.innings2_bowls})\n```"]

        stats = ''.join(stats) 

        embed = discord.Embed(description=f"{final_result}\n\nFinal results:\n{stats}\n{self.match_end_footer}")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url or ctx.author.avatar)
        embed.colour = MAYABLUE

        await ctx.send(embed=embed)
        await log_game(ctx, type=GameType.SINGLE)
        self.bot.games.pop(ctx.channel.id)
        match_info = await game.retreive_match_data()
        await self.bot.get_cog("Social").insert_match_data(match_info)
        self.bot.get_cog("GlobalEvents").insert_data_in_events(game) 
        return 
        
    @commands.command(
        aliases=['chall'], brief='Challenge someone to play.', 
        usage=['h! challenge | chall <Member tag>', ['h!challenge @SAMIR', 'h!chall @SAMIR']],
        description="".join(strings['challenge_desc']))
    @commands.cooldown(1, 2.0, type=commands.BucketType.channel)
    @commands.guild_only()
    async def challenge(self, ctx, player: discord.Member):
        
        if player.id == ctx.author.id: return await ctx.send("Imagine playing yourself.")
        elif player.id == ctx.bot.user.id: return await ctx.send(f"If you want to play with me, use {ctx.guild_prefix}play command.")
        elif player.bot == True: return await ctx.send(f'I can\'t play with other bots. Choose a human.')

        if ctx.channel.id in self.bot.games: return await ctx.send(f"A game is already running here.")
        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or channel.")

        toss_winner=0; participants_ids = []
        game = DoubleGame.create(ctx=ctx, player=player, bot=self.bot)
        self.bot.games[ctx.channel.id] = game

        def check01(message_1): return message_1.channel == ctx.channel and message_1.author.id == player.id and ('y' in message_1.content.lower() or 'n' in message_1.content.lower())
        def check02(message_2): return message_2.channel == ctx.channel and message_2.author.id == ctx.author.id and message_2.content.lower() in ('heads','tails')
        def check03(message_3): return message_3.channel == ctx.channel and message_3.author.id == toss_winner and message_3.content.lower() in ('bat','bowl') 
        def check04(message): return message.channel.type == discord.ChannelType.private and message.author.id in participants_ids and message.content in ('0','1','2','3','4','5','6',)

        await ctx.send(f'Hey **{player.name}**, **{ctx.author.name}** would like to challenge you, do you accept it? (yes / y / no / n)')

        try:
            message_1 = await self.bot.wait_for('message', timeout=60, check=check01)
            
        except asyncio.TimeoutError:
            await ctx.send("Person didn't respond in the given time.") 
            return self.bot.games.pop(ctx.channel.id)

        if 'n' in message_1.content.lower():
            await ctx.send(f"Well, {player.name} declined.")
            return self.bot.games.pop(ctx.channel.id)

        await ctx.send(f"{player.name} has accepted the challenge! Time to do toss, {ctx.author.mention} choose heads or tails? (heads / tails)")

        try: message_2 = await self.bot.wait_for('message', timeout=60, check=check02)

        except asyncio.TimeoutError:
            await ctx.send("Challenger didn't respond in the given time, so stopping the game.")
            return self.bot.games.pop(ctx.channel.id)

        if message_2.content.lower() == random.choice(['heads','tails']):
            toss_winner = ctx.author.id; await ctx.send(f"{ctx.author.mention} has won the toss! Choose bat or bowl? (bat / bowl)")

        else:
            toss_winner = player.id; await ctx.send(f"{player.mention} has won the toss! Choose bat or bowl? (bat / bowl)")

        try: message_3 = await self.bot.wait_for('message', timeout=60, check=check03)

        except asyncio.TimeoutError:
            await ctx.send("Person didn't respond in the given time, so stopping the game.")
            return self.bot.games.pop(ctx.channel.id)

        await ctx.send(f"<@{toss_winner}> has decided to **{message_3.content.lower()}**")

        if toss_winner == ctx.author.id: challenger_turn = message_3.content.lower()
        else:
            challenger_turn = 'bowl' if message_3.content.lower() == 'bat' else 'bat'

        game.challenger_turn = challenger_turn

        game.stats['curr_batsman'] = game.stats[ctx.author.id] if challenger_turn == 'bat' else game.stats[player.id]
        game.stats['curr_bowler'] = game.stats[player.id] if challenger_turn == 'bat' else game.stats[ctx.author.id]
        _prev_wicket_score = 0

        game.innings = Innings.ONE
        game.game_started = True
        participants_ids = [ctx.author.id, player.id]
        await ctx.send("Let the battle begin! both the players, send your actions by DM'ing me a number between 0 - 6\n"
                        "*NOTE: Please make sure you have DMs from this server enabled.*")

        while True:
            try: 
                message_4 = await self.bot.wait_for('message', timeout=15, check=check04)  
                participants_ids.remove(message_4.author.id); 
                game.stats[message_4.author.id]['last_action'] = int(message_4.content.lower())

                message_5 = await self.bot.wait_for('message', timeout=15, check=check04)
                participants_ids.remove(message_5.author.id); 
                game.stats[message_5.author.id]['last_action'] = int(message_5.content.lower())

            except asyncio.TimeoutError: 
                if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: return
                if game.stats['curr_batsman']['player'].id in participants_ids: 
                    game.stats['curr_batsman']['last_action'] = random.randint(0,6)
                    try: await send_message(bot=self.bot, ctx=None, user=game.stats['curr_batsman']['player'],
                    content='You didn\'t respond in time so i rolled a random number for you.')
                    except Exception: pass

                await asyncio.sleep(0.5)
                if game.stats['curr_bowler']['player'].id in participants_ids:
                    game.stats['curr_bowler']['last_action'] = random.randint(0,6)
                    try: await send_message(bot=self.bot, ctx=None, user=game.stats['curr_bowler']['player'],
                    content='You didn\'t respond in time so i rolled a random number for you.')
                    except Exception: pass

            if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: return
            if game.stats['curr_batsman']['last_action'] != game.stats['curr_bowler']['last_action']:

                _last_score = game.stats['curr_batsman']['runs']
                game.stats['curr_batsman']['runs'] += game.stats['curr_batsman']['last_action']
                game.stats['curr_batsman']['balls'] += 1
                game.timeline.append(game.stats['curr_batsman']['last_action'])
                await check_for_milestone(
                    game.stats['curr_batsman']['player'].name, game.channel, _last_score, game.stats['curr_batsman']['runs'], self.bot
                )

                await send_message(bot=self.bot, ctx=None, user=ctx.author, content=f"Opponent's last action -> **{game.stats[player.id]['last_action']}**"
                    "\n`Innings 1 score:  {runs} ({balls})`".format(**game.stats['curr_batsman']))

                await asyncio.sleep(0.5)
                await send_message(bot=self.bot, ctx=None, user=player, content=f"Opponent's last action -> **{game.stats[ctx.author.id]['last_action']}**"
                    "\n`Innings 1 score:  {runs} ({balls})`".format(**game.stats['curr_batsman']))
                participants_ids = [ctx.author.id, player.id]

            elif game.stats['curr_batsman']['last_action'] == game.stats['curr_bowler']['last_action']:

                duck1 = False
                if game.stats['curr_batsman']['runs'] - _prev_wicket_score >= game.stats['curr_batsman']['highest_score']:
                    game.stats['curr_batsman']['highest_score'] = game.stats['curr_batsman']['runs'] - _prev_wicket_score
                    _prev_wicket_score = game.stats['curr_batsman']['runs']
                if game.stats['curr_batsman']['runs'] == 0:
                    game.stats['curr_batsman']['duck'] = True
                    duck1 = True

                game.stats['curr_batsman']['balls'] += 1
                game.stats['curr_bowler']['wickets'] += 1
                game.timeline.append("W")
                await send_message(bot=self.bot, ctx=None, user=game.stats['curr_batsman']['player'],
                content=f"You are {'DUCK out! :joy: :duck:' if duck1 == True else 'out!'} \nOpponent's last action -> **{game.stats['curr_bowler']['last_action']}**")

                await asyncio.sleep(0.5)
                await send_message(bot=self.bot, ctx=None, user=game.stats['curr_bowler']['player'],
                content=f"Opponent is {'DUCK out! :joy: :duck:' if duck1 == True else 'out!'} \nOpponent's last action -> **{game.stats['curr_batsman']['last_action']}**")

                _target = game.stats['curr_batsman']['runs']+1
                await asyncio.sleep(0.5)
                await ctx.send('\n\n'.join(
                                [f"**{game.stats['curr_batsman']['player'].name}**  is {'DUCK ' if duck1 == True else ''}out!",
                                f"Final Score  ->  **{game.stats['curr_batsman']['runs']} ({game.stats['curr_batsman']['balls']})**",
                                f"**{game.stats['curr_bowler']['player'].name}**  needs **{_target}** run{pz(_target)} to win!"]
                                ) )
                await check_for_hattrick(
                    game.stats['curr_bowler']['player'].name, game.timeline, game.channel, game.stats['curr_bowler']['wickets'], True, self.bot
                )
                break
        
        game.innings = Innings.TWO
        innings_1_runs = game.stats['curr_batsman']['runs']
        game.stats['curr_batsman'], game.stats['curr_bowler'] = game.stats['curr_bowler'], game.stats['curr_batsman']
        participants_ids = [ctx.author.id, player.id]
        _prev_wicket_score = 0
        await asyncio.sleep(5)
        await ctx.send("Innings 2 have started! start DM'ing me your actions!")

        while True:
            try: 
                message_4 = await self.bot.wait_for('message', timeout=15, check=check04)
                participants_ids.remove(message_4.author.id); 
                game.stats[message_4.author.id]['last_action'] = int(message_4.content.lower())
                
                message_5 = await self.bot.wait_for('message', timeout=15, check=check04)
                participants_ids.remove(message_5.author.id); 
                game.stats[message_5.author.id]['last_action'] = int(message_5.content.lower())

            except asyncio.TimeoutError: 
                if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: return
                if game.stats['curr_batsman']['player'].id in participants_ids: 
                    game.stats['curr_batsman']['last_action'] = random.randint(0,6)
                    try: await send_message(bot=self.bot, ctx=None, user=game.stats['curr_batsman']['player'],
                    content='You didn\'t respond in time so i rolled a random number for you.')
                    except Exception: pass

                await asyncio.sleep(0.5)
                if game.stats['curr_bowler']['player'].id in participants_ids:
                    game.stats['curr_bowler']['last_action'] = random.randint(0,6)
                    try: await send_message(bot=self.bot, ctx=None, user=game.stats['curr_bowler']['player'],
                    content='You didn\'t respond in time so i rolled a random number for you.')
                    except Exception: pass
                    
            if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: return
            if game.stats['curr_batsman']['last_action'] != game.stats['curr_bowler']['last_action']:

                _last_score = game.stats['curr_batsman']['runs']
                game.stats['curr_batsman']['runs'] += game.stats['curr_batsman']['last_action']
                game.stats['curr_batsman']['balls'] += 1
                game.timeline.append(game.stats['curr_batsman']['last_action'])
                await check_for_milestone(
                    game.stats['curr_batsman']['player'].name, game.channel, _last_score, game.stats['curr_batsman']['runs'], self.bot
                )

                to_author = f"Opponent's last action -> **{game.stats[player.id]['last_action']}**\n" +\
                    "`Innings 2 score:  {runs} ({balls})`".format(**game.stats['curr_batsman'])
                to_player = f"Opponent's last action -> **{game.stats[ctx.author.id]['last_action']}**\n" +\
                    "`Innings 2 score:  {runs} ({balls})`".format(**game.stats['curr_batsman'])

                if game.stats['curr_batsman']['runs'] > innings_1_runs: 

                    text = "\n\nScore has been chased!\nFinal Score  ->  **{runs}**  **({balls})**".format(**game.stats['curr_batsman'])
                    to_author += text
                    to_player += text
                    await send_message(bot=self.bot, ctx=None, user=ctx.author, content=to_author)
                    await asyncio.sleep(0.5)
                    await send_message(bot=self.bot, ctx=None, user=player, content=to_player)
                    innings_2_runs = game.stats['curr_batsman']['runs']; 
                    break

                else: 
                    await send_message(bot=self.bot, ctx=None, user=ctx.author, content=to_author)
                    await asyncio.sleep(0.5)
                    await send_message(bot=self.bot, ctx=None, user=player, content=to_player)
                    participants_ids = [ctx.author.id, player.id]
                    continue

            elif game.stats['curr_batsman']['last_action'] == game.stats['curr_bowler']['last_action']:

                duck2 = False
                if game.stats['curr_batsman']['runs'] - _prev_wicket_score >= game.stats['curr_batsman']['highest_score']:
                    game.stats['curr_batsman']['highest_score'] = game.stats['curr_batsman']['runs'] - _prev_wicket_score
                    _prev_wicket_score = game.stats['curr_batsman']['runs']
                if game.stats['curr_batsman']['runs'] == 0:
                    game.stats['curr_batsman']['duck'] = True
                    duck2 = True

                game.stats['curr_batsman']['balls'] += 1
                game.stats['curr_bowler']['wickets'] += 1
                game.timeline.append("W")

                await send_message(bot=self.bot, ctx=None, user=game.stats['curr_batsman']['player'], 
                content=f"You are {'DUCK out! :joy: :duck:' if duck2 == True else 'out!'} \nOpponent's last action -> **{game.stats['curr_bowler']['last_action']}**")
                await asyncio.sleep(0.5)

                await send_message(bot=self.bot, ctx=None, user=game.stats['curr_bowler']['player'], 
                content=f"Opponent is {'DUCK out! :joy: :duck:' if duck2 == True else 'out!'} \nOpponent's last action -> **{game.stats['curr_batsman']['last_action']}**")

                await asyncio.sleep(0.5)
                await ctx.send('\n\n'.join(
                                    [f"**{game.stats['curr_batsman']['player'].name}** is {'DUCK ' if duck2 == True else ''}out!",
                                    f"Final Score  ->  **{game.stats['curr_batsman']['runs']} ({game.stats['curr_batsman']['balls']})**"]
                                ) )
                await check_for_hattrick(
                    game.stats['curr_bowler']['player'].name, game.timeline, game.channel, game.stats['curr_bowler']['wickets'], True, self.bot
                )
                innings_2_runs = game.stats['curr_batsman']['runs']
                break


        if innings_1_runs > innings_2_runs:

            if challenger_turn == 'bat':     game.winner = ctx.author; diff = innings_1_runs - innings_2_runs
            elif challenger_turn == 'bowl':  game.winner = player;     diff = innings_1_runs - innings_2_runs
            
            result_text = f"{game.winner.mention} won the game by {diff} run{pz(diff)}! :confetti_ball:"

        elif innings_1_runs < innings_2_runs:

            if challenger_turn == 'bat':    game.winner = player
            elif challenger_turn == 'bowl': game.winner = ctx.author

            result_text = f"{game.winner.mention} won the game! :confetti_ball:"

        elif innings_1_runs == innings_2_runs: 
            result_text = f"**Whoa, this game is a draw! :handshake:**"
            game.winner = Tie() ##"TIE"

        embed = discord.Embed(description=(
            f"{result_text}\n\n" +\
            f"Final scoreboard:\n" +\
            f"```\n『 1st Innings 』\n" +  f"⫸ {game.stats['curr_bowler']['player'].name}" +\
            " {runs}({balls})\n\n".format(**game.stats['curr_bowler']) +\
            f"『 2nd Innings 』\n" + f"⫸ {game.stats['curr_batsman']['player'].name}" +\
            " {runs}({balls})```".format(**game.stats['curr_batsman']) +\
            f"\n\n{self.match_end_footer}"
            )).set_author(name=self.bot.user.name, icon_url=str(self.bot.user.avatar_url or self.bot.user.avatar))
        embed.colour = MAYABLUE
        await ctx.send(embed=embed)
        await log_game(ctx, GameType.DOUBLE)

        self.bot.games.pop(ctx.channel.id)
        match_info = await game.retreive_match_data()
        await self.bot.get_cog("Social").insert_match_data(match_info)
        self.bot.get_cog("GlobalEvents").insert_data_in_events(game)
        return 

def setup(bot):
    bot.add_cog(Default(bot))
