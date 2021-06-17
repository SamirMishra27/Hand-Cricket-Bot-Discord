from discord.ext import commands
from discord import Embed, Member, ButtonStyle
from discord.ui import Button, Item, View, button

from os import getpid
from datetime import datetime
from random import choice
from utils import MAYABLUE, SPRINGGREEN, send_message, strings
from helpcommand import CustomView

import psutil
import sqlite3
import asyncio

proc = psutil.Process(getpid())
proc.cpu_percent(interval=None)

class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog_brief = 'Other commands.'
        self.cog_description = "Lists other non game related commands."
        with open('news.txt') as f:
            self.news_content = f.read()
        self.news_end_footer = "Bot made and maintained by SAMIR."
        self.stats_end_footer = None
    
    @commands.command(brief = 'Checks latency.', usage = ['h! ping', None], description="".join(strings['ping_desc']))
    async def ping(self, ctx):
        
        resp = await ctx.send("Pinging...")
        diff = resp.created_at - ctx.message.created_at
        return await resp.edit(content=f"Pong! latency -> {int(self.bot.latency * 1000)}ms! Roundtrip -> {1000*diff.total_seconds()}ms!")
    
    @commands.command(brief = 'Stats about the bot.', usage = ['h! stats', None], description="".join(strings['stats_desc']))
    @commands.cooldown(1, 5.0, commands.BucketType.channel)
    async def stats(self, ctx):
        
        ram = round(proc.memory_info().rss/1e6, 2)
        ram_percent = round(proc.memory_percent(), 2)
        cpu_usage = round(proc.cpu_percent(interval=None), 2)
        diff = datetime.now() - self.bot.launched_at

        total_matches = await self.bot.db.execute_fetchall("SELECT COUNT(all) FROM matches;")
        if ctx.guild is not None:
            server_matches = await self.bot.db.execute("SELECT COUNT(all) FROM matches WHERE guild_id == (?);", (ctx.guild.id,))
            server_matches = await server_matches.fetchone()

        embed = Embed(title="Statistics:")
        embed.colour = MAYABLUE
        embed.add_field(
            name = "Bot stats:",
            value = '\n'.join(["Guilds: {}".format(len(ctx.bot.guilds)),
            'Bot version: v{}'.format(ctx.bot.version),
            '[Top.gg]({}) votes: {}'.format(ctx.bot.topgg, self.bot.get_cog('EventLoops').topggvotes) ]),
            inline = True
        )
        uptime = round(diff.seconds/60)
        embed.add_field(
            name = "Server system stats:",
            value = '\n'.join(["**RAM**: {}MB  ({})%".format(ram, ram_percent),
            "**CPU**: {}%".format(cpu_usage),
            "**Uptime**: {} days {} hours {} mins.".format(int(diff.days), int(uptime/60), int(uptime%60))]) #uptime/1440
        )
        if ctx.guild is not None:
            msg = f"Matches played in {ctx.guild.name}: **{server_matches[0]}**"
        else: msg = ''
        embed.add_field(
            name = "Match stats:",
            value = f"Matches played: **{total_matches[0][0]}**\n"
                    f"{msg}",
            inline = False
        )
        embed.set_footer(text=self.stats_end_footer if self.stats_end_footer is not None else f'Requested by {ctx.author.name}')
        await ctx.send(embed=embed)

    @commands.command(
        aliases=['new'], 
        brief = 'Most recent news about the bot.', 
        usage = ['h! news', None],
        description = "".join(strings['news_desc']))
    @commands.cooldown(1, 5.0, commands.BucketType.channel)
    async def news(self, ctx):
        
        embed = Embed()
        embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url or ctx.bot.user.avatar)
        embed.set_footer(text="For more help use .help command.")
        embed.description = self.news_content
        embed.set_footer(text=self.news_end_footer)
        embed.colour = SPRINGGREEN
        await ctx.send(embed=embed)

    @commands.command(brief = 'Invite link of bot.', usage = ['h! invite', None], description = "".join(strings['invite_desc']))
    @commands.cooldown(1, 5.0, commands.BucketType.channel)
    async def invite(self, ctx):
        
        return await ctx.send(embed=Embed(
            description='Here\'s my [Invite Link!]({}) \n[Support Server Link!](https://discord.gg/Mb9s5sVkSz)'.format(
                ctx.bot.send_invite_link, ctx.bot.send_support_server), colour=SPRINGGREEN))

    @commands.command(
        aliases = ['changeprefix'],
        brief = 'Show the server\'s prefix or change it.',
        usage = ['h! prefix | changeprefix <optional: new prefix>', None],
        description = "".join(strings['prefix_desc']))
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10.0, commands.BucketType.channel)
    async def prefix(self, ctx, new_prefix=None):
        
        if new_prefix is None:
            if ctx.guild is None:
                return await ctx.send(f'My default prefix is `{self.bot.prefix}`')
            return await ctx.send(
                f'My prefix in this server is `{ctx.guild_prefix}`\n'
                f'My default prefix is `{self.bot.prefix}`')

        if len(str(new_prefix)) > 5:
            return await ctx.send(":x: Maximum prefix length must be 5.")

        try:
            await self.bot.db.execute("UPDATE prefixes set prefix = (?) WHERE guild_id == (?);", (ctx.guild.id, str(new_prefix)))
        except Exception as e: 
            print(e)

            await self.bot.db.execute_insert("INSERT INTO prefixes(guild_id, prefix) VALUES (?,?);", (ctx.guild.id, str(new_prefix)))
            await self.bot.db.commit() 
        
        self.bot.guild_settings_cache[ctx.guild.id]['prefix'] = str(new_prefix)
        return await ctx.send(f"Prefix is now: `{new_prefix}`")


    @commands.command(brief = 'Instructions on how to play the game.', aliases=['rules'], usage=['h! howtoplay', None], description="""No description available.""")
    @commands.cooldown(1, 30.0, commands.BucketType.channel)
    async def howtoplay(self, ctx):
        
        with open("howtoplay.txt") as f:
            lines = f.readlines()
            pages = [''.join(lines[0:18]), ''.join(lines[19:23]), ''.join(lines[24:28]), ''.join(lines[29:38]), ''.join(lines[39:47])]

        await ctx.send(
            embed=Embed(description=pages[0], colour=SPRINGGREEN),
            view= CustomView(pages=pages, user=ctx.author, timeout=60)
        )

    @commands.command(
        aliases=['tease'], 
        brief='Sledge another player!', 
        usage=['h! sledge | tease <user tag>', ['h!sledge @SAMIR']],
        description="".join(strings['sledge_desc'])
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    async def sledge(self, ctx, user: Member):

        if user.id == ctx.author.id: return await ctx.send("Don't sledge yourself, that's just too much!")

        elif user.id == ctx.bot.user.id: return await ctx.send(
            "Wow listen, you are so bad at this game that you cannot tease anyone and so you decided to "
            "Sledge me? Pitiful! :rofl:"
        )
        return await ctx.send(f"**{user.name}**, {choice(strings['sledges'])}")

    @commands.command(
        brief = 'Gives you vote links.',
        usage = ['h! vote', None],
        description = 'No description available.'
    )
    @commands.cooldown(1, per=5.0, type=commands.BucketType.channel)
    async def vote(self, ctx):
        return await ctx.send(
            embed = Embed(description = "[Top.gg]({})\n[BotsForDiscord]({})".format(self.bot.topgg, self.bot.bfd),
            color=MAYABLUE).set_author(name=self.bot.user.name, icon_url=str(self.bot.user.avatar_url or self.bot.user.avatar))
        )

def setup(bot):
    bot.add_cog(Miscellaneous(bot))