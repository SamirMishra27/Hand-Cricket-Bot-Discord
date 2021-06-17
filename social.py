from discord.ext import commands
from utils import *
from json import loads, dumps
from functools import reduce
from math import ceil

class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog_brief = "Social related commands."
        self.cog_description = ""

    async def create_user_profile(self, userid):
        
        user = self.bot.get_user(userid)

        user_profile = {
            'name': user.name,
            'description': "",
            'matches_played': 0,
            'matches_won': 0,
            'matches_lost': 0,
            'runs': 0,
            'balls': 0,
            'wickets': 0,
            'wickets_lost': 0,
            'highest_score': 0,
            'hattricks': 0,
            'ducks': 0,
            'batting_average': 0,
            'match_log': "[]",
            'status': "ACTIVE",
            'created_at': str(datetime.now()),
            'field5': None,
            'field6': None,
            'field19': None,
            'field20': None
        }
        self.bot.user_profile_cache[userid] = user_profile
        to_enter = [userid]
        to_enter.extend(user_profile.values())

        await self.bot.db.execute(
            """INSERT INTO profiles(userid, name, description, matches_played, matches_won, matches_lost, runs, balls, wickets,
            wickets_lost, highest_score, hattricks, ducks, batting_average, match_log, status, created_at, Field5, Field6, Field19, Field20) VALUES 
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", tuple(to_enter) 
        )
        await self.bot.db.commit()
        self.bot.user_profile_cache[userid]['match_log'] = []

    async def execute_update(self, profile, userid):
        await self.bot.db.execute(
            """UPDATE profiles
                SET description = (?),
                    matches_played = (?),
                    matches_won = (?),
                    matches_lost = (?),
                    runs = (?),
                    balls = (?),
                    wickets = (?),
                    wickets_lost = (?),
                    highest_score = (?),
                    hattricks = (?),
                    ducks = (?),
                    batting_average = (?),
                    match_log = (?)
                WHERE userid == (?);""", (
                    profile['description'], profile['matches_played'], profile['matches_won'], profile['matches_lost'], 
                    profile['runs'], profile['balls'], profile['wickets'], profile['wickets_lost'],
                    profile['highest_score'], profile['hattricks'], profile['ducks'], 
                    profile['batting_average'], dumps(profile['match_log']), userid,
                )
        )
        await self.bot.db.commit()

    async def update_user_data(self, userid, match_info):

        profile = self.bot.user_profile_cache[userid]
        profile['match_log'].append(match_info)

        profile['matches_played'] += 1
        if match_info[1] == "WIN":
            profile['matches_won'] += 1
        elif match_info[1] == "LOSS":
            profile['matches_lost'] += 1
        else: pass
        profile['runs'] += match_info[3]
        profile['balls'] += match_info[4]
        profile['wickets'] += match_info[7]
        profile['wickets_lost'] += match_info[8]
        if match_info[11] >= profile['highest_score']:
            profile['highest_score'] = match_info[11]
        profile['hattricks'] += 1 if match_info[9] == True else 0
        profile['ducks'] += 1 if match_info[10] == True else 0
        try:
            profile['batting_average'] = round(profile['runs'] / profile['wickets_lost'], 3)
        except Exception as e:
            profile['batting_average'] = profile['runs']

        await self.execute_update(profile, userid)
    
    async def insert_match_data(self, match_info):
        new_count = []
        update_count = []

        for userid, match_info in match_info.items():

            if userid not in self.bot.user_profile_cache:

                await self.create_user_profile(userid)
                await self.update_user_data(userid, match_info)
                new_count.append(userid)

            else:

                await self.update_user_data(userid, match_info)
                update_count.append(userid)
        self.bot.log.info(
            f"{len(new_count)} user profiles was created. {new_count}\n" +
            f"and {len(update_count)} user profiles was updated. {update_count}"
        )

    @commands.command(
        aliases = ['me'],
        brief = "Shows your HandCricket profile and various statistics.",
        usage = ['h! profile <optional: user tag>', ['h!profile ', 'h!profile @SAMIR']],
        description = "This command shows the profile including statistics of a person in this Bot."
    )
    async def profile(self, ctx, user: Member = None):
        user = ctx.author if user is None else user
        if user.bot == True : 
            user = ctx.author
        if user.id not in self.bot.user_profile_cache:
            await self.create_user_profile(user.id)
            self.bot.log.info(f'A user profile was updated. {user.id}')

        embed = Embed(title=f"{user.name}'s Profile", color=MAYABLUE)
        profile = self.bot.user_profile_cache[user.id]

        embed.add_field(name="Name", value=profile['name'], inline=False)
        keys = ('description', 'matches_played', 'matches_won', 'matches_lost', 'runs', 'balls', 'wickets',
                'wickets_lost', 'highest_score', 'hattricks', 'ducks', 'batting_average')

        for key in keys:
            embed.add_field(name=key.title().replace('_',' '), value=profile[key])
        time = str(datetime.now())
        # embed.set_thumbnail(url=str(user.avatar_url or user.avatar))
        embed.set_footer(text=f"Today at {time[11:16]} UTC")
        return await ctx.send(embed=embed)

    @commands.command(
        hidden = True,
        usage = [2,2],
        description = ""
    )
    @commands.is_owner()
    async def updatepro(self, ctx, user_id : int): 
        user = self.bot.get_user(user_id)
        profile = self.bot.user_profile_cache[user.id]
        match_log = profile['match_log']

        profile['matches_played'] = len(match_log)
        profile['matches_won'] = len( list( filter( lambda x: x[1] == "WIN", match_log) ) )
        profile['matches_lost'] = len( list ( filter( lambda x: x[1] == "LOSS", match_log) ) )

        profile['runs'] = reduce( lambda x, y: x + y[3], match_log, 0 )
        profile['balls'] = reduce( lambda x, y: x + y[4], match_log, 0 )
        profile['wickets'] = reduce( lambda x, y: x + y[7], match_log, 0 )
        profile['wickets_lost'] = reduce( lambda x, y: x + y[8], match_log, 0 )
        
        for match in match_log:
            if match[11] >= profile['highest_score']:
                profile['highest_score'] = match[11]
        profile['hattricks'] = len( list( filter( lambda x: x[9] == True, match_log) ) )
        profile['ducks'] = len( list( filter( lambda x: x[10] == True, match_log) ) )

        await self.execute_update(profile, user.id)
        await ctx.send("Done!")

    @commands.command(
        usage = [3,3],
        hidden = True
    )
    @commands.is_owner()
    async def matchlog(self, ctx, user_id : int, last_page: bool=True):
        # user = ctx.author if user is None else user user.id user: Member
        user = self.bot.get_user(user_id)
        match_log = self.bot.user_profile_cache[user.id]['match_log']

        nav = {'▶️':1, '◀️':-1}
        last_page = ceil(len(match_log)/5) - 1
        curr_page = 0 if last_page==False else last_page
            
        page = match_log[curr_page*5 : (curr_page*5)+5]
        message = await ctx.send(
            embed=Embed(description = f"Name: {user.name}\nId: {user.id}\n\n```python\n{page}```",
            color=MAYABLUE, )
        )
        try:
            await message.add_reaction('◀️')
            await message.add_reaction('▶️')
        except Exception as e:
            return await ctx.send(":x: I do not have the required permissions to run this command.")
        
        def check(react, user): return user == ctx.author and \
            react.message == message and react.message.channel == ctx.channel \
            and str(react.emoji) in ('▶️','◀️')

        while True:
            try:
                react, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
            except asyncio.TimeoutError:
                try: return await message.clear_reactions()
                except: return

            resp = (curr_page + nav[str(react.emoji)])
            if resp <= last_page and resp >= 0:
                curr_page = curr_page + nav[str(react.emoji)]
                page = match_log[curr_page*5 : (curr_page*5)+5]
                await message.edit(
                    embed=Embed(description = f"Name: {user.name}\nId: {user.id}\n\n```python\n{page}```",
                    color=MAYABLUE)
                )
            else: pass
            continue   

def setup(bot):
    bot.add_cog(Social(bot))