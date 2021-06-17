import discord
from discord.ext import commands
from utils import *
from typing import Optional

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog_brief = "Commands that work in several gamemodes."
        self.cog_description = ""

    
    @commands.command(
        aliases = ['j', 'in'],
        brief = 'Join the current multiplayer/run race game.',
        usage = ['h! join | j | in', ['h!join']],
        description = "".join(strings['join_desc'])
    )
    @before_game_only()
    @multiplayer_game_only()
    @game_only()
    async def join(self, ctx):
        
        game = self.bot.games[ctx.channel.id]

        if ctx.author in game.players:
            return await ctx.send("You have already joined the match.")
        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or channel.")

        if game.type == GameType.MULTI and len(game.players) >= 20: return await ctx.send("Sorry, maximum 20 players can join the match.")
        elif game.type == GameType.RUNRACE and len(game.players) >= 10: return await ctx.send("Sorry, maximum 10 players can join the match.")

        if game.game_started == True: return await ctx.send("Match has already started.")

        if game.type == GameType.MULTI:
            if game.shuffled == True:
                if len(game.TeamA) < len(game.TeamB):
                    game.TeamA.append(ctx.author)
                else:
                    game.TeamB.append(ctx.author)
        
        game.players.append(ctx.author)
        return await ctx.send("Successfully joined the match. :white_check_mark:")

    @commands.command(
        aliases = ['le'],
        brief = 'Leaves the current multiplayer/run race game.',
        usage = ['h! leave | le', None],
        description = "".join(strings['leave_desc'])
    )
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @participants_only()
    @game_only()
    async def leave(self, ctx):
        
        game = self.bot.games[ctx.channel.id]
        
        if game.type == GameType.MULTI or game.type == GameType.RUNRACE:
            if ctx.author.id == game.host:
                return await ctx.send("You are a host. change the host to someone else before leaving.")

            if game.game_started in (False, 'pregame'):
                game.players.remove(ctx.author)
                if game.type == GameType.MULTI:
                    if ctx.author in game.TeamA: game.TeamA.remove(ctx.author)
                    elif ctx.author in game.TeamB: game.TeamB.remove(ctx.author)
                    else: pass
                return await ctx.send("You have left the game.")

            elif game.game_started == True:
                if game.type == GameType.RUNRACE:
                    return await ctx.send("Leave the game as it's and don't respond, the game will auto end after sometime.")

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
            if ctx.author != game.player:
                return
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
            if ctx.author not in game.players:
                return
            await ctx.send("Are you sure you want to leave this match?")
            def check(message):
                return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ('yes','no')
            message = await self.bot.wait_for('message', timeout=20, check=check)

            if message.content.lower() == 'yes':
                opponent = game.players[0] if game.players[1] == ctx.author else game.players[1]

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
        aliases = ['pl', 'plist', 'players'],
        brief = 'Shows the full list of players Team wise.',
        usage = ['h! playerlist | pl | plist | players', None],
        description = "".join(strings['playerlist_desc'])
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @participants_only()
    @multiplayer_game_only()
    @game_only()
    async def playerlist(self, ctx):
        
        game = self.bot.games[ctx.channel.id]; 
        if game.type == GameType.MULTI:
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

                embed.add_field(name=f"{game.team_settings['Team A name']}:", value=A, inline=False)
                embed.add_field(name=f"{game.team_settings['Team B name']}:", value=B, inline=False)
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

                embed.add_field(name=f"{game.team_settings['Team A name']}:", value=A, inline=False)
                embed.add_field(name=f"{game.team_settings['Team B name']}:", value=B, inline=False)
                return await ctx.send(embed=embed)

        elif game.type == GameType.RUNRACE:
            if game.game_started == True:
                return await ctx.send("Playerlist is not available after Run Race has started.")
            else:
                pl_list = "```"
                for num, player in enumerate( game.players, start=1):
                    pl_list += f"{num}. {player.name}\n"
            embed = discord.Embed(title="Playerlist")
            embed.set_thumbnail(url=str(ctx.guild.icon_url))
            embed.color = 0x73C2FB
            embed.description = pl_list + "```"
            return await ctx.send(embed=embed)
    
    @commands.command(
        aliases = ['ch', 'host', 'newhost'],
        brief = 'Changes the game host.',
        usage = ['h! changehost | ch | host | newhost <player tag>', ['h!changehost @SAMIR', 'h!newhost @SAMIR']],
        description = "".join(strings['changehost_desc'])
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @participants_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def changehost(self, ctx, arg: discord.Member):
        
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
        usage = ['h! addbot <optional: number>', ['h!addbot 2', 'h!addbot 5', 'h!addbot', 'h!addbot Josh, Ankit', 'h!addbot King Kohli, Best Umpire, Akash, AB']],
        description = "".join(strings['addbot_desc'])
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    @participants_only()
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def addbot(self, ctx, *, args: str = '1'):
        
        game = self.bot.games[ctx.channel.id]

        if game.type == GameType.MULTI and len(game.players) == 20: return await ctx.send("Can't add more than 20 players, Only 10 players on each side.")
        elif game.type == GameType.RUNRACE and len(game.players) == 10: return await ctx.send("Can't add more than 10 players, Only 10 players can be added.")

        if not args.isnumeric():
            args = args.split(",")
            
            added_arg = 0
            for name in args:
                game.bot_count += 1
                count = game.bot_count
                BOT = FBot(count=count)

                BOT.name = str(name.lstrip()[0:18])
                if len(BOT.name) == 0:
                    BOT.name = f'Bot' + f'{str(count)}'
                game.players.append(BOT)
                if game.type == GameType.MULTI:
                    if game.shuffled == True:
                        if len(game.TeamA) < len(game.TeamB):
                            game.TeamA.append(BOT)
                        else:
                            game.TeamB.append(BOT)
                added_arg += 1
                if game.type == GameType.MULTI and len(game.players) >= 20 : break
                elif game.type == GameType.RUNRACE and len(game.players) >= 10 : break
        
        else:
            try:
                args_limit = int(args)
            except Exception as e:
                raise commands.BadArgument()
            added_arg = 0
            for i in range(0, args_limit):
                
                game.bot_count += 1
                count = game.bot_count
                BOT = FBot(count=count)

                game.players.append(BOT)
                if game.type == GameType.MULTI:
                    if game.shuffled == True:
                        if len(game.TeamA) < len(game.TeamB):
                            game.TeamA.append(BOT)
                        else:
                            game.TeamB.append(BOT)
                added_arg += 1
                if game.type == GameType.MULTI and len(game.players) == 20 : break
                elif game.type == GameType.RUNRACE and len(game.players) == 10 : break
        return await ctx.send(f"Successfully added {added_arg} bot{pz(added_arg)}. :white_check_mark:")

    @commands.command(
        brief = 'Removes a dummy player.',
        usage = ['h! removebot <optional: bot\'s name>', None])
    @participants_only()
    @before_game_only()
    @host_only()    
    @multiplayer_game_only()
    @game_only()
    async def removebot(self, ctx, *, args: str = None):
        
        game = self.bot.games[ctx.channel.id]

        if game.bot_count == 0: return await ctx.send("No bots to remove.")
        
        _player = None
        if args != None:
            for player in game.players:
                if not len(str(player.id)) < 4:
                    continue
                if player.name == args:
                    _player = player
                    break
            else:
                return await ctx.send(":x: No such player found!")
        else:
            for player in game.players:
                if len(str(player.id)) < 4 and player.id -100 == game.bot_count:
                    _player = player
        game.players.remove(_player)
        if game.type == GameType.MULTI:
            if _player in game.TeamA: game.TeamA.remove(_player)
            elif _player in game.TeamB: game.TeamB.remove(_player)
            else: pass

        game.bot_count -= 1
        return await ctx.send(f"Removed {_player.name}")

    @commands.command(
        aliases = ['kick'],
        brief = 'Removes a player from the game.',
        usage = ['h! remove | kick <player tag>', ['h!kick @SAMIR', 'h!remove @SAMIR']],
        description = "".join(strings['remove_desc'])
    )
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @participants_only()
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def remove(self, ctx, arg: discord.Member):
        
        game = self.bot.games[ctx.channel.id]
        if arg not in game.players: return await ctx.send("Player has not joined the game.")

        if arg == ctx.author:
            return await ctx.send(f"Can't remove yourself as a host.")

        else:
            game.players.remove(arg)
            if game.type == GameType.MULTI:
                if arg in game.TeamA: game.TeamA.remove(arg)
                elif arg in game.TeamB: game.TeamB.remove(arg)
                else: pass
            return await ctx.send(f"Removed **{arg.name}**")

    @commands.command(
        brief = 'Starts a multiplayer or run race match.',
        usage = ['h! start', None],
        description = "".join(strings['start_desc'])
    )
    @before_game_only()
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def start(self, ctx):
        game = self.bot.games[ctx.channel.id]

        if game.type == GameType.MULTI:
            
            if game.overs == None: 
                return await ctx.send(f"Set overs first.")
            if game.TeamA_turn == None: 
                return await ctx.send(f"You have not done the toss. use {self.bot.prefix}toss to do decide who will bat first.")
            if len(game.players) <4: 
                return await ctx.send(f"At least 4 players are required to start the game. If no one joins, try using the addbot command.")
            if len(game.TeamA) != len(game.TeamB): 
                return await ctx.send("There is an unequal amount of players on both sides. try adding a bot if no one joins.")
            if game.shuffled == False:
                return await ctx.send("You have not shuffuled the players yet. use command shuffle to shuffle the players first.")

            return await self.bot.get_cog('Multiplayer')._start_multiplayer_match(ctx)

        elif game.type == GameType.RUNRACE:

            if len(game.players) < 3:
                return await ctx.send("At least 3 players are required to start the game. If no one joins, try using the addbot command.")
            return await self.bot.get_cog('RunRace')._start_run_race_game(ctx)

    @commands.command(
        aliases = ['del', 'yeet', 'forfeit', 'end'],
        brief = 'Deletes the current multiplayer game.',
        usage = ['h! delete | del | yeet | forfeit | end', None]
    )
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @host_only()
    @multiplayer_game_only()
    @game_only()
    async def delete(self, ctx):
        
        if ctx.channel.id not in self.bot.games: return await ctx.send("Nothing to delete.")
        game = self.bot.games[ctx.channel.id]

        await ctx.send("Dude are you sure you want to delete this match? (yes/no)")

        def check(message): return message.channel.id == ctx.channel.id and message.author.id == ctx.author.id and message.content.lower() in ('yes','no') 
        try: message = await self.bot.wait_for('message', timeout=25, check=check)
        except asyncio.TimeoutError: return

        if message.content.lower() == 'yes':
            self.bot.games.pop(ctx.channel.id)
            return await ctx.send("Match has been abandoned.")
        else: return


def setup(bot):
    bot.add_cog(General(bot))