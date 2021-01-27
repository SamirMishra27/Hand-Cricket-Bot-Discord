from discord.ext import commands
from discord import Forbidden, Embed
import discord
import sqlite3

from itertools import islice
from contextlib import redirect_stdout
from io import StringIO
from textwrap import indent
from traceback import format_exception, print_exc
import subprocess

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
                return await ctx.send("Success!")
            except Exception as e: 
                print(e); 
                return await ctx.send("Error!")

        try: 
            self.bot.reload_extension(str(arg)); 
            return await ctx.send("Success!")
        except Exception as e: 
            print(e); 
            return await ctx.send("Error!")

    @commands.command(aliases=['l'], hidden=True)
    async def load(self, ctx, arg):
        try: 
            self.bot.load_extension(str(arg)); 
            return await ctx.send("Success!")
        except Exception as e: 
            print(e); 
            return await ctx.send("Error!")

    @commands.command(aliases=['u'], hidden=True)
    async def unload(self, ctx, arg):
        try: 
            self.bot.unload_extension(str(arg)); 
            return await ctx.send("Success!")
        except Exception as e: 
            print(e); 
            return await ctx.send("Error!")

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
            'disocrd': discord,
            'bot': self.bot,
            'author': ctx.author
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
        except Exception as e:
            result = "```python\n"
            result += "".join(format_exception(e, e, e.__traceback__)) + "```"
            result = result.replace(r"c:...Path...\ownercog.py", "YOU MUST NOT SEE THIS PATH KEK")

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


def setup(bot):
    bot.add_cog(Owner(bot))
