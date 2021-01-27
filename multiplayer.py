from game import MultiplayerGame
from discord.ext import commands
from utils import *

import discord
import random
import asyncio
import traceback

class Multiplayer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.ACTION_TIMEOUT = 20
        self.cog_brief = 'Multiplayer match commands.'
        self.cog_description = "This category includes commands needed to play the Multiplayer gamemode."

    @commands.command(
        aliases = ['c'],
        brief = 'Creates a multiplayer game.',
        usage = [f"h! create | c", None]
    )
    @commands.guild_only()
    async def create(self, ctx):
        """Creates a lobby for Multiplayer hand cricket match. This allows multiple members to join, the creator will be the host."""
        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or channel.")

        if ctx.channel.id in self.bot.games: return await ctx.send("A game is already running here.")

        new_game = MultiplayerGame.create(ctx, self.bot)
        self.bot.games[ctx.channel.id] = new_game

        wait_msg = await ctx.send(f"A game of hand cricket Multiplayer has been started by **{ctx.author.name}**, "
            f"use {self.bot.prefix}join to join the match!")
        await wait_msg.add_reaction('✅')
        await asyncio.sleep(60)
        try:
            return await wait_msg.clear_reaction('✅')
        except discord.Forbidden: return

    @commands.command(
        aliases = ['j', 'in'],
        brief = 'Join the current multiplayer game.',
        usage = ['h! join | j | in', ['h!join']]
    )
    @before_game_only()
    @multiplayer_game_only()
    @game_only()
    async def join(self, ctx):
        """Joins an existing multiplayer match lobby. You cannot join multiple matches at the same time. 
        You can also join the game through reacting to the green check mark."""
        game = self.bot.games[ctx.channel.id]

        if ctx.author in game.players:
            return await ctx.send("You have already joined the match.")
        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or channel.")

        if len(game.players) == 20: return await ctx.send("Sorry, maximum 20 players can join the match.")

        if game.game_started == True: return await ctx.send("Match has already started.")

        if game.shuffled == True:
            if len(game.TeamA) < len(game.TeamB):
                game.TeamA.append(ctx.author)
            else:
                game.TeamB.append(ctx.author)
        
        game.players.append(ctx.author)
        return await ctx.send("Successfully joined the match. :white_check_mark:")

    @commands.command(
        aliases = ['le'],
        brief = 'Leaves the current multiplayer game.',
        usage = ['h! leave | le', None]
    )
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @participants_only()
    @game_only()
    async def leave(self, ctx):
        """Used for leaving a multiplayer match lobby or any ongoing hand cricket match. 
        If it is a Single player or Player vs Player match, it forfeits the game and shows the scores with no result."""
        game = self.bot.games[ctx.channel.id]
        
        if game.type == GameType.MULTI:
            if ctx.author.id == game.host:
                return await ctx.send("You are a host. change the host to someone else before leaving.")

            if game.game_started in (False, 'pregame'):
                if ctx.author in game.TeamA: game.TeamA.remove(ctx.author)
                elif ctx.author in game.TeamB: game.TeamB.remove(ctx.author)
                else: pass
                game.players.remove(ctx.author)
                return await ctx.send("You have left the game.")

            elif game.game_started == True:
                await ctx.send("Are you sure you want to leave this ongoing match? you will be replaced by a bot. (yes/no)")
                def check(message): return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ('yes','no')

                message = await self.bot.wait_for('message', timeout=25, check=check)
                if message.content.lower() == 'no': return

                game.players.remove(ctx.author)

                game.bot_count += 1
                count = game.bot_count
                BOT = FBot(count=count)
                game.players.append(BOT)

                if ctx.author.id in game.TeamA:
                    stats = game.TeamA.pop(ctx.author.id)

                    game.TeamA[BOT.id] = stats
                    stats['player'] = BOT
                    stats['is_human'] = False
                    for key in ['name', 'runs', 'balls', 'wickets']:
                        game.TeamA[key] = game.TeamA.pop(key)

                    if ctx.author.id == game.curr_batsman['player'].id:
                        game.curr_batsman = game.TeamA[BOT.id]
                    elif ctx.author.id == game.curr_bowler['player'].id:
                        game.curr_bowler = game.TeamA[BOT.id]
                    else: pass

                elif ctx.author.id in game.TeamB:
                    stats = game.TeamB.pop(ctx.author.id)

                    game.TeamB[BOT.id] = stats
                    stats['player'] = BOT
                    stats['is_human'] = False
                    for key in ['name', 'runs', 'balls', 'wickets']:
                        game.TeamB[key] = game.TeamB.pop(key)

                    if ctx.author.id == game.curr_batsman['player'].id:
                        game.curr_batsman = game.TeamB[BOT.id]
                    elif ctx.author.id == game.curr_bowler['player'].id:
                        game.curr_bowler = game.TeamB[BOT.id]
                    else: pass
                        
                return await ctx.send(f"**{ctx.author.name}** has been kicked out of this match, and is replaced by {BOT.mention}")

        if game.game_started == False: return
        elif game.type == GameType.SINGLE:
            if ctx.author.id != game.player: return
            await ctx.send("Are you sure you want to leave this match?")
            def check(message):
                return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ('yes','no')
            message = await self.bot.wait_for('message', timeout=20, check=check)

            if message.content.lower() == 'yes':
                final_result = "The match was a no result."
                stats = (
                    f"```\n『 1st Innings 』\n"
                    f"⫸ {ctx.author.name if game.player_turn == 'batting' else 'Bot'} - {game.innings1_runs}({game.innings1_bowls})\n"
                    f"\n『 2nd Innings 』\n"
                    f"⫸ {'Bot' if game.player_turn == 'batting' else ctx.author.name } - {game.innings2_runs}({game.innings2_bowls})\n```"
                )
                await ctx.send(f"{final_result}\n\nFinal results:\n{stats}")
                self.bot.games.pop(ctx.channel.id)
                return 

            else: return

        elif game.type == GameType.DOUBLE:
            if ctx.author.id not in game.players: return
            await ctx.send("Are you sure you want to leave this match?")
            def check(message):
                return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ('yes','no')
            message = await self.bot.wait_for('message', timeout=20, check=check)

            if message.content.lower() == 'yes':
                opponent_id = game.players[0] if game.players[1] == ctx.author.id else game.players[1]
                opponent: discord.Member = game.stats[opponent_id]['player']

                await ctx.send(
                    f"{opponent.mention}, {ctx.author.mention} has forfeited the match!\n\n" +\
                    "The match was a No result.\n\n" +\
                    "Final scoreboard:\n```\n" + "『 1st Innings 』\n" +\
                    f"⫸ {game.stats['curr_bowler']['player'].name}" +\
                    " {runs}({balls})\n\n".format(**game.stats['curr_bowler']) +\
                    "『 2nd Innings 』\n" +\
                    f"⫸ {game.stats['curr_batsman']['player'].name}" +\
                    " {runs}({balls})```".format(**game.stats['curr_batsman'])
                    )
                self.bot.games.pop(ctx.channel.id)
                return
                
            else: return

    @commands.command(
        brief = 'Shuffles the players into teams.',
        usage = ['h! shuffle', None])
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @min_four_players_only()
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def shuffle(self, ctx):
        """Randomly shuffle the players and split into two teams once enough players join. Shuffling is mandatory to create teams."""
        game = self.bot.games[ctx.channel.id]
        if game.game_started == 'pregame' : return await ctx.send("Cannot shuffle when toss has already begun!")

        random.shuffle(game.players)
        length = len(game.players)

        game.TeamA = game.players[ 0 : int(length/2) ]
        game.TeamB = game.players[ int(length/2) : ]

        await ctx.send("Players have been shuffled.")
        if game.shuffled == False:
            game.shuffled = True
            return await self.bot.get_cog('Multiplayer').playerlist(ctx)

    @commands.command(
        aliases = ['overs'],
        brief = 'Sets overs for the game.',
        usage = ['h! setovers | overs <number>', ['h!setovers 2', 'h!setovers 5', 'h!setovers 20', 'h!overs 6']]
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def setovers(self, ctx, arg: int):
        """Set the maximum number of overs each team will play in the Multiplayer match. 
        You can set a minimum of 2 or maximum of 20 overs. Setting overs is mandatory."""
        if arg > 20 or arg < 2:
            return await ctx.send("Choose a number between 2 and 20")

        else: 
            game = self.bot.games[ctx.channel.id]
            game.overs = int(arg) * 6
            return await ctx.send("Overs has been set to {}".format(game.overs/6))

    @commands.command(
        aliases = ['del', 'yeet', 'forfeit'],
        brief = 'Deletes the current multiplayer game.',
        usage = ['h! delete | del | yeet | forfeit', None]
    )
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def delete(self, ctx):
        """Deletes the ongoing Multiplayer match, whether its started or not. Be careful when deleting matches. 
        All stats will be lost and no scoreboard will be posted upon abandoning it."""
        if ctx.channel.id not in self.bot.games: return await ctx.send("Nothing to delete.")

        await ctx.send("Dude are you sure you want to delete this match? (yes/no)")

        def check(message): return message.channel.id == ctx.channel.id and message.author.id == ctx.author.id and message.content.lower() in ('yes','no') 
        try: message = await self.bot.wait_for('message', timeout=25, check=check)
        except asyncio.TimeoutError: return

        if message.content.lower() == 'yes':
            self.bot.games.pop(ctx.channel.id)
            return await ctx.send("Match has been abandoned.")
        else: return

    @commands.command(
        aliases = ['pl', 'plist', 'players'],
        brief = 'Shows the full list of players Team wise.',
        usage = ['h! playerlist | pl | plist | players', None]
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @participants_only()
    @shuffled_only()
    @multiplayer_game_only()
    @game_only()
    async def playerlist(self, ctx):
        """Shows the full player list and who is in which team. If this command is used before starting match, it only shows the two teams composition.
        If this command is used after the match has started, it will also show how many runs and wickets each player has scored, 0/0 if their turn hasn't came yet."""
        game = self.bot.games[ctx.channel.id]; 
        mid_num = int( (len(game.players)/2)+1 )

        if game.game_started in (False, 'pregame'):
            A, B = '```', '```'; 
            for num, player in enumerate(game.TeamA, start=1): 
                A += str(num) + '. ' + player.name \
                + f" {'(H)' if player.id == game.host else ''}" \
                + f" {'(C)' if num == 1 else ''}" + '\n' 

            for num, player in enumerate(game.TeamB, start=mid_num): 
                B += str(num) + '. ' + player.name \
                + f" {'(H)' if player.id == game.host else ''}" \
                + f" {'(C)' if num == mid_num else ''}" + '\n' 
            A += '```'; B += '```'

            embed = discord.Embed(title='Teams composition')
            embed.set_thumbnail(url=str(ctx.guild.icon_url))
            embed.set_footer(text=f'Use {self.bot.prefix}swap <num> <num> to swap the position of two players.')
            embed.color = 0x73C2FB

            embed.add_field(name='Team A:', value=A, inline=False)
            embed.add_field(name='Team B:', value=B, inline=False)
            return await ctx.send(embed=embed)

        elif game.game_started == True:
            A, B = '```', '```'
            for pl_id in game.TeamA.keys():
                if pl_id in ('name','runs','balls','wickets'): continue

                A += spacing(game.TeamA[pl_id]['player'].name) + \
                    "{runs}({balls}) || {wickets}-{runs_given}".format(**game.TeamA[pl_id]) + \
                    " ({})\n".format(overs(game.TeamA[pl_id]['balls_given']))

            for pl_id in game.TeamB.keys():
                if pl_id in ('name','runs','balls','wickets'): continue

                B += spacing(game.TeamB[pl_id]['player'].name) + \
                    "{runs}({balls}) || {wickets}-{runs_given}".format(**game.TeamB[pl_id]) + \
                    " ({})\n".format(overs(game.TeamB[pl_id]['balls_given']))

            A += '```'; B += '```'
            embed = discord.Embed(title='Player stats')
            embed.set_thumbnail(url=str(ctx.guild.icon_url))
            embed.color = 0x73C2FB

            embed.add_field(name='Team A:', value=A, inline=False)
            embed.add_field(name='Team B:', value=B, inline=False)
            return await ctx.send(embed=embed)

    @commands.command(
        brief = 'Swaps two players.',
        usage = ['h!swap <Player 1 no.> <Player 2 no.>', ['h!swap 2 6', 'h!swap 3 8', 'h!swap 5 7']])
    @shuffled_only()
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def swap(self, ctx, arg1: int, arg2: int):
        """Using this command you can swap the positions of two players in teams.
        To swap, use the position number of the player in playerlist. For eg. if PlayerA is in position 3. and PlayerB in position 5.
        do command *swap 3 5* and it'll swap their positions. You can swap players between a Team (to change a captain) and swap between two teams."""
        game = self.bot.games[ctx.channel.id]
        if arg1 -1 > len(game.players) or arg2 -1 > len(game.players):
            return await ctx.send(":x: Choose numbers within the playerlist.")

        arg1 -= 1; arg2 -= 1 
        game.players[arg1], game.players[arg2] = game.players[arg2], game.players[arg1]
        length = len(game.players)

        game.TeamA = game.players[ 0 : int(length/2) ]
        game.TeamB = game.players[ int(length/2) : ]

        return await ctx.send(f"Swapped {game.players[arg1].name} and {game.players[arg2].name}")

    @commands.command(
        aliases = ['ch', 'host', 'newhost'],
        brief = 'Changes the game host.',
        usage = ['h! changehost | ch | host | newhost', ['h!changehost @SAMIR', 'h!newhost @SAMIR']]
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @participants_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def changehost(self, ctx, arg: discord.Member):
        """Changes the host to the tagged person. The host is responsible for setting overs, swapping players,
        doing toss, shuffle players and deleting the match anytime if they want to."""
        game = self.bot.games[ctx.channel.id]

        if arg not in game.players:
            return await ctx.send("Choose a player from the playerlist.")
        if arg == ctx.author:
            return await ctx.send("You are already the host.")

        else:
            game.host = arg.id
            return await ctx.send(f"The new host is now {arg.name}")

    @commands.command(
        brief = 'Adds a dummy player.',
        usage = ['h! addbot', ['h!addbot 2', 'h!addbot 5', 'h!addbot']])
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @participants_only()
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def addbot(self, ctx, arg: int = 1):
        """Adds a bot player in the playerlist who is just an automated player. If in case not many members join the match lobby,
        you can add bots to meet minimum 4 players requirement or add some additional players.
        
        *Note: The main point of adding bots is to fill the space if there is unequal amount of players. 
        I do not recommend filling the team with bots, its a lot more fun to play with server members.*"""
        game = self.bot.games[ctx.channel.id]
        if len(game.players) == 20: return await ctx.send("Can't add more than 20 players, Only 10 players on each side.")

        added_arg = 0
        for i in range(0, arg):
            
            game.bot_count += 1
            count = game.bot_count
            BOT = FBot(count=count)

            game.players.append(BOT)
            if game.shuffled == True:
                if len(game.TeamA) < len(game.TeamB):
                    game.TeamA.append(BOT)
                else:
                    game.TeamB.append(BOT)
            added_arg += 1
            if len(game.players) == 20 : break
        return await ctx.send(f"Successfully added {added_arg} bot{pz(added_arg)}. :white_check_mark:")


    @commands.command(
        brief = 'Removes a dummy player.',
        usage = ['h! removebot', None])
    @participants_only()
    @before_game_only()
    @host_only()    
    @multiplayer_game_only()
    @game_only()
    async def removebot(self, ctx):
        """Removes a bot player from the team if it is not needed. You can remove one bot each command."""
        game = self.bot.games[ctx.channel.id]

        if game.bot_count == 0: return await ctx.send("No bots to remove.")
        
        for player in game.players:
            if len(str(player.id)) < 4 and player.id -100 == game.bot_count:
                game.players.remove(player)
                if player in game.TeamA: game.TeamA.remove(player)
                elif player in game.TeamB: game.TeamB.remove(player)
                else: pass

                game.bot_count -= 1
                return await ctx.send(f"Removed {player.name}")

    @commands.command(
        aliases = ['kick'],
        brief = 'Removes a player from the game.',
        usage = ['h! remove | kick <player tag>', ['h!kick @SAMIR', 'h!remove @SAMIR']]
    )
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @participants_only()
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def remove(self, ctx, arg: discord.Member):
        """Removes a player from the match lobby. You cannot remove players when match has started, in case if the player is afk, HandCricket Bot will 
        automatically roll a number for that player each 20 seconds."""
        game = self.bot.games[ctx.channel.id]
        if arg not in game.players: return await ctx.send("Player has not joined the game.")

        if arg == ctx.author:
            return await ctx.send(f"Can't remove yourself as a host.")

        else:
            game.players.remove(arg)
            if arg in game.TeamA: game.TeamA.remove(arg)
            elif arg in game.TeamB: game.TeamB.remove(arg)
            else: pass
            return await ctx.send(f"Removed **{arg.name}**")

    @commands.command(
        brief = 'Begins toss for the teams.',
        usage = ['h! toss', None])
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @min_four_players_only()
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def toss(self, ctx):
        """Does the toss for the both teams before starting a match. Toss helps in deciding which team will bat first and which team will bowl first.
        The respective team captains do the coin toss and then the winner captain decides if they wants to bat first or bowl."""
        game = self.bot.games[ctx.channel.id]
        game.game_started = 'pregame'

        if game.toss_winner is not None: return await ctx.send("Toss has already been done.")
        await ctx.send(f"Starting toss, **Team A** captain **{game.TeamA[0].name}** choose heads or tails? (heads/tails)")

        def check(message): return message.author == game.TeamA[0] and message.channel == ctx.channel \
                            and message.content.lower() in ('heads', 'tails')

        if len(str(game.TeamA[0].id)) < 4:
            message = random.choice(['heads', 'tails'])
            await asyncio.sleep(5)

        else:
            try:
                message = await self.bot.wait_for('message', timeout=60, check=check)
                message = message.content.lower()
            except asyncio.TimeoutError:
                message = 'heads'

        if message == random.choice(['heads', 'tails']): 

            toss_winner = 'Team A'
            toss_winner_cpt = game.TeamA[0]

        else: 
            toss_winner = 'Team B'
            toss_winner_cpt = game.TeamB[0]
            
        await ctx.send(f"**{toss_winner}** has won the toss. **{toss_winner}** captain **{toss_winner_cpt.name}** Choose bat or bowl? (bat/bowl)")    

        def check02(message): return message.author == toss_winner_cpt and message.channel == ctx.channel \
                                and message.content.lower() in ('bat', 'bowl')

        if len(str(toss_winner_cpt.id)) < 4:
            message = random.choice(['bat', 'bowl'])
            await asyncio.sleep(5)

        else:
            try:
                message = await self.bot.wait_for('message', timeout=60, check=check02)
                message = message.content.lower()
            except asyncio.TimeoutError:
                message = 'bowl'

        game.toss_winner = toss_winner
        if toss_winner == 'Team A':
            game.TeamA_turn = message

        elif toss_winner == 'Team B':
            if message == 'bat': game.TeamA_turn = 'bowl'
            elif message == 'bowl': game.TeamA_turn = 'bat'

        game.game_started = False

        await ctx.send(f"**{toss_winner}** has decided to **{message} first!** use {self.bot.prefix}start to start the game.")

    @commands.command(brief = 'Starts the multiplayer match.', usage = ['h!start', None])
    @shuffled_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def start(self, ctx):
        """*Breaths deeply* Finally this command starts the match, Bot will there after tell who will bat first and who will bowl first.
        Once a match is started cannot be paused. If a player goes afk, Bot will roll a random number on behalf of it. (In case of a bot player it already is.)"""

        game = self.bot.games[ctx.channel.id]
        if game.overs == None: return await ctx.send(f"Set overs first.")
        if game.TeamA_turn == None: return await ctx.send(f"You have not done the toss. use {self.bot.prefix}toss to do decide who will bat first.")
        if len(game.players) <4: return await ctx.send(f"At least 4 players are required to start the game. If no one joins, try using the addbot command.")
        if len(game.TeamA) != len(game.TeamB): return await ctx.send("There is an unequal amount of players on both sides. try adding a bot if no one joins.")
        
        await ctx.send("Starting match! :stadium:")
        await game.initialise()
        await asyncio.sleep(3)


        def check(message): return message.channel.type == discord.ChannelType.private \
            and message.author.id in participants_ids \
            and message.content in ('0','1','2','3','4','5','6',)
        
        for playerid in game.batting_team.keys():
            if playerid in ('name','runs','balls','wickets') or game.batting_team[playerid]['is_out'] == True:
                continue
            else:
                game.curr_batsman = game.batting_team[playerid]; break

        index = 0
        keys = list(game.bowling_team.keys())
        for playerid in keys:
            if playerid in ('name','runs','balls','wickets'):
                continue
            else:
                game.curr_bowler = game.bowling_team[playerid]; break

        participants_ids = [game.curr_batsman['player'].id, game.curr_bowler['player'].id]
        msg = '\n\n'.join([
            f"Innings 1 has started!" ,
            f"First batsman is **{game.curr_batsman['player'].name}** " ,
            f"First bowler is **{game.curr_bowler['player'].name}** " ,
            f"Start sending me your actions in my DMs"
        ])
        await ctx.send(msg)

        while True:

            try:
                if game.curr_batsman['is_human'] == False:
                    game.curr_batsman['last_action'] = random.randint(0,6)
                    participants_ids.remove(game.curr_batsman['player'].id)

                else:
                    message = await self.bot.wait_for('message', timeout=self.ACTION_TIMEOUT, check=check)
                    if message.author.id in game.TeamA: game.TeamA[message.author.id]['last_action'] = int(message.content.lower())
                    else: game.TeamB[message.author.id]['last_action'] = int(message.content.lower())
                    participants_ids.remove(message.author.id)

                if game.curr_bowler['is_human'] == False:
                    game.curr_bowler['last_action'] = random.randint(0,6)
                    participants_ids.remove(game.curr_bowler['player'].id)
                    if game.curr_batsman['is_human'] == False: await asyncio.sleep(3)

                else:
                    message = await self.bot.wait_for('message', timeout=self.ACTION_TIMEOUT, check=check)
                    if message.author.id in game.TeamA: game.TeamA[message.author.id]['last_action'] = int(message.content.lower())
                    else: game.TeamB[message.author.id]['last_action'] = int(message.content.lower())
                    participants_ids.remove(message.author.id)
                
            except asyncio.TimeoutError:
                if ctx.channel.id not in self.bot.games: return

                if game.curr_batsman['player'].id in participants_ids:
                    game.curr_batsman['last_action'] = random.randint(0,6)

                if game.curr_bowler['player'].id in participants_ids:
                    game.curr_bowler['last_action'] = random.randint(0,6)

            if ctx.channel.id not in self.bot.games: return
            if game.curr_batsman['last_action'] != game.curr_bowler['last_action']: 

                await game.increment_runs()

                await game.send_msg('BATSMAN', "Opponent's last action -> {}\n".format(game.curr_bowler['last_action']) + 
                                         "Your score: {runs} ({balls})".format(**game.curr_batsman))
                
                await game.send_msg('BOWLER', "Opponent's last action -> {last_action}\nOpponent score: {runs} ({balls})".format(**game.curr_batsman))
                participants_ids = [game.curr_batsman['player'].id, game.curr_bowler['player'].id]

            elif game.curr_batsman['last_action'] == game.curr_bowler['last_action']: 

                await game.increment_wicket()
                
                await game.send_msg('BATSMAN', "You are out! \nOpponent's last action {} \n".format(game.curr_bowler['last_action']) + 
                                         "score: {runs} ({balls})".format(**game.curr_batsman))
                
                await game.send_msg('BOWLER', "Opponent is out! \nOpponent's last action {last_action} \nscore: {runs} ({balls})".format(**game.curr_batsman))

                msg = '\n'.join([
                    "**{}** is out! bowled by **{}**".format(game.curr_batsman['player'].name, game.curr_bowler['player'].name),
                    "```{player.name}: {runs} ({balls})".format(**game.curr_batsman),
                    "{player.name}: {wickets} - {runs_given}```".format(**game.curr_bowler),
                    "**{name}** score: {runs}/{wickets}".format(**game.batting_team) + \
                    "  {} overs\n\n".format(overs(game.batting_team['balls']))
                ])
                
                for playerid in game.batting_team.keys():
                    if playerid in ('name','runs','balls','wickets') or game.batting_team[playerid]['is_out'] == True:
                        continue
                    else:
                        game.curr_batsman = game.batting_team[playerid]; 
                        await ctx.send(msg + f"Next batsman is **{game.curr_batsman['player'].name}**")
                        break
                    
                else:
                    _target = game.batting_team['runs']+1
                    msg += '\n'.join([
                        "**{name}** is all out! Innings over.".format(**game.batting_team),
                        "⫸ Final score: {runs}/{wickets}".format(**game.batting_team) + \
                        "  {} overs\n\n".format(overs(game.batting_team['balls'])),
                        "**{}** needs {} run{} to win.".format(game.bowling_team['name'], _target, pz(_target)),
                        "\nInnings 2 starting in 10 seconds."
                    ])
                    await ctx.send(msg)
                    break

                participants_ids = [game.curr_batsman['player'].id, game.curr_bowler['player'].id]

            if game.batting_team['balls'] == game.overs:

                await game.send_msg('BOWLER', "Innings are over!")
                msg = ''.join([
                    "Innings Over!\n\n",
                    "**{name}** score: {runs} / {wickets}".format(**game.batting_team),
                    "  {} overs\n\n".format(overs(game.batting_team['balls'])),
                    "\n**{0}** need {1} runs to win!\n\n".format(game.bowling_team['name'], game.batting_team['runs']+1),
                    "\nInnings 2 starting in 10 seconds."
                ])
                await ctx.send(msg)
                break

            elif game.curr_bowler['balls_given'] % 6 == 0:
                
                await game.send_msg('BOWLER', "Your over is finished!")
                index, keys = await game.next_bowler(index, keys)

                msg = '\n'.join([ 
                    "After this over → {player.name}'s score: {runs} ({balls})".format(**game.curr_batsman),
                    f"Next bowler to bowl is {game.curr_bowler['player'].mention}, start sending actions."
                ])
                await ctx.send(msg)
                participants_ids = [game.curr_batsman['player'].id, game.curr_bowler['player'].id]
                continue
            
            else:
                continue

        await game.change_innings()
        await asyncio.sleep(10)

        for playerid in game.batting_team.keys():
            if playerid in ('name','runs','balls','wickets'):
                continue
            else:
                game.curr_batsman = game.batting_team[playerid]; break

        index = 0
        keys = list(game.bowling_team.keys())
        for playerid in keys:
            if playerid in ('name','runs','balls','wickets'):
                continue
            else:
                game.curr_bowler = game.bowling_team[playerid]; break

        participants_ids = [game.curr_batsman['player'].id, game.curr_bowler['player'].id]
        msg = '\n\n'.join([
            f"Innings 2 has started!",
            f"First batsman is **{game.curr_batsman['player'].name}** " ,
            f"First bowler is **{game.curr_bowler['player'].name}** " ,
            f"Start sending me your actions in my DMs"
        ])
        await ctx.send(msg)

        while True:

            try:
                if game.curr_batsman['is_human'] == False:
                    game.curr_batsman['last_action'] = random.randint(0,6)
                    participants_ids.remove(game.curr_batsman['player'].id)

                else:
                    message = await self.bot.wait_for('message', timeout=self.ACTION_TIMEOUT, check=check)
                    participants_ids.remove(message.author.id)
                    if message.author.id in game.TeamA: game.TeamA[message.author.id]['last_action'] = int(message.content.lower())
                    else: game.TeamB[message.author.id]['last_action'] = int(message.content.lower())

                if game.curr_bowler['is_human'] == False:
                    game.curr_bowler['last_action'] = random.randint(0,6)
                    participants_ids.remove(game.curr_bowler['player'].id)
                    if game.curr_batsman['is_human'] == False: await asyncio.sleep(3)

                else:
                    message = await self.bot.wait_for('message', timeout=self.ACTION_TIMEOUT, check=check)
                    participants_ids.remove(message.author.id)
                    if message.author.id in game.TeamA: game.TeamA[message.author.id]['last_action'] = int(message.content.lower())
                    else: game.TeamB[message.author.id]['last_action'] = int(message.content.lower())
                
            except asyncio.TimeoutError:
                if ctx.channel.id not in self.bot.games: return

                if game.curr_batsman['player'].id in participants_ids:
                    game.curr_batsman['last_action'] = random.randint(0,6)

                if game.curr_bowler['player'].id in participants_ids:
                    game.curr_bowler['last_action'] = random.randint(0,6)

            if ctx.channel.id not in self.bot.games: return
            if game.curr_batsman['last_action'] != game.curr_bowler['last_action']: 

                await game.increment_runs()
                
                await game.send_msg('BATSMAN', "Opponent's last action -> {}\n".format(game.curr_bowler['last_action']) + 
                                               "Your score: {runs} ({balls})".format(**game.curr_batsman))

                await game.send_msg('BOWLER', "Opponent's last action -> {last_action}\nOpponent score: {runs} ({balls})".format(**game.curr_batsman))
                participants_ids = [game.curr_batsman['player'].id, game.curr_bowler['player'].id]

                if game.batting_team['runs'] > game.bowling_team['runs']:
                    await ctx.send("Score has been chased!\nInnings over.")
                    break

            elif game.curr_batsman['last_action'] == game.curr_bowler['last_action']: 

                await game.increment_wicket()
                                
                await game.send_msg('BATSMAN', "You are out! \nOpponent's last action {} \n".format(game.curr_bowler['last_action']) + 
                                              "score: {runs} ({balls})".format(**game.curr_batsman))

                await game.send_msg('BOWLER', "Opponent is out! \nOpponent's last action {last_action} \nscore: {runs} ({balls})".format(**game.curr_batsman))

                msg = '\n'.join([
                    "**{}** is out! bowled by **{}**".format(game.curr_batsman['player'].name, game.curr_bowler['player'].name),
                    "```{player.name}: {runs} ({balls})".format(**game.curr_batsman),
                    "{player.name}: {wickets} - {runs_given}```".format(**game.curr_bowler),
                    "**{name}** score: {runs}/{wickets}".format(**game.batting_team) + \
                    "  {} overs\n\n".format(overs(game.batting_team['balls']))
                ])
                
                for playerid in game.batting_team.keys():
                    if playerid in ('name','runs','balls','wickets') or game.batting_team[playerid]['is_out'] == True:
                        continue
                    else:
                        game.curr_batsman = game.batting_team[playerid]; 
                        await ctx.send(msg + f"Next batsman is **{game.curr_batsman['player'].name}**")
                        break
                    
                else:
                    msg += '\n'.join([
                        "**{name}** is all out! Innings over.".format(**game.batting_team),
                        "⫸ Final score: {runs}/{wickets}".format(**game.batting_team) + \
                        "  {} overs\n\n".format(overs(game.batting_team['balls']))
                    ])
                    await ctx.send(msg)
                    break

                participants_ids = [game.curr_batsman['player'].id, game.curr_bowler['player'].id]

            if game.batting_team['balls'] == game.overs:

                await game.send_msg('BOWLER', "Innings are over!")
                msg = ''.join([ 
                    "Innings Over!\n\n",
                    "**{name}** score: {runs} / {wickets}".format(**game.batting_team),
                    "  {} overs\n\n".format(overs(game.batting_team['balls'])), 
                    "The match is over!"
                    ])
                await ctx.send(msg)
                break

            elif game.curr_bowler['balls_given'] % 6 == 0:

                await game.send_msg('BOWLER', "Your over is finished!")
                index, keys = await game.next_bowler(index, keys)

                msg = '\n'.join([ 
                    "After this over → {player.name}'s score: {runs} ({balls})".format(**game.curr_batsman),
                    f"Next bowler to bowl is {game.curr_bowler['player'].mention}, start sending actions."
                ])
                await ctx.send(msg)
                participants_ids = [game.curr_batsman['player'].id, game.curr_bowler['player'].id]
                continue
            
            else:
                continue
                
        await game.check_endgame()
        await ctx.send(game.result)
        try: 
            await game.generate_scorecard_image()
        except Exception as e: 
            traceback.print_exc() 
            await game.make_scoreboard()
        self.bot.games.pop(ctx.channel.id)
        await log_game(ctx, GameType.MULTI)
        return

    @commands.command(brief = 'Shows the current status of the game.', usage = ['h! status', None])
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @participants_only()
    @after_game_only()
    @multiplayer_game_only()
    @game_only()
    async def status(self, ctx):
        """Shows live status of the current multiplayer match, it gives info about what Innings it is,
        Scores of both Teams, how many wickets they lost, which player is batting, which player is bowling and/or 
        How many runs left to chase if its second innings."""

        game = self.bot.games[ctx.channel.id]
        overs_done = overs(game.batting_team['balls'])
        overs_left = overs(game.overs)
        for player in game.players: 
            if player.id == game.host: host_name = player.name ; break

        embed = discord.Embed(title="Match Status")
        embed.colour = MAYABLUE
        embed.set_author(name=ctx.guild.name, icon_url=str(ctx.guild.icon_url))
        embed.add_field(name="Innings", value="**{}**".format(game.innings.value), inline=True)
        embed.add_field(name="Overs", value="{} / {}".format(overs_done, overs_left), inline=True)
        embed.add_field(name="Host", value="{}".format(host_name), inline=True)
        embed.add_field(
            name=game.bowling_team['name'],
            value="{runs}/{wickets}  ".format(**game.bowling_team) + "({} overs)".format(overs(game.bowling_team['balls'])),
            inline=False
        )
        embed.add_field(
            name=game.batting_team['name'],
            value="{runs}/{wickets}  ".format(**game.batting_team) + "({} overs)".format(overs(game.batting_team['balls'])),
            inline=True
        )
        embed.add_field(
            name="Batsman",
            value="**{player.name}:** {runs} ({balls}) runs".format(**game.curr_batsman),
            inline=False
        )
        embed.add_field(
            name="Bowler",
            value="**{player.name}:** {runs_given} - {wickets}".format(**game.curr_bowler) + " ({} overs)".format(overs(game.curr_bowler['balls_given'])),
            inline=True
        )
        if game.innings == Innings.TWO:
            name = game.batting_team['name']
            runs = game.bowling_team['runs']-game.batting_team['runs']+1
            balls = game.overs-game.batting_team['balls']
            wickets = len(game.batting_team)-game.batting_team['wickets']-4
            embed.set_footer(text="{} needs {} more run{} to win from {} ball{} and {} wicket{}.".format(
                name, runs,
                pz(runs), balls, pz(balls), wickets, pz(wickets)
            ))
        return await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Multiplayer(bot))