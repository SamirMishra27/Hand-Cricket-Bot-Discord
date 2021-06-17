import discord
from discord.ext import commands
from discord.ext import tasks

import json
from datetime import datetime
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from utils import *
from os import remove
from time import sleep
from traceback import format_exception

class GlobalEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog_brief = "Events related commands."
        self.cog_description = ""

        self.event_display_name = "First Summer Event!"
        self.event_name = "testeventapril2021"
        self.event_data = {"413000": {'runs':0, 'balls':0, 'wickets':0}}
        self.event_start_date = datetime(2021, 4, 23, 00, 35, 0, 0)
        self.event_end_date = datetime(2021, 5, 5, 23, 40, 0, 0)
        self.event_target = 25000

        self.event_has_started = False
        self.event_status = ""
        self.event_has_ended = False
        self.ongoing_events = False #True

        self.update_event_status.start()
        sleep(0.4)
        self.bot.loop.create_task(self.on_cog_load())
        sleep(0.4)
        self.update_event_data.start()

    async def on_cog_load(self):
        if self.ongoing_events != True:
            return
        if self.event_name == None:
            return

        event_data = await self.bot.db.execute_fetchall("SELECT * FROM events WHERE event_name == (?);", (self.event_name,))
        self.event_data = json.loads(event_data[0][1])
        return

    def cog_unload(self):

        self.update_event_status.cancel()
        self.update_event_data.cancel()

    @tasks.loop(minutes=30.0)
    async def update_event_data(self):
        if self.ongoing_events != True:
            return
        if self.event_name == None:
            return
        if len(self.event_data) == 0:
            return

        data = json.dumps(self.event_data)
        await self.bot.db.execute("UPDATE events SET event_data = (?) WHERE event_name == (?);", (data, self.event_name))
        await self.bot.db.commit()
        
    @update_event_data.before_loop
    async def before_update_event_data(self):
        await self.bot.wait_until_ready()

    @update_event_data.after_loop
    async def after_update_event_data(self):
        if self.update_event_data.is_being_cancelled():
            if self.ongoing_events != True:
                return
            if self.event_name == None:
                return
            if len(self.event_data) == 0:
                return
            data = json.dumps(self.event_data)
            await self.bot.db.execute("UPDATE events SET event_data = (?) WHERE event_name == (?);", (data, self.event_name))
            await self.bot.db.commit()
            print("We got here lmao.")
        else:
            self.update_event_data.restart()

    @tasks.loop(minutes=30.0)
    async def update_event_status(self):
        date = datetime.now()
        if date > self.event_start_date and date < self.event_end_date:
            self.event_has_started = True
            self.event_has_ended = False

        elif date > self.event_end_date:
            self.event_has_ended = True
            self.event_has_started = False

        if self.event_has_started == False and self.event_has_ended == False:
            starting_in = self.event_start_date - datetime.now()
            time = round(starting_in.seconds/60)
            self.event_status = f"Starting in {int(starting_in.days)} days {int(time/60)} hrs {int(time%60)} mins"

        elif self.event_has_started == True and self.event_has_ended == False:
            ending_in = self.event_end_date - datetime.now()
            time = round(ending_in.seconds/60)
            self.event_status = f"Ending in {int(ending_in.days)} days {int(time/60)} hrs {int(time%60)} mins"

        elif self.event_has_started == False and self.event_has_ended == True:
            # self.event_name += "--ended"
            self.event_status = f"Event has ended!"

    @update_event_status.before_loop
    async def before_update_event_status(self):
        await self.bot.wait_until_ready()

    @update_event_status.after_loop
    async def after_update_event_status(self):
        self.update_event_status.restart()

    @commands.command(
        aliases = ['globalevents'],
        brief = "Shows information about global events.",
        usage = ['h! events | globalevents', None],
        description = "".join(strings['events_desc'])
    )
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def events(self, ctx):

        if self.ongoing_events == False or self.event_name == None:
            return await ctx.send(
                embed = discord.Embed(
                    title="No upcoming or ongoing events!",
                    description = "Check back later!",
                    color = discord.Color.darker_grey()
                )
            )

        elif self.ongoing_events == True:
            if self.event_has_started == False and self.event_has_ended == False:
                return await ctx.send(
                    embed = discord.Embed(
                        title= "Upcoming Events",
                        description = f"**Event**: {self.event_display_name}\n{self.event_status}",
                        color = discord.Color.darker_grey()
                    )
                )
            else:
                if ctx.guild is not None:
                    if str(ctx.channel.guild.id) not in self.event_data:
                        self.event_data[str(ctx.guild.id)] = {'runs':0, 'balls':0, 'wickets':0}

                with Image.open("assets/Untitled3_20210416014831.png") as im:
                    sc = im.copy()
                    font_size = 38
                    font = ImageFont.truetype("assets/CoreSansD65Heavy.otf", font_size)

                im2 = Image.new("RGBA", (853,1280), color=(255,255,255))
                sc2 = im2.copy()
                sc1draw = ImageDraw.Draw(sc)
                sc2draw = ImageDraw.Draw(sc2)

                if ctx.guild is not None:
                    guild_score = self.event_data[str(ctx.channel.guild.id)]['runs']

                    position = 1
                    for guild in sorted(self.event_data.items(), key=lambda x: (x[1]['runs'], x[1]['balls']), reverse=True):
                        if int(guild[0]) == ctx.guild.id:
                            break
                        else:
                            position += 1
                    
                    total = 0
                    for guild in self.event_data.values():
                        total += guild['runs']
                    progress = (total / self.event_target) * 100
                    
                    arc = 820 * (progress/100)

                    sc2draw.line(xy=(10,1110,arc,1110), fill=(255,69,0), width=216)

                    sc1draw.multiline_text(xy=(75, 460), text=f"Reach {self.event_target} runs before the end of event.", fill=(255,255,255), font=font)

                    sc1draw.multiline_text(xy=(40, 860), text=f"Your server's score: {guild_score}", fill=(255,255,255), font=font)
                    
                    sc1draw.multiline_text(xy=(40, 910), text=f"Your server's rank: #{position}", fill=(255,255,255), font=font)

                    sc1draw.multiline_text(xy=(600, 865), text=f"Total runs: \n{total} / {self.event_target}", fill=(255,255,255), font=font)
                
                elif ctx.guild is None:
                    total = 0
                    for guild in self.event_data.values():
                        total += guild['runs']
                    progress = (total / self.event_target) * 100
                    
                    arc = 820 * (progress/100)

                    sc2draw.line(xy=(10,1110,arc,1110), fill=(255,69,0), width=216)

                    sc1draw.multiline_text(xy=(75, 460), text=f"Reach {self.event_target} runs before the end of event.", fill=(255,255,255), font=font)

                    sc1draw.multiline_text(xy=(320, 865), text=f"Total runs: \n{total} / {self.event_target}", fill=(255,255,255), font=font)

                mix = Image.alpha_composite(sc2, sc)
                mix.save(f"temporary/{ctx.author.id}.png")

                file = discord.File(f"temporary/{ctx.author.id}.png")
                await ctx.send(file=file, embed=discord.Embed(
                    color=MAYABLUE, title="Ongoing Event"
                ).set_image(url=f"attachment://{ctx.author.id}.png").set_footer(
                    text=self.event_status
                ))
                return remove(f'temporary/{ctx.author.id}.png')

    def insert_data_in_events(self, game):
        if self.ongoing_events != True:
            return 
        if self.event_name == None:
            return
        if self.event_has_started != True:
            return

        if game.channel.type == discord.ChannelType.private :
            self.event_data["413000"]['runs'] += game.innings1_runs + game.innings2_runs
            self.event_data["413000"]['balls'] += game.innings1_bowls + game.innings2_bowls
            self.event_data["413000"]['wickets'] += 1
            return

        if str(game.channel.guild.id) not in self.event_data:
            self.event_data[str(game.channel.guild.id)] = {'runs':0, 'balls':0, 'wickets':0}

        if game.type == GameType.SINGLE:
            self.event_data[str(game.channel.guild.id)]['runs'] += game.innings1_runs + game.innings2_runs
            self.event_data[str(game.channel.guild.id)]['balls'] += game.innings1_bowls + game.innings2_bowls
            self.event_data[str(game.channel.guild.id)]['wickets'] += 1

        elif game.type == GameType.DOUBLE:
            game.stats.pop('curr_batsman')
            game.stats.pop('curr_bowler')
            for player in game.stats.values():
                self.event_data[str(game.channel.guild.id)]['runs'] += player['runs']
                self.event_data[str(game.channel.guild.id)]['balls'] += player['balls']
                self.event_data[str(game.channel.guild.id)]['wickets'] += player['wickets']

        elif game.type == GameType.MULTI:
            self.event_data[str(game.channel.guild.id)]['runs'] += game.batting_team_stats['runs'] + game.bowling_team_stats['runs']
            self.event_data[str(game.channel.guild.id)]['balls'] += game.batting_team_stats['balls'] + game.bowling_team_stats['balls']
            self.event_data[str(game.channel.guild.id)]['wickets'] += game.batting_team_stats['wickets'] + game.bowling_team_stats['wickets']

        elif game.type == GameType.RUNRACE:
            for player in game.player_stats.values():
                self.event_data[str(game.channel.guild.id)]['runs'] += player['runs']
                self.event_data[str(game.channel.guild.id)]['balls'] += player['balls']
                self.event_data[str(game.channel.guild.id)]['wickets'] += 0 if player['is_out'] == False else 1

    @commands.command(hidden=True)
    @commands.is_owner()
    async def backup_event_data(self, ctx):
        try:
            event_data = await self.bot.db.execute_fetchall("SELECT * FROM events WHERE event_name == (?);", (self.event_name,))
            await self.bot.db.execute("UPDATE events SET event_data = (?) WHERE event_name == (?);", (event_data[0][1], f"{self.event_name}--backup"))
            await self.bot.db.commit()
            return await ctx.send("event data sucessfully backuped.")
        except Exception as e:
            return await ctx.send('```\n' + format_exception(e, e, e.__traceback__) + '\n```')

def setup(bot):
    bot.add_cog(GlobalEvents(bot))