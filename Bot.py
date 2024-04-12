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

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='+', intents=intents)

service = Service()

@bot.event
async def on_ready():
	guild, match_channel = get_channel_by_name(MATCH_CHANNEL)
	print(f'{bot.user} is connected to the following guild:\n{guild.name}(id: 'f'{guild.id})')
	print(f'.....Initializing.....')
	latest_match_date = service.get_latest_match_date()
	if latest_match_date:
		messages = [message async for message in match_channel.history(limit=None, after=latest_match_date, oldest_first=True)]
	else:
		messages = [message async for message in match_channel.history(limit=None, oldest_first=True)]
	for message in messages:
		if MATCH_PREFIX in message.content:
			link = clean_link(message.content)
			service.process_match(link)
	print(f'.....Bot has finished initializing.....')

@bot.event
async def on_message(message):
	if message.channel.name == MATCH_CHANNEL and MATCH_PREFIX in message.content:
		link = clean_link(message.content)
		response = service.process_match(link)
		if service.ladder_enabled:
			if response:
				await message.channel.send(embed=generate_embed('🪜   Ladder Update   🪜', service.latest_rank_update_text[RankType.MONTH], 0x5C2C06))
			else:
				await message.channel.send(embed=generate_embed('🛑   Warning   🛑', 'Match already processed', 0xE60019))
		await update_usage_stats()
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
		service.ladder_enabled = not service.ladder_enabled
		await ctx.channel.send(f'Clod\'s Ladder is now {"enabled" if service.ladder_enabled else "disabled"}.')
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

@bot.command(name='update_pokemon_usage', help='Use this command to update te pokemon usage')
async def update_pokemon_usage(ctx):
	try:
		await update_usage_stats()
	except Exception as e:
		print(e)
		await ctx.channel.send(embed=BOT_WARNING_EMBED)
	return

def clean_link(message):
	return MATCH_PREFIX + message.split(MATCH_PREFIX)[1].split('\n')[0].split(' ')[0].split('>')[0].split('?')[0].strip()

def generate_embed(title, content, color):
	embed = discord.Embed(title=title, description=content, color=color)
	return embed

def get_channel_by_name(channel):
	guild = discord.utils.get(bot.guilds, name=GUILD_NAME)
	return guild, next((x for x in guild.text_channels if x.name == channel), None)

async def update_usage_stats():
	guild, usage_channel = get_channel_by_name(POKEMON_USAGE_CHANNEL)
	message = (await usage_channel.history(limit=1).flatten())[0]
	usage_text = service.get_all_pokemon_usage('most', RankType.MONTH, datetime.datetime.utcnow(), 20, 'gen9customgame')
	embed = generate_embed(f'🐉   Monthly Pokemon Usage   🐉', usage_text, 0x1DB954)
	embed.set_image(url=f'https://play.pokemonshowdown.com/sprites/ani/{usage_text.split("**")[1].split("**")[0].lower().replace(".", "").replace(" ", "")}.gif')
	try:
		await message.edit(embed=embed)
	except:
		await usage_channel.send(embed=embed)

BOT_WARNING_EMBED = generate_embed(f'⚠   Bot Warning   ⚠', 'Something went wrong', 0x3B3B3B)