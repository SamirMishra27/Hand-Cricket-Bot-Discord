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
        self.ACTION_TIMEOUT = 20
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
        except discord.Forbidden: return

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        # print("Received a message!")
        if message.channel.type != discord.ChannelType.private:
            return
        if message.content not in ("0","1","2","3","4","5","6"):
            return

        for game in self.bot.games.values():
            if game.type != GameType.RUNRACE:
                continue
            if message.author in game.players:
                game = game
        if game.type != GameType.RUNRACE:
            return
        if game.game_started == False:
            return

        player = game.player_stats[message.author.id]
        if player['is_out'] == True:
            return

        player['last_action'] = int(message.content)
        bot_action = crypto.randint(0,6) 
                 
        if player['last_action'] != bot_action:
            player['runs'] += player['last_action']
            player['balls'] += 1

            await game.send_message(
                player['player'].id, "Bot's last action -> {}\n".format(bot_action) + \
                "Your score: {runs} ({balls})\n".format(**player) + \
                "Your position in the leaderboad is **#{}**!".format(game.get_position(player['player'].id))
            )

        elif player['last_action'] == bot_action:
            player['balls'] += 1
            player['is_out'] = True

            await game.send_message(
                player['player'].id, "You are out! \nBot's last action -> {}\n".format(bot_action) + \
                "**Your final score: {runs} ({balls})**\n".format(**player) + \
                "Your position in the leaderboad is **#{}**!".format(game.get_position(player['player'].id))
            )
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
                    value=f"Scored: **{player[1]['runs']} ({player[1]['balls']})** {'(OUT!)' if player[1]['is_out'] == True else ''}",
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
                    # bot_action = crypto.randint(0,6)
                    actions = [0,1,2,3,4,5,6]
                    actions.remove(player['last_action'])
                    actions.append(player['last_action'])
                    bot_action = random.choices(actions, [14.78,14.78,14.78,14.78,14.78,14.78,11.28],k=1)[0]
                    if player['last_action'] != bot_action:
                        player['runs'] += player['last_action']
                        player['balls'] += 1
                    elif player['last_action'] == bot_action:
                        player['balls'] += 1
                        player['is_out'] = True    

            if (time() - game.started_at) > 60*5:
                to_end = True
            if to_end == True: 
                winner = ""
                await status_message.edit(embed=await update_stats(self, add_image=False, footer=True))
                for player in sorted(game.player_stats.items(), key=lambda x: (x[1]['runs'], x[1]['balls']), reverse=True):
                    winner = player[1]['player']
                    break
                await ctx.send(f"The match is over! {winner.mention} wins the race! :confetti_ball:")
                self.bot.games.pop(ctx.channel.id)
                self.bot.get_cog("GlobalEvents").insert_data_in_events(game)
                await log_game(ctx, type=GameType.RUNRACE)
                return

            await asyncio.sleep(3.5)
            continue


def setup(bot):        
    bot.add_cog(RunRace(bot))