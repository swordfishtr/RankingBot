import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from Service import Service
from Database import RankType
import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_NAME = os.getenv('DISCORD_GUILD')
MATCH_PREFIX = os.getenv('MATCH_PREFIX')
MATCH_CHANNEL = os.getenv('MATCH_CHANNEL')
POKEMON_USAGE_CHANNEL = os.getenv('POKEMON_USAGE_CHANNEL')
LADDER_CHANNEL = os.getenv('LADDER_CHANNEL')
DEV_USER = os.getenv('DEV_USER')

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='+', intents=intents)

service = Service()

@bot.event
async def on_ready():
	guild, match_channel = get_channel_by_name(MATCH_CHANNEL)
	print(f'{bot.user} is connected to the following guild:\n{guild.name}(id: 'f'{guild.id})')
	print('.....Initializing.....')
	latest_match_date = service.get_latest_match_date()
	try:
		await scan_replays(10, latest_match_date)
		print('.....Bot has finished initializing.....')
	except Exception as e:
		print(e)

@bot.event
async def on_message(message):
	if message.channel.name == MATCH_CHANNEL and MATCH_PREFIX in message.content:
		try:
			links = get_links(message.content)
			for link in links:
				response = service.process_match(link)
				if service.ladder_enabled:
					if response:
						await message.channel.send(embed=generate_embed('🪜   Ladder Update   🪜', service.latest_rank_update_text[RankType.MONTH], 0x5C2C06))
					else:
						await message.channel.send(embed=generate_embed('🛑   Warning   🛑', 'Match already processed', 0xE60019))
			await update_usage_stats()
			await update_ladder_stats()
		except Exception as e:
			print(e)
			await message.channel.send(embed=BOT_WARNING_EMBED)
	await bot.process_commands(message)

@bot.command(name='ranking', help='Use this command to get rankings')
async def ranking(ctx, rank_type='month', unranked='ranked', limit=20, format='gen9customgame'):
	try:
		if service.ladder_enabled:
			if rank_type == 'all':
				rank_text = service.generate_rank_text(RankType.ALL_TIME, None, unranked == 'unranked', limit, format)
			else:
				rank_text = service.generate_rank_text(RankType.MONTH, datetime.datetime.utcnow(), unranked == 'unranked', limit, format)
			await ctx.channel.send(embed=generate_embed('👑   Rankings   👑', rank_text, 0x8B0000))
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='past_ranking', help='Use this command to get past rankings')
async def past_ranking(ctx, month='01', year='1970', unranked='ranked', limit=20, format='gen9customgame'):
	try:
		rank_text = service.generate_rank_text(RankType.MONTH, datetime.datetime(year=int(year), month=int(month), day=1, tzinfo=datetime.timezone.utc), unranked == 'unranked', limit, format)
		await ctx.channel.send(embed=generate_embed(f'⌛   Past Rankings ({month}/{year})   ⌛', rank_text, 0xCD7F32))
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='show_rank', help='Use this command to get past rankings')
async def show_rank(ctx, username, rank_type='month', format='gen9customgame'):
	try:
		if service.ladder_enabled:
			if rank_type == 'all':
				rank_text = service.get_user_rank(username.lower(), RankType.ALL_TIME, None, format)
			else:
				rank_text = service.get_user_rank(username.lower(), RankType.MONTH, datetime.datetime.utcnow(), format)
			await ctx.channel.send(embed=generate_embed(f'⭐   {username} Rank   ⭐', rank_text, 0x4169E1))
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='pokemon_usage', help='Use this command to get pokemon usage')
async def pokemon_usage(ctx, username='all', usage_type='most', rank_type='month', limit=5, format='gen9customgame'):
	try:
		if username == 'all':
			if rank_type == 'all':
				usage_text = service.get_all_pokemon_usage(usage_type, RankType.ALL_TIME, None, limit, format)
			else:
				usage_text = service.get_all_pokemon_usage(usage_type, RankType.MONTH, datetime.datetime.utcnow(), limit, format)
		else:
			if rank_type == 'all':
				usage_text = service.get_pokemon_usage(username.lower(), usage_type, RankType.ALL_TIME, None, limit, format)
			else:
				usage_text = service.get_pokemon_usage(username.lower(), usage_type, RankType.MONTH, datetime.datetime.utcnow(), limit, format)
		embed = generate_embed(f'🐉   {"All Time" if username == "all" else username} Pokemon Usage   🐉', usage_text, 0x1DB954)
		embed.set_image(url=f'https://play.pokemonshowdown.com/sprites/ani/{usage_text.split("**")[1].split("**")[0].lower().replace(".", "").replace(" ", "")}.gif')
		await ctx.channel.send(embed=embed)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='pokemon_usage_one', help='Use this command to get pokemon usage for a single pokemon')
async def pokemon_usage_one(ctx, pokemon, usage_type='most', rank_type='month', format='gen9customgame'):
	try:
		if rank_type == 'all':
			usage_text = service.get_pokemon_usage_one(pokemon, usage_type, RankType.ALL_TIME, None, format)
		else:
			usage_text = service.get_pokemon_usage_one(pokemon, usage_type, RankType.MONTH, datetime.datetime.utcnow(), format)
		embed = generate_embed(f'🐲   {pokemon} Usage   🐲', usage_text, 0xFFD700)
		if '**' in usage_text:
			embed.set_image(url=f'https://play.pokemonshowdown.com/sprites/ani/{usage_text.split("**")[1].split("**")[0].lower().replace(".", "").replace(" ", "")}.gif')
		await ctx.channel.send(embed=embed)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='past_pokemon_usage', help='Use this command to get past pokemon usage')
async def past_pokemon_usage(ctx, username='all', usage_type='most', month='01', year='1970', limit=5, format='gen9customgame'):
	try:
		if username == 'all':
			usage_text = service.get_all_pokemon_usage(usage_type, RankType.MONTH, datetime.datetime(year=int(year), month=int(month), day=1, tzinfo=datetime.timezone.utc), limit, format)
		else:
			usage_text = service.get_pokemon_usage(username.lower(), usage_type, RankType.MONTH, datetime.datetime(year=int(year), month=int(month), day=1, tzinfo=datetime.timezone.utc), limit, format)
		embed = generate_embed(f'🐉⌛  {"All Time" if username == "all" else username} Pokemon Usage ({month}/{year})  ⌛🐉', usage_text, 0x1DB954)
		embed.set_image(url=f'https://play.pokemonshowdown.com/sprites/ani/{usage_text.split("**")[1].split("**")[0].lower().replace(".", "").replace(" ", "")}.gif')
		await ctx.channel.send(embed=embed)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='rival', help='Use this command to get rival')
async def rival(ctx, username, rival_type='most', rank_type='month', limit=5, format='gen9customgame'):
	try:
		if rank_type == 'all':
			rival_text = service.get_rival(username.lower(), rival_type, RankType.ALL_TIME, None, limit, format)
		else:
			rival_text = service.get_rival(username.lower(), rival_type, RankType.MONTH, datetime.datetime.utcnow(), limit, format)
		await ctx.channel.send(embed=generate_embed(f'😈   {username} Rival   😈', rival_text, 0xA020F0))
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='toggle_ladder', help='Use this command to toggle ladder')
async def toggle_ladder(ctx):
	try:
		if ctx.author.display_name == DEV_USER:
			service.ladder_enabled = not service.ladder_enabled
			await ctx.channel.send(f'Clod\'s Ladder is now {"enabled" if service.ladder_enabled else "disabled"}.')
		else:
			await ctx.channel.send(embed=DEV_ONLY_WARNING_EMBED)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='update_pokemon_usage', help='Use this command to update the pokemon usage')
async def update_pokemon_usage(ctx):
	try:
		if ctx.author.display_name == DEV_USER:
			await update_usage_stats()
		else:
			await ctx.channel.send(embed=DEV_ONLY_WARNING_EMBED)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='update_ladder', help='Use this command to update the ladder')
async def update_ladder(ctx):
	try:
		if ctx.author.display_name == DEV_USER:
			await update_ladder_stats()
		else:
			await ctx.channel.send(embed=DEV_ONLY_WARNING_EMBED)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='scan_all_replays', help='Use this command to scan all replays')
async def scan_all_replays(ctx, month=None, year=None):
	try:
		if ctx.author.display_name == DEV_USER:
			if not month or not year:
				await scan_replays()
			else:
				await scan_replays(10, datetime.datetime(year=int(year), month=int(month), day=1))
		else:
			await ctx.channel.send(embed=DEV_ONLY_WARNING_EMBED)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='scan_thread', help='Use this command to scan a specific thread')
async def scan_thread(ctx, thread, channel=MATCH_CHANNEL):
	try:
		if ctx.author.display_name == DEV_USER:
			guild = discord.utils.get(bot.guilds, name=GUILD_NAME)
			match_channel = discord.utils.get(guild.text_channels, name=channel)
			match_thread = discord.utils.get(match_channel.threads, name=thread)
			messages = [message async for message in match_thread.history(limit=None, oldest_first=True)]
			scan_messages(messages, 10)
		else:
			await ctx.channel.send(embed=DEV_ONLY_WARNING_EMBED)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='ping', help='Use this command to ping a specific role')
async def ping(ctx, role, message):
	try:
		if role.lower() != 'here' and role.lower() != 'everyone':
			discord_role = discord.utils.get(ctx.guild.roles, name=role)
			await ctx.channel.send(f'{discord_role.mention} {message}')
		else:
			await ctx.channel.send(embed=BAD_ROLE_WARNING_EMBED)
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='glad', help='Use this command to ping a the 35 Gladiator role')
async def ping_gladiator(ctx, message=None):
	try:
		discord_role = discord.utils.get(ctx.guild.roles, name='35 Gladiator')
		await ctx.channel.send(f'{discord_role.mention}{" " + message if message else ""}')
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='spec', help='Use this command to ping a the 35 Spectator role')
async def ping_spectator(ctx, message=None):
	try:
		discord_role = discord.utils.get(ctx.guild.roles, name='35 Spectator')
		await ctx.channel.send(f'{discord_role.mention}{" " + message if message else ""}')
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='doub', help='Use this command to ping a the 35 Double role')
async def ping_double(ctx, message=None):
	try:
		discord_role = discord.utils.get(ctx.guild.roles, name='35 Double')
		await ctx.channel.send(f'{discord_role.mention}{" " + message if message else ""}')
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='baby', help='Use this command to ping a the 35 Baby role')
async def ping_baby(ctx, message=None):
	try:
		discord_role = discord.utils.get(ctx.guild.roles, name='35 Baby')
		await ctx.channel.send(f'{discord_role.mention}{" " + message if message else ""}')
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

def get_links(message):
	links = []
	tokens = message.split(MATCH_PREFIX)[1:]
	for token in tokens:
		links.append(MATCH_PREFIX + token.split('\n')[0].split(' ')[0].split('>')[0].split('?')[0].strip())
	return links

def generate_embed(title, content, color):
	embed = discord.Embed(title=title, description=content, color=color)
	return embed

def get_channel_by_name(channel):
	guild = discord.utils.get(bot.guilds, name=GUILD_NAME)
	return guild, next((x for x in guild.text_channels if x.name == channel), None)

async def update_usage_stats():
	guild, usage_channel = get_channel_by_name(POKEMON_USAGE_CHANNEL)
	messages = [message async for message in usage_channel.history(limit=1, oldest_first=False)]
	usage_text = service.get_all_pokemon_usage('most', RankType.MONTH, datetime.datetime.utcnow(), 20, 'gen9customgame')
	embed = generate_embed(f'🐉   Monthly Pokemon Usage   🐉', usage_text, 0x1DB954)
	embed.set_image(url=f'https://play.pokemonshowdown.com/sprites/ani/{usage_text.split("**")[1].split("**")[0].lower().replace(".", "").replace(" ", "")}.gif')
	try:
		await messages[0].edit(embed=embed)
	except:
		await usage_channel.send(embed=embed)

async def update_ladder_stats():
	guild, usage_channel = get_channel_by_name(LADDER_CHANNEL)
	messages = [message async for message in usage_channel.history(limit=1, oldest_first=False)]
	rank_text = service.generate_rank_text(RankType.MONTH, datetime.datetime.utcnow(), False, 20, 'gen9customgame')
	if len(rank_text.split('\n')) < 20:
		rank_text = service.generate_rank_text(RankType.MONTH, datetime.datetime.utcnow(), True, 20, 'gen9customgame')
	embed = generate_embed('👑   Monthly Rankings   👑', rank_text, 0x8B0000)
	try:
		await messages[0].edit(embed=embed)
	except:
		await usage_channel.send(embed=embed)

async def scan_replays(print_interval=100, date=None):
	guild, match_channel = get_channel_by_name(MATCH_CHANNEL)
	print(f'.....Scanning for replays{" after " + date.strftime("%m/%d/%Y") if date else ""}.....')
	if date:
		messages = [message async for message in match_channel.history(limit=None, after=date, oldest_first=True)]
	else:
		messages = [message async for message in match_channel.history(limit=None, oldest_first=True)]
	scan_messages(messages, print_interval)


def scan_messages(messages, print_interval):
	count = len(messages)
	print(f'.....Scanning {count} messages.....')
	processed_matches = 0
	already_processed_matches = 0
	for idx, message in enumerate(messages):
		if idx % print_interval == 0:
			print(f'.....{idx} / {count} messages scanned.....')
		if MATCH_PREFIX in message.content:
			links = get_links(message.content)
			for link in links:
				response = service.process_match(link)
				if response:
					processed_matches += 1
					print(f'**New** match processed ({processed_matches}): {link}')
				else:
					already_processed_matches += 1
					print(f'Match already processed ({already_processed_matches}): {link}')
	print(f'.....Bot has finished scanning ({processed_matches} new matches, {already_processed_matches} already processed).....')

BOT_WARNING_EMBED = generate_embed(f'⚠   Bot Warning   ⚠', 'Something went wrong', 0x3B3B3B)
DEV_ONLY_WARNING_EMBED = generate_embed(f'⚠   Bot Warning   ⚠', 'Sorry, this command is for developers only', 0x3B3B3B)
BAD_ROLE_WARNING_EMBED = generate_embed(f'⚠   Bot Warning   ⚠', 'Sorry, this role is not allowed', 0x3B3B3B)