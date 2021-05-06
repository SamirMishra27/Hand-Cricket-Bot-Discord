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
        aliases = ['c', 'create_multiplayer'],
        brief = 'Creates a multiplayer game.',
        usage = [f"h! create | c | create_multiplayer", None],
        description = "".join(strings['create_desc'])
    )
    @commands.guild_only()
    async def create(self, ctx):
        
        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or channel.")

        if ctx.channel.id in self.bot.games: return await ctx.send("A game is already running here.")

        new_game = MultiplayerGame.create(ctx, self.bot)
        self.bot.games[ctx.channel.id] = new_game

        wait_msg = await ctx.send(f"A game of hand cricket Multiplayer has been started by **{ctx.author.name}**, "
            f"use {self.bot.prefix}join to join the match!")
        await wait_msg.add_reaction(misc_emojis['rtj'])
        await asyncio.sleep(60)
        try:
            return await wait_msg.clear_reaction(misc_emojis['rtj'])
        except discord.Forbidden: return


    @commands.command(
        brief = 'Shuffles the players into teams.',
        usage = ['h! shuffle', None],
        description = "".join(strings['shuffle_desc'])
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @min_four_players_only()
    @before_game_only()
    @host_only()
    @multiplayer_mode_only()
    @multiplayer_game_only()
    @game_only()
    async def shuffle(self, ctx):
        
        game = self.bot.games[ctx.channel.id]
        if game.game_started == 'pregame' : return await ctx.send("Cannot shuffle when toss has already begun!")

        random.shuffle(game.players)
        length = len(game.players)

        game.TeamA = game.players[ 0 : int(length/2) ]
        game.TeamB = game.players[ int(length/2) : ]

        await ctx.send("Players have been shuffled.")
        if game.shuffled == False:
            game.shuffled = True
            # return await self.bot.get_cog('Multiplayer').playerlist(ctx)
            return await self.bot.get_cog('General').playerlist(ctx)

    @commands.command(
        aliases = ['overs'],
        brief = 'Sets overs for the game.',
        usage = ['h! setovers | overs <number>', ['h!setovers 2', 'h!setovers 5', 'h!setovers 20', 'h!overs 6']],
        description = "".join(strings['setovers_desc'])
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @before_game_only()
    @host_only()
    @multiplayer_mode_only()
    @multiplayer_game_only()
    @game_only()
    async def setovers(self, ctx, arg: int):
        
        if arg > 20 or arg < 2:
            return await ctx.send("Choose a number between 2 and 20")

        else: 
            game = self.bot.games[ctx.channel.id]
            game.overs = int(arg) * 6
            return await ctx.send("Overs has been set to {}".format(game.overs/6))

    @commands.command(
        brief = 'Swaps two players.',
        usage = ['h!swap <Player 1 no.> <Player 2 no.>', ['h!swap 2 6', 'h!swap 3 8', 'h!swap 5 7']],
        description = "".join(strings['swap_desc']))
    @shuffled_only()
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def swap(self, ctx, arg1: int, arg2: int):
        
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
        brief = 'Begins toss for the teams.',
        usage = ['h! toss', None],
        description = "".join(strings['toss_desc']))
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @min_four_players_only()
    @before_game_only()
    @shuffled_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def toss(self, ctx):
        
        game = self.bot.games[ctx.channel.id]
        game.game_started = 'pregame'

        if game.toss_winner is not None: return await ctx.send("Toss has already been done.")
        await ctx.send(f"Starting toss, **{game.team_settings['Team A name']}** captain **{game.TeamA[0].mention}** choose heads or tails? (heads/tails)")

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

            toss_winner = game.team_settings['Team A name']
            toss_winner_cpt = game.TeamA[0]

        else: 
            toss_winner = game.team_settings['Team B name']
            toss_winner_cpt = game.TeamB[0]
            
        await ctx.send(f"**{toss_winner}** has won the toss. **{toss_winner}** captain **{toss_winner_cpt.mention}** Choose bat or bowl? (bat/bowl)")    

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
        if toss_winner == game.team_settings['Team A name']:
            game.TeamA_turn = message

        elif toss_winner == game.team_settings['Team B name']:
            if message == 'bat': game.TeamA_turn = 'bowl'
            elif message == 'bowl': game.TeamA_turn = 'bat'

        game.game_started = False

        await ctx.send(f"**{toss_winner}** has decided to **{message} first!** use {self.bot.prefix}start to start the game.")

    async def _start_multiplayer_match(self, ctx):
        
        game = self.bot.games[ctx.channel.id]
        
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
            f"First batsman is **{game.curr_batsman['player'].mention}** " ,
            f"First bowler is **{game.curr_bowler['player'].mention}** " ,
            f"Start sending me your actions in my DMs"
        ])
        await ctx.send(msg)
        self.bot.loop.create_task(self.bot.get_cog('Multiplayer').status(ctx))

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
                
                await game.send_msg('BATSMAN', "You are out! \nOpponent's last action -> {} \n".format(game.curr_bowler['last_action']) + 
                                         "score: {runs} ({balls})".format(**game.curr_batsman) + f" {ctx.channel.mention}")

                await game.send_msg('BOWLER', "Opponent is out! \nOpponent's last action -> {last_action} \nscore: {runs} ({balls})".format(**game.curr_batsman))

                msg = '\n'.join([
                    "**{}** is out! bowled by **{}**".format(game.curr_batsman['player'].name, game.curr_bowler['player'].name),
                    "```{player.name}: {runs} ({balls})".format(**game.curr_batsman),
                    "{player.name}: {wickets} - {runs_given}```".format(**game.curr_bowler),
                    "**{name}** score: {runs}/{wickets}".format(**game.batting_team) + \
                    "  -  {} overs\n\n".format(overs(game.batting_team['balls']))
                ])
                
                for playerid in game.batting_team.keys():
                    if playerid in ('name','runs','balls','wickets') or game.batting_team[playerid]['is_out'] == True:
                        continue
                    else:
                        game.curr_batsman = game.batting_team[playerid]; 
                        next_batsman_msg = f"Next batsman is **{game.curr_batsman['player'].mention}**"
                        await game.send_msg('BOWLER', next_batsman_msg)
                        await ctx.send(msg + next_batsman_msg)
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

                await game.send_msg('BOWLER', "Innings are over!"  + f" {ctx.channel.mention}")
                await game.send_msg('BATSMAN', "Innings are over!"  + f" {ctx.channel.mention}")
                await asyncio.sleep(0.5)
                msg = ''.join([
                    "**Innings Over!**\n\n",
                    "**{name}** score: {runs} / {wickets}".format(**game.batting_team),
                    "  {} overs\n".format(overs(game.batting_team['balls'])),
                    "\n**{0}** need {1} runs to win!\n".format(game.bowling_team['name'], game.batting_team['runs']+1),
                    "\nInnings 2 starting in 10 seconds."
                ])
                await ctx.send(msg)
                break

            elif game.curr_bowler['balls_given'] % 6 == 0:
                
                await game.send_msg('BOWLER', "Your over is finished!" + f" {ctx.channel.mention}")
                await asyncio.sleep(0.5)
                keys = list(game.bowling_team.keys())
                index, keys = await game.next_bowler(index, keys)

                msg = '\n'.join([ 
                    "After this over → {player.name}'s score: {runs} ({balls})".format(**game.curr_batsman),
                    f"Next bowler to bowl is {game.curr_bowler['player'].mention}, start sending actions."
                ])
                await ctx.send(msg)
                await game.send_msg('BATSMAN', f"Next bowler to bowl is {game.curr_bowler['player'].mention}")
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
            f"First batsman is **{game.curr_batsman['player'].mention}** " ,
            f"First bowler is **{game.curr_bowler['player'].mention}** " ,
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
                                
                await game.send_msg('BATSMAN', "You are out! \nOpponent's last action -> {} \n".format(game.curr_bowler['last_action']) + 
                                              "score: {runs} ({balls})".format(**game.curr_batsman) + f' {ctx.channel.mention}')

                await game.send_msg('BOWLER', "Opponent is out! \nOpponent's last action -> {last_action} \nscore: {runs} ({balls})".format(**game.curr_batsman))

                msg = '\n'.join([
                    "**{}** is out! bowled by **{}**".format(game.curr_batsman['player'].name, game.curr_bowler['player'].name),
                    "```{player.name}: {runs} ({balls})".format(**game.curr_batsman),
                    "{player.name}: {wickets} - {runs_given}```".format(**game.curr_bowler),
                    "**{name}** score: {runs}/{wickets}".format(**game.batting_team) + \
                    "  -  {} overs\n\n".format(overs(game.batting_team['balls']))
                ])
                
                for playerid in game.batting_team.keys():
                    if playerid in ('name','runs','balls','wickets') or game.batting_team[playerid]['is_out'] == True:
                        continue
                    else:
                        game.curr_batsman = game.batting_team[playerid]; 
                        next_batsman_msg = f"Next batsman is **{game.curr_batsman['player'].mention}**"
                        await game.send_msg('BOWLER', next_batsman_msg)
                        await ctx.send(msg + next_batsman_msg)
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

                await game.send_msg('BOWLER', "Innings are over!" + f' {ctx.channel.mention}')
                await game.send_msg('BATSMAN', "Innings are over!" + f' {ctx.channel.mention}')
                await asyncio.sleep(0.5)
                msg = ''.join([ 
                    "Innings Over!\n\n",
                    "**{name}** score: {runs} / {wickets}".format(**game.batting_team),
                    "  {} overs\n\n".format(overs(game.batting_team['balls'])), 
                    "The match is over!"
                    ])
                await ctx.send(msg)
                break

            elif game.curr_bowler['balls_given'] % 6 == 0:

                await game.send_msg('BOWLER', "Your over is finished!" + f' {ctx.channel.mention}')
                await asyncio.sleep(0.5)
                keys = list(game.bowling_team.keys())
                index, keys = await game.next_bowler(index, keys)

                msg = '\n'.join([ 
                    "After this over → {player.name}'s score: {runs} ({balls})".format(**game.curr_batsman),
                    f"Next bowler to bowl is {game.curr_bowler['player'].mention}, start sending actions."
                ])
                await ctx.send(msg)
                await game.send_msg('BATSMAN', f"Next bowler to bowl is {game.curr_bowler['player'].mention}")
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
        self.bot.get_cog("GlobalEvents").insert_data_in_events(game)
        await log_game(ctx, GameType.MULTI)
        return

    @commands.command(brief = 'Shows the current status of the game.', 
    usage = ['h! status', None], 
    description="".join(strings['status_desc']))
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @participants_only()
    @after_game_only()
    @multiplayer_game_only()
    @game_only()
    async def status(self, ctx):        

        game = self.bot.games[ctx.channel.id]
        if game.is_updating == True:
            return await ctx.send("Please wait!")
        game.is_updating = True
        async def query_stats(self, add_image=True):
            overs_done = overs(game.batting_team['balls']) 
            overs_left = overs(game.overs)
            for player in game.players: 
                if player.id == game.host: host_name = player.name ; break

            embed = discord.Embed(title="Match Status")
            embed.colour = MAYABLUE
            embed.set_author(name=ctx.guild.name, icon_url=str(ctx.guild.icon_url))
            if add_image == True:
                embed.set_image(url=live_gif)
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
            return embed
        status_message = await ctx.send(embed=await query_stats(self, add_image=True))
        for i in range(0, 31):
            await asyncio.sleep(3)
            
            if ctx.channel.id not in self.bot.games or game.game_id != self.bot.games[ctx.channel.id].game_id: 
                old_embed = status_message.embeds[0]
                old_embed.set_image(url=discord.Embed().Empty)
                old_embed.set_footer(text="Match has ended.")
                return await status_message.edit(embed=old_embed)
                # return await status_message.embeds[0].set_image(url=None)await query_stats(self, add_image=False)url=None
            else:
                try:
                    await status_message.edit(embed=await query_stats(self, add_image=True))
                except Exception as e:
                    old_embed = status_message.embeds[0]
                    old_embed.set_image(url=discord.Embed().Empty)
                    old_embed.set_footer(text="Match has ended.")
                    return await status_message.edit(embed=old_embed)

        await asyncio.sleep(3)
        old_embed = status_message.embeds[0]
        old_embed.set_image(url=discord.Embed().Empty)
        # old_embed.set_footer(text="Match has ended.")
        game.is_updating = False
        return await status_message.edit(embed=old_embed)
        # return await status_message.embeds[0].set_image(url=None)=await query_stats(self, add_image=False)

    @commands.command(
        brief = "Changes team's name.",
        usage = ['h! changeteamname | <Team name> <Team\'s new name>', ['h!changeteamname Teama Champions']],
        aliases = ['editteamname','teamname'],
        description = "".join(strings['changeteamname_desc'])
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def changeteamname(self, ctx, team, *, name):
        game = self.bot.games[ctx.channel.id]

        if len(name) > 20:
            return await ctx.send(":x: Name should be shorter than 20 characters.")

        if team.lower().replace("_","").replace(" ","") in (game.team_settings['Team A name'].lower().replace(" ",""), "teama"):
            game.team_settings['Team A name'] = name

        elif team.lower().replace("_","").replace(" ","") in (game.team_settings['Team B name'].lower().replace(" ",""), "teamb"):
            game.team_settings['Team B name'] = name

        else:
            return await ctx.send(":x: Team name is not valid!")

        return await ctx.send(f"Changed {team.upper()}'s name to {name}")

def setup(bot):
    bot.add_cog(Multiplayer(bot))