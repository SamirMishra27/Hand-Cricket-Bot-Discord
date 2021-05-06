from discord.ext import commands
from discord import Forbidden, Embed
import discord

from traceback import format_exception, print_exc
from contextlib import redirect_stdout
from textwrap import indent
from io import StringIO

import subprocess
import asyncio
import datetime
from utils import *
import crypto
import aiosqlite
import json

from re import sub
from os import getcwd

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.save = None

    async def cog_check(self, ctx):
        if ctx.author.id == self.bot.owner_id:
            return True
        return False

    @commands.command(hidden=True)
    async def owner(self, ctx):
        return await ctx.send("Samir!")

    @commands.command(aliases=['r'], hidden=True)
    async def reload(self, ctx, arg):
        if arg.isdecimal():
            try: 
                self.bot.reload_extension(self.bot.bot_extensions[int(arg)]); 
                return await ctx.message.add_reaction('✅') #send("Success!")
            except Exception as e: 
                print(e); 
                return await ctx.message.add_reaction('❌') #send("Error!")

        try: 
            self.bot.reload_extension(str(arg)); 
            return await ctx.message.add_reaction('✅') #send("Success!")
        except Exception as e: 
            print(e); 
            return await ctx.message.add_reaction('❌') #send("Error!")

    @commands.command(aliases=['l'], hidden=True)
    async def load(self, ctx, arg):
        try: 
            self.bot.load_extension(str(arg)); 
            return await ctx.message.add_reaction('✅') #send("Success!")
        except Exception as e: 
            print(e); 
            return await ctx.message.add_reaction('❌') #send("Error!")

    @commands.command(aliases=['u'], hidden=True)
    async def unload(self, ctx, arg):
        try: 
            self.bot.unload_extension(str(arg)); 
            return await ctx.message.add_reaction('✅') #.send("Success!")
        except Exception as e: 
            print(e); 
            return await ctx.message.add_reaction('❌') #.send("Error!")

    @commands.command(aliases=['eval','e'], hidden=True)
    async def _evaluate(self, ctx, *, arg):
        def clean_code(content):
            if content.startswith("```") and content.endswith("```"):
                return "\n".join(content.split("\n")[1:])[:-3]
            else:
                return content

        code = clean_code(arg)
        local_variables = {
            'ctx': ctx,
            'game': self.bot.games.get(ctx.channel.id, None),
            'discord': discord, 
            'bot': self.bot,
            'author': ctx.author,
            'asyncio': asyncio,
            'datetime': datetime,
            'aiosqlite': aiosqlite,
            'json': json
        }
        stdout = StringIO()
        try:
            with redirect_stdout(stdout):
                exec(
                    f"async def function():\n{indent(code, '    ')}",
                    local_variables
                )
                obj = await local_variables["function"]()
                result = (f"--*Output*```python\n{stdout.getvalue()}\n---```\n" +\
                         f"--*RETURN VALUE* ```python\n{obj}```")
                result = sub(r'([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84})', 'Redacted', result)
        except Exception as e:
            result = "```python\n"
            result += "".join(format_exception(e, e, e.__traceback__)) + "```"
            result = result.replace(r"path\ownercog.py", "YOU MUST NOT SEE THIS PATH KEK")

        return await ctx.send(result)

    @commands.command(aliases=['exec','ex'], hidden=True)
    async def _execute(self, ctx, *, arg):
        try:
            sb = subprocess.Popen(args=arg, shell=True, stdout=subprocess.PIPE)
            return await ctx.send(f"```{sb.stdout.read()}```")
        except Exception as e: 
            return await ctx.send("```"+"".join(format_exception(e, e, e.__traceback__))+"```")

    @commands.command(hidden=True)
    async def test(self, ctx, ): 
        print("Hello World!", ctx.guild_prefix) 

    @commands.command(aliases=['ieval', 'ie'], hidden=True)
    async def _interactive_eval(self, ctx):
        def clean_code(content):
            if content.startswith("```") and content.endswith("```"):
                return "\n".join(content.split("\n")[1:])[:-3]
            else:
                return content
        def check(before, message):
            return message.channel == ctx.channel and message.author == ctx.author and message == ctx.message

        local_variables = {
            'ctx': ctx,
            'game': self.bot.games.get(ctx.channel.id, None),
            'discord': discord, 
            'bot': self.bot,
            'author': ctx.author,
            'asyncio': asyncio,
            'datetime': datetime
        }
        message = await ctx.send("`Started...`")
        while True:
            stdout = StringIO()
            try:
                before, arg = await self.bot.wait_for('message_edit', timeout=300, check=check)
                code = clean_code(arg.content)

            except asyncio.TimeoutError:
                return await message.edit(content="{}\n The interactive session has been ended.".format(message.content))

            try:
                with redirect_stdout(stdout):
                    exec(
                        f"async def function():\n{indent(code, '    ')}",
                        local_variables
                    )
                    obj = await local_variables["function"]()
                    result = (f"--*Output*```python\n{stdout.getvalue()}\n---```\n" +\
                            f"--*RETURN VALUE* ```python\n{obj}```")
                    result = sub(
                        r'([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84})',
                        'Redacted', result)
            except Exception as e:
                result = "```python\n"
                result += "".join(format_exception(e, e, e.__traceback__)) + "```"
                result = result.replace(r"c:\Users\User\Desktop\CLASS 12 PYTHON CBSE\HandCricketBot\ownercog.py",
                 "YOU MUST NOT SEE THIS PATH KEK")
            await message.edit(content=result)
            continue

    @commands.command(name='console')
    async def send_to_console(self, ctx, arg):
        print(arg)
        
    @commands.command(name='query')
    async def db_query(self, ctx, _type, table, arg1: int =1, arg2: int =2, to_match=None, condition=None):

        if _type not in ['count', 'rows'] or table not in ['prefixes', 'matches','events']:
            return await ctx.send("Type or Table is invalid.")

        query = "SELECT "
        if _type == 'count':
            query += 'Count(All) '

        elif _type == 'rows':
            query += '* '

        query += 'FROM ' + table.lower() + ' '

        if _type == 'rows':
            query += 'LIMIT ' + str(arg1) + ' OFFSET ' + str(arg2) + ' '

        if condition is not None:
            query += 'WHERE ' + to_match + ' == ' + condition

        query.strip("DROP drop TABLE table")

        result = await self.bot.db.execute_fetchall(query)
        return await ctx.send(f"```python\n{result}\n```")

    @commands.command()
    async def ownerplay(self, ctx, coin):
        if crypto.choice(['heads','tails']) == coin.lower():
            msg = "You won the toss! Choose bat or bowl?"
            await ctx.send(msg)

            def check(msg): return msg.author == ctx.author
            try:
                resp = await self.bot.wait_for('message', timeout=60, check=check)
            except:
                return
            user_choice = 'bat' if resp.content.lower() == 'bat' else 'bowl'
        else:
            user_choice = crypto.choice(['bat', 'bowl'])
            msg = f"You lost the toss! You're gonna {user_choice} first!"
            await ctx.send(msg)

        i1r, i1b, i2r, i2b, tg = 0,0,0,0,0
        bot_action = 0
        your_action = 0
        embed = discord.Embed(title=f"{ctx.author.name} vs Bot", colour=MAYABLUE)
        embed.add_field(name="Innings 1", value=f"Runs:\n{i1r}\nBalls:\n{i1b}",inline=False)
        embed.add_field(name="Bot's last action", value=bot_action,inline=False)
        message = await ctx.send(embed=embed)
        async with ctx.channel.typing():
            for emoji in action_emojis:
                await message.add_reaction(emoji)

        def check2(reaction, user):
            return str(reaction.emoji) in action_emojis.keys() and user.id == ctx.author.id
        await ctx.send("Game has started!")
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check2)
                your_action = action_emojis[str(reaction.emoji)]
            except:
                your_action = crypto.randint(0,6)

            bot_action = crypto.randint(0,6)
            if bot_action != your_action:
                if user_choice == 'bat':
                    i1r += your_action; i1b += 1
                else:
                    i1r += bot_action; i1b += 1

                # await message.remove_reaction(str(reaction), ctx.author)
                await message.edit(
                    embed=discord.Embed(
                        title=f"{ctx.author.name} vs Bot", colour=MAYABLUE
                    ).add_field(name="Innings 1", value=f"Runs:\n{i1r}\nBalls:\n{i1b}",inline=False
                    ).add_field(name="Bot's last action", value=bot_action,inline=False)
                )
                continue

            else:
                i1b += 1
                fp = 'You are' if user_choice == 'bat' else 'Bot is'
                tg = i1r + 1
                await ctx.send(f"{fp} out!\nTarget -> {tg}")  
                # await message.remove_reaction(str(reaction), ctx.author)
                await message.edit(
                    embed=discord.Embed(
                        title=f"{ctx.author.name} vs Bot", colour=MAYABLUE
                    ).add_field(name="Innings 1", value=f"Runs:\n{i1r}\nBalls:\n{i1b}",inline=False
                    ).add_field(name="Bot's last action", value=bot_action,inline=False)
                )
                break

        await ctx.send("Innings 2 have started!")
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check2)
                your_action = action_emojis[str(reaction.emoji)]
            except:
                your_action = crypto.randint(0,6)

            bot_action = crypto.randint(0,6)
            if bot_action != your_action:
                if user_choice == 'bat':
                    i2r += your_action; i2b += 1
                else:
                    i2r += bot_action; i2b += 1

                # await message.remove_reaction(str(reaction), ctx.author)
                await message.edit(
                    embed=discord.Embed(
                        title=f"{ctx.author.name} vs Bot", colour=MAYABLUE
                    ).add_field(name="Innings 1", value=f"Runs:\n{i1r}\nBalls:\n{i1b}\ntarget:\n{tg}",inline=False
                    ).add_field(name="Innings 2", value=f"Runs:\n{i2r}\nBalls:\n{i2b}",inline=False
                    ).add_field(name="Bot's last action", value=bot_action)
                )
                if i2r > i1r:
                    await ctx.send("Score has been chased!"); break
                continue

            else:
                i1b += 1
                fp = 'You are' if user_choice == 'bowl' else 'Bot is'
                await ctx.send(f"{fp} out!")  
                # await message.remove_reaction(str(reaction), ctx.author)
                await message.edit(
                    embed=discord.Embed(
                        title=f"{ctx.author.name} vs Bot", colour=MAYABLUE
                    ).add_field(name="Innings 1", value=f"Runs:\n{i1r}\nBalls:\n{i1b}\ntarget:\n{tg}",inline=False
                    ).add_field(name="Innings 2", value=f"Runs:\n{i2r}\nBalls:\n{i2b}",inline=False
                    ).add_field(name="Bot's last action", value=bot_action)
                )
                break
        if i1r == i2r:
            result = "Match tied!"
        elif i1r > i2r:
            if user_choice == 'bat':
                result, diff = 'won', i1r-i2r
            else:
                result, diff = 'lost', i1r-i2r
        elif i1r < i2r:
            if user_choice == 'bat':
                result, diff = 'lost', i2r-i1r
            else:    
                result, diff = 'won', i2r-i1r
        await ctx.send(f"You {result} the game by {diff} runs.")
        await message.edit(
            embed=discord.Embed(
                title=f"{ctx.author.name} vs Bot", colour=MAYABLUE
            ).add_field(name="Innings 1", value=f"Runs:\n{i1r}\nBalls:\n{i1b}\ntarget:\n{tg}",inline=False
            ).add_field(name="Innings 2", value=f"Runs:\n{i2r}\nBalls:\n{i2b}",inline=False
            ).add_field(name="Bot's last action", value=bot_action)
        )
        return await log_game(ctx, type=GameType.SINGLE)

    @commands.command(aliases=['rdb'])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def reconnect_database_backup(self, ctx):
        await self.bot.db.commit()
        await self.bot.db.close()
        await asyncio.sleep(1.9)
        self.bot.db = await aiosqlite.connect("data.db")
        await ctx.send("Output -> `None`") 
        await asyncio.sleep(1.9)
        file = discord.File("data.db")
        return await ctx.send(file=file)

def setup(bot):
    bot.add_cog(Owner(bot))