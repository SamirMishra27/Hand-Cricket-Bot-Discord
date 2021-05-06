from discord.ext import commands
from discord import Embed
from utils import *

class CustomHelpCommand(commands.DefaultHelpCommand):

    def __init__(self):
        super().__init__(
            indent = 8,
            verify_checks=False
        )

    async def send_bot_help(self, mapping):
        bot = self.context.bot
        embed = Embed()
        embed.colour = MAYABLUE
        embed.set_thumbnail(url=str(bot.user.avatar_url))

        row_1 = ''
        if self.context.guild is not None:
            row_1 = (
                f'My prefix in this server is `{self.context.guild_prefix}`'
            )
        row_1 += (
            f'\nMy default prefix is `{bot.prefix}`'
            f'\nYou can also mention me instead.'
            )

        row_5 = (
            f'[Invite Link]({bot.send_invite_link}) to add the bot to your server!'
            f'\n[Support Server Link]({bot.send_support_server}) for more help and suggestions and feedback.'
   )
     
        for cog, commands in mapping.items():
            cog_name = getattr(cog, '__cog_name__', 'Other')
            if cog_name in ('Owner','EventLoops','Six','Help','Other'):
                continue
            
            cmd_list = ''
            if cog_name in ('Multiplayer', 'Default', 'Misc', 'RunRace','GlobalEvents','General'):
                cmd_list += f'*{cog.cog_brief}*\n'
            for command in commands:
                if command.hidden == True:
                    continue
                cmd_list += f"{bot.prefix}{command.name} - `{command.brief}`\n"  #spacing()
            embed.add_field(name=cog_name, value=cmd_list, inline=False)

        row_6 = bot.help_end_footer
        embed.set_footer(text=row_6) 
        embed.description = row_1+'\n\n'+row_5
        embed.add_field(
            name="Useful",
            value=  f"[Documentation](https://gist.github.com/SamirMishra27/d14c3edf24ccbac5e466735c7064452d) | [Donate](https://www.patreon.com/SamirMishra27) | "
                    f"[Patreon](https://www.patreon.com/SamirMishra27) | [Top.gg]({bot.topgg}) | [BotsForDiscord]({bot.bfd})",
            inline= False
        )
        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        if command.hidden:
            return

        bot = self.context.bot
        usage = self.get_command_signature(command)
        embed = Embed(title=f'command {command.name}')
        embed.set_author(name=bot.user.name,icon_url=str(bot.user.avatar_url))
        embed.description = (
            f":label: | **Usage:** \n`{command.usage[0]}`"
            f"\n\n:page_with_curl: | **Description:** \n{command.description}" #command.briefiojcommand.help
        )
        if command.usage[1] is not None:
            embed.description += f"\n\n:speech_balloon: | **Example:**\n"
            for eg in command.usage[1]:
                embed.description += f"→ *{eg}*\n"

        embed.colour = MAYABLUE
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        bot = self.context.bot
        if cog.qualified_name in ('Owner','EventLoops','Help','GlobalEvents','General'):
            return

        cmd_list = ''
        for command in cog.walk_commands():
            if command.hidden: continue
            cmd_list += f'{self.context.bot.prefix}{command.name} - {command.brief}\n'
        embed = Embed(title=cog.qualified_name)
        embed.set_author(name=bot.user.name, icon_url=str(bot.user.avatar_url))
        embed.description = (
            f"{cog.cog_description}\n\n"
            f"{cmd_list}"
        )
        embed.colour = MAYABLUE
        return await self.get_destination().send(embed=embed)

class Help(commands.Cog):

    def __init__(self, bot):
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self
        self.bot = bot
        self.cog_brief = "Help command"
        self.cog_description = "Shows this command"

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

def setup(bot):
    bot.add_cog(Help(bot))