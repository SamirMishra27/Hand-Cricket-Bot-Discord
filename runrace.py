from game import RunRaceGame
from discord.ext import commands
from utils import *
from time import time

import discord
import crypto
import asyncio

class RunRace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ACTION_TIMEOUT = 15
        self.cog_brief = "Run Race commands."
        self.cog_description = "This category includes commands needed to play the Run Race gamemode."

    @commands.command(
        aliases = ['rr', 'create_runrace'],
        brief = "Creates a Run Race game.",
        usage = ["h! runrace | create_runrace", None]
    )
    @commands.guild_only()
    async def runrace(self, ctx):

        to_decline = check_for_other_games(ctx.bot, ctx.author)
        if to_decline == True:
            return await ctx.send("You are already playing another Hand Cricket match in a different server or a channel.")
        
        if ctx.channel.id in self.bot.games: return await ctx.send("A game is already running here.")

        new_game = RunRaceGame.create(ctx, self.bot)
        self.bot.games[ctx.channel.id] = new_game

        wait_msg = await ctx.send(
            f"A game of Hand Cricket Run Race has been created by **{ctx.author.name}, **"
            f"use {self.bot.prefix}join to join this match!")
        await wait_msg.add_reaction(misc_emojis['rtj'])
        await asyncio.sleep(60)
        try:
            return await wait_msg.clear_reaction(misc_emojis['rtj'])
        except Exception as e: return

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        
        if message.channel.type != discord.ChannelType.private:
            return
        if message.content not in ("0","1","2","3","4","5","6"):
            return

        for game in self.bot.games.values():
            if game.type == GameType.RUNRACE and message.author in game.players:
                game = game
                break
        else:    
            return
        if game.type != GameType.RUNRACE:
            return
        if game.game_started == False:
            return

        player = game.player_stats[message.author.id]
        if player['is_out'] == True:
            return

        player['last_action'] = int(message.content)
        player['l3as'].append(player['last_action'])

        if player['l3as'][0] == player['l3as'][1] == player['l3as'][2]:
            bot_action = player['last_action']
        else:
            bot_action = crypto.randint(0,6) 
                 
        if player['last_action'] != bot_action:
            _last_score = player['runs']
            player['runs'] += player['last_action']
            player['balls'] += 1
            player['timeline'].append(player['last_action'])

            await game.send_message(
                player['player'].id, "Bot's last action -> {}\n".format(bot_action) + \
                "`Your score: {runs}/{wickets} ({balls})\n`".format(**player) + \
                "Your position in the leaderboad is **#{}**!".format(game.get_position(player['player'].id))
            )
            await check_for_milestone(
                player['player'].name, player['player'], _last_score, player['runs'], self.bot
            )

        elif player['last_action'] == bot_action:

            if player['runs'] - player['_prev_wicket_score'] >= player['highest_score']:
                player['highest_score'] = player['runs'] - player['_prev_wicket_score']
                player['_prev_wicket_score'] = player['runs']
            if player['runs'] == 0:
                player['duck'] == True
                
            player['balls'] += 1
            player['wickets'] += 1
            player['timeline'].append("W")

            out_msg = "You are {} \nBot's last action -> {}\n".format('out!' if player['runs'] != 0 else 'DUCK out! :joy: :duck:' ,bot_action)
                            
            if player['wickets'] == game.wickets:
                player['is_out'] = True
                out_msg += ("**Your final score: {runs}/{wickets} ({balls})**\n".format(**player) + \
                            "\n{}  ".format(game.channel.mention))

            else:
                wicks_left = game.wickets - player['wickets']
                out_msg += "You have `{} wicket{}` left!\n".format(wicks_left, pz(wicks_left))
                
            await game.send_message(
                player['player'].id, out_msg + \
                "Your position in the leaderboad is **#{}**!".format(game.get_position(player['player'].id)) 
            )
            await check_for_hattrick('Bot', player['timeline'], player['player'], player['wickets'], False, self.bot)
        return

    async def _start_run_race_game(self, ctx):
        game = self.bot.games[ctx.channel.id]
        await game.initialise()
        await ctx.send("Run Race has started! Everyone hop into my DMs and start sending actions.")
        to_end = False

        async def update_stats(self, add_image=True, footer=False):
            embed = discord.Embed(title=f"{ctx.guild.name} Run Race.")
            embed.colour = MAYABLUE
            position = 1

            for player in sorted(game.player_stats.items(), key=lambda x: (x[1]['runs'], x[1]['balls']), reverse=True):
                embed.add_field(
                    name=f"#{position} - **{player[1]['player'].name}**",
                    value=f"Scored: **{player[1]['runs']}/{player[1]['wickets']} ({player[1]['balls']})** {'(OUT!)' if player[1]['is_out'] == True else ''}",
                    inline=False
                )
                position += 1
            if add_image == True:
                embed.set_image(url=live_gif)
            if footer == True:
                embed.set_footer(text=" The match is over! ")
            return embed   

        status_message = await ctx.send(embed=await update_stats(self, add_image=True, footer=False))
        while True:
            for player in game.player_stats.values():
                if player['is_out'] == True:
                    continue
                else:
                    await status_message.edit(embed=await update_stats(self, add_image=True, footer=False))
                    to_end = False
                    break

            else:
                to_end = True

            for player in game.player_stats.values():

                if player['is_human'] == False:
                    if player['is_out'] == True:
                        continue

                    player['last_action'] = crypto.randint(0,6)
                    bot_action = crypto.randint(0,6)
                    if player['last_action'] != bot_action:
                        player['runs'] += player['last_action']
                        player['balls'] += 1

                    elif player['last_action'] == bot_action:
                        player['balls'] += 1
                        player['wickets'] += 1
                        if player['wickets'] == game.wickets:
                            player['is_out'] = True    

            if (time() - game.started_at) > 600:
                to_end = True
            if to_end == True: 
                winner = ""
                await status_message.edit(embed=await update_stats(self, add_image=False, footer=True))
                for player in sorted(game.player_stats.items(), key=lambda x: (x[1]['runs'], x[1]['balls']), reverse=True):
                    winner = player[1]['player']
                    break
                await ctx.send(f"The match is over! {winner.mention} wins the race! :confetti_ball:")
                self.bot.get_cog("GlobalEvents").insert_data_in_events(game)
                await log_game(ctx, type=GameType.RUNRACE)
                self.bot.games.pop(ctx.channel.id)
                game.check_endgame() 
                match_info = await game.retreive_match_data()
                await self.bot.get_cog("Social").insert_match_data(match_info)
                return

            await asyncio.sleep(3.5)
            continue

    @commands.command(
        aliases = ['sw', 'wicket', 'wickets'],
        brief = "Sets wickets for each player in the match.",
        description = "",
        usage = ['h! setwickets | wicket | sw  <Number>']
    )        
    @before_game_only()
    @host_only()
    @runrace_mode_only()
    @game_only()
    async def setwickets(self, ctx, wickets: int):
        if wickets not in range(1,6):
            return await ctx.send(":x: Choose a number between 1 - 5")

        game = self.bot.games[ctx.channel.id]
        game.wickets = int(wickets)
        return await ctx.send(f"Wickets has been set to **{wickets}** :white_check_mark:")

def setup(bot):        
    bot.add_cog(RunRace(bot))