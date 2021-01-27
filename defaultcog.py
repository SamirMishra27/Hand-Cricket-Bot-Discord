import discord
from discord.ext import commands

import asyncio
import random

from utils import *
from game import SingleGame, DoubleGame

class Default(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog_brief = 'Single and Double player commands.'
        self.cog_description = "This category lists two commands, player vs bot and player vs player."
        self.match_end_footer = "*Did you liked the bot? Upvote it on [Top.gg]({})*".format(self.bot.topgg)

    @commands.command(hidden=True, usage = ['h!hello', None])
    async def hello(self, ctx):
        """No description available"""
        return await ctx.send("Hello!")

    @commands.command(self_bot=False, brief='Play against the bot.', usage = ['h! play', None])
    @commands.cooldown(1, 2.0, type=commands.BucketType.channel)
    async def play(self, ctx):
        """Play a Hand Cricket match against the bot using this command. The bot first prompts you for a toss and then the match begins.
        You can also use this command in Direct messages."""
        if ctx.channel.id in self.bot.games: return await ctx.send(f"A game is already running here.")
        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or channel.")

        await ctx.send("Starting Player vs Bot game!\n\nCoin toss, choose heads or tails?"); 
        # self.bot.games[ctx.channel.id] = {}
        game = SingleGame.create(ctx=ctx)
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
            bot_msg = f"I've decided to let you **{choice}**.\n"

        game.player_turn = player_turn

        await ctx.send(bot_msg + "Alrighty! let the game begin!"); 
        await asyncio.sleep(3)

        game.innings = Innings.ONE
        game.game_started = True
        print(self.bot.games[ctx.channel.id])
        await ctx.send("Game has started! start sending your actions, send a number between 0 - 6 in this channel.")

        while True:

            try:
                message_3 = await self.bot.wait_for('message', timeout=120, check=check03)
            except asyncio.TimeoutError:
                if ctx.channel.id not in self.bot.games: return
                await ctx.send("No response received for 120 seconds, forfeiting the match. The game was a no result.")
                return self.bot.games.pop(ctx.channel.id)

            if ctx.channel.id not in self.bot.games: return
            pl_msg = int(message_3.content)
            bot_msg = random.randint(0,6)

            if pl_msg != bot_msg:

                if player_turn == 'batting': 
                    game.innings1_runs += int(pl_msg); 
                    game.innings1_bowls += 1

                elif player_turn == 'bowling': 
                    game.innings1_runs += bot_msg; 
                    game.innings1_bowls += 1

                await ctx.send(f"{bot_msg}!\n`Current score {game.innings1_runs} ({game.innings1_bowls})`")
                continue

            elif pl_msg == bot_msg:

                game.innings1_bowls += 1
                await ctx.send(f"{bot_msg}!\n{'You are' if player_turn == 'batting' else 'Bot is'} out!  "
                f"Target -> **{game.innings1_runs+1}** run{pz(game.innings1_runs)}.\n{'Bot' if player_turn == 'batting' else 'You'} "
                f"need {game.innings1_runs+1} run{pz(game.innings1_runs+1)} to win!")
                break

        game.innings = Innings.TWO
        await asyncio.sleep(3)
        await ctx.send("Innings 2 has started! start sending your actions, send a number between 0 - 6 in this channel.")

        while True:

            try: 
                message_3 = await self.bot.wait_for('message', timeout=120, check=check03)
            except asyncio.TimeoutError: 
                if ctx.channel.id not in self.bot.games: return
                await ctx.send("No response received for 120 seconds, forfeiting the match. The game was a no result.")
                return self.bot.games.pop(ctx.channel.id)

            if ctx.channel.id not in self.bot.games: return
            pl_msg = int(message_3.content)
            bot_msg = random.randint(0,6)

            if pl_msg != bot_msg:

                if player_turn == 'batting': 
                    game.innings2_runs += bot_msg; 
                    game.innings2_bowls += 1

                elif player_turn == 'bowling': 
                    game.innings2_runs += int(pl_msg); 
                    game.innings2_bowls += 1

                _msg = f"{bot_msg}!\n`Current score {game.innings2_runs} ({game.innings2_bowls})`"
                if game.innings2_runs > game.innings1_runs: 
                    _msg += "\nScore has been chased!"
                    await ctx.send(_msg)
                    break; 
                else: 
                    await ctx.send(_msg)
                    continue
            
            elif pl_msg == bot_msg:

                game.innings2_bowls += 1
                await ctx.send(f"{bot_msg}!\n{'You are' if player_turn == 'bowling' else 'Bot is'} out!  "
                f"Final score is {game.innings2_runs} run{pz(game.innings2_runs)}! `{game.innings2_runs} ({game.innings2_bowls})`")
                break

        if game.innings1_runs > game.innings2_runs: 

            diff = game.innings1_runs - game.innings2_runs
            if player_turn == 'batting':
                final_result = f"You won the game by {diff} run{pz(diff)}!" + ' :confetti_ball:'

            elif player_turn == 'bowling':
                final_result = f"You lost the game, bot won by {diff} run{pz(diff)}."

        elif game.innings1_runs < game.innings2_runs: 

            if player_turn == 'batting':
                final_result = f"You lost the game."

            elif player_turn == 'bowling':
                final_result = f"You won the game!" + ' :confetti_ball:'

        elif game.innings1_runs == game.innings2_runs: final_result = f"**The game ended in a draw! :O**"

        stats = [f"```\n『 1st Innings 』\n", 
                f"⫸ {ctx.author.name if player_turn == 'batting' else 'Bot'} - {game.innings1_runs}({game.innings1_bowls})\n",
                f"\n『 2nd Innings 』\n",
                f"⫸ {'Bot' if player_turn == 'batting' else ctx.author.name } - {game.innings2_runs}({game.innings2_bowls})\n```"]

        stats = ''.join(stats) 
        embed = discord.Embed(description=f"{final_result}\n\nFinal results:\n{stats}\n{self.match_end_footer}")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.colour = MAYABLUE
        await ctx.send(embed=embed)
        self.bot.games.pop(ctx.channel.id)
        return await log_game(ctx, type=GameType.SINGLE)
        
    @commands.command(aliases=['chall'], brief='Challenge someone to play.', 
    usage=['h! challenge | chall <Member tag>', ['h!challenge @SAMIR', 'h!chall @SAMIR']])
    @commands.cooldown(1, 2.0, type=commands.BucketType.channel)
    @commands.guild_only()
    async def challenge(self, ctx, player: discord.Member):
        """Challenge another member in the server for a 1 vs 1 Hand cricket match using this command."""

        if player.id == ctx.author.id: return await ctx.send("Imagine playing yourself.")
        elif player.id == ctx.bot.user.id: return await ctx.send(f"If you want to play with me, use {ctx.guild_prefix}play command.")
        elif player.bot == True: return await ctx.send(f'I can\'t play with other bots. Choose a human.')

        if ctx.channel.id in self.bot.games: return await ctx.send(f"A game is already running here.")
        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or channel.")

        self.bot.games[ctx.channel.id] = {}; toss_winner=0; participants_ids = []
        game = DoubleGame.create(ctx=ctx, player=player)
        self.bot.games[ctx.channel.id] = game

        def check01(message_1): return message_1.channel == ctx.channel and message_1.author.id == player.id and message_1.content.lower() in ('yes','no')
        def check02(message_2): return message_2.channel == ctx.channel and message_2.author.id == ctx.author.id and message_2.content.lower() in ('heads','tails')
        def check03(message_3): return message_3.channel == ctx.channel and message_3.author.id == toss_winner and message_3.content.lower() in ('bat','bowl') 
        def check04(message): return message.channel.type == discord.ChannelType.private and message.author.id in participants_ids and message.content in ('0','1','2','3','4','5','6',)

        await ctx.send(f'Hey **{player.name}**, **{ctx.author.name}** would like to challenge you, do you accept it? (yes / no)')

        try:
            message_1 = await self.bot.wait_for('message', timeout=60, check=check01)
            
        except asyncio.TimeoutError:
            await ctx.send("Person didn't respond in the given time.") 
            return self.bot.games.pop(ctx.channel.id)

        if message_1.content.lower() == 'no': 
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

        game.innings = Innings.ONE
        game.game_started = True
        participants_ids = [ctx.author.id, player.id]
        await ctx.send("Let the battle begin! both the players, send your actions by DM'ing me a number between 0 - 6\n"
                        "*NOTE: Please make sure you have DMs from this server enabled.*")

        while True:
            try: 
                message_4 = await self.bot.wait_for('message', timeout=20, check=check04)  
                participants_ids.remove(message_4.author.id); 
                game.stats[message_4.author.id]['last_action'] = int(message_4.content.lower())

                message_5 = await self.bot.wait_for('message', timeout=20, check=check04)
                participants_ids.remove(message_5.author.id); 
                game.stats[message_5.author.id]['last_action'] = int(message_5.content.lower())

            except asyncio.TimeoutError: 
                if ctx.channel.id not in self.bot.games: return
                if game.stats['curr_batsman']['player'].id in participants_ids: 
                    game.stats['curr_batsman']['last_action'] = random.randint(0,6)
                    try: await game.stats['curr_batsman']['player'].send('You didn\'t respond in time so i rolled a random number for you.')
                    except Exception: pass

                if game.stats['curr_bowler']['player'].id in participants_ids:
                    game.stats['curr_bowler']['last_action'] = random.randint(0,6)
                    try: await game.stats['curr_bowler']['player'].send('You didn\'t respond in time so i rolled a random number for you.')
                    except Exception: pass

            if ctx.channel.id not in self.bot.games: return
            if game.stats['curr_batsman']['last_action'] != game.stats['curr_bowler']['last_action']:

                game.stats['curr_batsman']['runs'] += game.stats['curr_batsman']['last_action']
                game.stats['curr_batsman']['balls'] += 1

                await ctx.author.send(f"Opponent's last action -> **{game.stats[player.id]['last_action']}**"
                    "\n`Innings 1 score:  {runs} ({balls})`".format(**game.stats['curr_batsman']))
                await player.send(f"Opponent's last action -> **{game.stats[ctx.author.id]['last_action']}**"
                    "\n`Innings 1 score:  {runs} ({balls})`".format(**game.stats['curr_batsman']))
                participants_ids = [ctx.author.id, player.id]

            elif game.stats['curr_batsman']['last_action'] == game.stats['curr_bowler']['last_action']:

                game.stats['curr_batsman']['balls'] += 1
                await game.stats['curr_batsman']['player'].send(
                    f"You are out! \nOpponent's last action -> **{game.stats['curr_bowler']['last_action']}**")
                await game.stats['curr_bowler']['player'].send(
                    f"Opponent is out! \nOpponent's last action -> **{game.stats['curr_batsman']['last_action']}**")

                _target = game.stats['curr_batsman']['runs']+1
                await ctx.send('\n\n'.join(
                                [f"**{game.stats['curr_batsman']['player'].name}**  is out!",
                                f"Final Score  ->  **{game.stats['curr_batsman']['runs']} ({game.stats['curr_batsman']['balls']})**",
                                f"**{game.stats['curr_bowler']['player'].name}**  needs **{_target}** run{pz(_target)} to win!"]
                                ) )
                break
        
        game.innings = Innings.TWO
        innings_1_runs = game.stats['curr_batsman']['runs']
        game.stats['curr_batsman'], game.stats['curr_bowler'] = game.stats['curr_bowler'], game.stats['curr_batsman']
        participants_ids = [ctx.author.id, player.id]
        await asyncio.sleep(5)
        await ctx.send("Innings 2 have started! start DM'ing me your actions!")

        while True:
            try: 
                message_4 = await self.bot.wait_for('message', timeout=20, check=check04)
                participants_ids.remove(message_4.author.id); 
                game.stats[message_4.author.id]['last_action'] = int(message_4.content.lower())
                
                message_5 = await self.bot.wait_for('message', timeout=20, check=check04)
                participants_ids.remove(message_5.author.id); 
                game.stats[message_5.author.id]['last_action'] = int(message_5.content.lower())

            except asyncio.TimeoutError: 
                if ctx.channel.id not in self.bot.games: return
                if game.stats['curr_batsman']['player'].id in participants_ids: 
                    game.stats['curr_batsman']['last_action'] = random.randint(0,6)
                    try: await game.stats['curr_batsman']['player'].send('You didn\'t respond in time so i rolled a random number for you.')
                    except Exception: pass

                if game.stats['curr_bowler']['player'].id in participants_ids:
                    game.stats['curr_bowler']['last_action'] = random.randint(0,6)
                    try: await game.stats['curr_bowler']['player'].send('You didn\'t respond in time so i rolled a random number for you.')
                    except Exception: pass

            if ctx.channel.id not in self.bot.games: return
            if game.stats['curr_batsman']['last_action'] != game.stats['curr_bowler']['last_action']:

                game.stats['curr_batsman']['runs'] += game.stats['curr_batsman']['last_action']
                game.stats['curr_batsman']['balls'] += 1

                to_author = f"Opponent's last action -> **{game.stats[player.id]['last_action']}**\n" +\
                    "`Innings 2 score:  {runs} ({balls})`".format(**game.stats['curr_batsman'])
                to_player = f"Opponent's last action -> **{game.stats[ctx.author.id]['last_action']}**\n" +\
                    "`Innings 2 score:  {runs} ({balls})`".format(**game.stats['curr_batsman'])

                if game.stats['curr_batsman']['runs'] > innings_1_runs: 

                    text = "\n\nScore has been chased!\nFinal Score  ->  **{runs}**  **({balls})**".format(**game.stats['curr_batsman'])
                    to_author += text
                    to_player += text
                    await ctx.author.send(to_author)
                    await player.send(to_player)
                    innings_2_runs = game.stats['curr_batsman']['runs']; 
                    break

                else: 
                    await ctx.author.send(to_author)
                    await player.send(to_player)
                    participants_ids = [ctx.author.id, player.id]
                    continue

            elif game.stats['curr_batsman']['last_action'] == game.stats['curr_bowler']['last_action']:

                game.stats['curr_batsman']['balls'] += 1
                await game.stats['curr_batsman']['player'].send(f"You are out! \nOpponent's last action -> **{game.stats['curr_bowler']['last_action']}**")
                await game.stats['curr_bowler']['player'].send(f"Opponent is out! \nOpponent's last action -> **{game.stats['curr_batsman']['last_action']}**")

                await ctx.send('\n\n'.join(
                                    [f"**{game.stats['curr_batsman']['player'].name}** is out!",
                                    f"Final Score  ->  **{game.stats['curr_batsman']['runs']} ({game.stats['curr_batsman']['balls']})**"]
                                ) )
                innings_2_runs = game.stats['curr_batsman']['runs']
                break


        if innings_1_runs > innings_2_runs:

            if challenger_turn == 'bat':     winner = ctx.author; diff = innings_1_runs - innings_2_runs
            elif challenger_turn == 'bowl':  winner = player;     diff = innings_1_runs - innings_2_runs
            
            result_text = f"{winner.mention} won the game by {diff} run{pz(diff)}! :confetti_ball:"

        elif innings_1_runs < innings_2_runs:

            if challenger_turn == 'bat': winner = player
            elif challenger_turn == 'bowl': winner = ctx.author

            result_text = f"{winner.mention} won the game! :confetti_ball:"

        elif innings_1_runs == innings_2_runs: 
            result_text = f"**Whoa, this game is a draw! :handshake:**"

        embed = discord.Embed(description=(
            f"{result_text}\n\n" +\
            f"Final scoreboard:\n" +\
            f"```\n『 1st Innings 』\n" +  f"⫸ {game.stats['curr_bowler']['player'].name}" +\
            " {runs}({balls})\n\n".format(**game.stats['curr_bowler']) +\
            f"『 2nd Innings 』\n" + f"⫸ {game.stats['curr_batsman']['player'].name}" +\
            " {runs}({balls})```".format(**game.stats['curr_batsman']) +\
            f"\n\n{self.match_end_footer}"
            )).set_author(name=self.bot.user.name, icon_url=str(self.bot.user.avatar_url))
        embed.colour = MAYABLUE
        await ctx.send(embed=embed)
        self.bot.games.pop(ctx.channel.id)
        return await log_game(ctx, GameType.DOUBLE); 
        return        


def setup(bot):
    bot.add_cog(Default(bot))