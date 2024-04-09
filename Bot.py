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

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='+', intents=intents)

service = Service()

@bot.event
async def on_ready():
	guild = discord.utils.get(bot.guilds, name=GUILD_NAME)
	print(f'{bot.user} is connected to the following guild:\n{guild.name}(id: 'f'{guild.id})')
	print(f'.....Initializing.....')
	match_channel = next((x for x in guild.text_channels if x.name == MATCH_CHANNEL), None)
	latest_match_date = service.get_latest_match_date()
	if latest_match_date:
		messages = [message async for message in match_channel.history(after=latest_match_date, oldest_first=True)]
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
		service.process_match(link)
		await message.channel.send(service.latest_rank_update_text[RankType.MONTH])
	await bot.process_commands(message)

@bot.command(name='initialize_from_file', help='Use this command to initialize from file')
async def initialize_from_file(ctx):
	with open('replays.txt') as file:
		for line in file:
			line = 'https://replay.pokemonshowdown.com/gen9customgame-' + line.strip()
			service.process_match(line)
	await ctx.channel.send('Finished initializing')
	return

@bot.command(name='ranking', help='Use this command to get rankings')
async def ranking(ctx, rank_type='month', unranked='ranked', limit=20):
	if rank_type == 'all':
		rank_text = service.generate_rank_text(RankType.ALL_TIME, None, unranked == 'unranked', limit)
	else:
		rank_text = service.generate_rank_text(RankType.MONTH, datetime.datetime.now(), unranked == 'unranked', limit)
	await ctx.channel.send(embed=generate_embed('👑   Rankings   👑', rank_text, 0x8B0000))
	return

@bot.command(name='past_ranking', help='Use this command to get past rankings')
async def past_ranking(ctx, month='01', year='1970', unranked='ranked', limit=20):
	rank_text = service.generate_rank_text(RankType.MONTH, datetime.datetime(year=int(year), month=int(month), day=1), unranked == 'unranked', limit)
	await ctx.channel.send(embed=generate_embed(f'⌛   Past Rankings ({month}/{year})   ⌛', rank_text, 0xCD7F32))
	return

@bot.command(name='show_rank', help='Use this command to get past rankings')
async def show_rank(ctx, username, rank_type='month'):
	if rank_type == 'all':
		rank_text = service.get_user_rank(username.lower(), RankType.ALL_TIME, None)
	else:
		rank_text = service.get_user_rank(username.lower(), RankType.MONTH, datetime.datetime.now())
	await ctx.channel.send(embed=generate_embed(f'⭐   {username} Rank   ⭐', rank_text, 0x4169E1))
	return

@bot.command(name='pokemon_usage', help='Use this command to get pokemon usage')
async def pokemon_usage(ctx, username='all', usage_type='most', rank_type='month', limit=5):
	if username == 'all':
		if rank_type == 'all':
			usage_text = service.get_all_pokemon_usage(usage_type, RankType.ALL_TIME, None, limit)
		else:
			usage_text = service.get_all_pokemon_usage(usage_type, RankType.MONTH, datetime.datetime.now(), limit)
	else:
		if rank_type == 'all':
			usage_text = service.get_pokemon_usage(username.lower(), usage_type, RankType.ALL_TIME, None, limit)
		else:
			usage_text = service.get_pokemon_usage(username.lower(), usage_type, RankType.MONTH, datetime.datetime.now(), limit)
	embed = generate_embed(f'🐉   {"All Time" if username == "all" else username} Pokemon Usage   🐉', usage_text, 0x1DB954)
	embed.set_image(url=f'https://play.pokemonshowdown.com/sprites/ani/{usage_text.split("**")[1].split("**")[0].lower()}.gif')
	await ctx.channel.send(embed=embed)
	return

@bot.command(name='rival', help='Use this command to get rival')
async def rival(ctx, username, rival_type='most', rank_type='month', limit=5):
	if rank_type == 'all':
		rival_text = service.get_rival(username.lower(), rival_type, RankType.ALL_TIME, None, limit)
	else:
		rival_text = service.get_rival(username.lower(), rival_type, RankType.MONTH, datetime.datetime.now(), limit)
	await ctx.channel.send(embed=generate_embed(f'😈   {username} Rival   😈', rival_text, 0xA020F0))
	return

def clean_link(message):
	return MATCH_PREFIX + message.split(MATCH_PREFIX)[1].split('\n')[0].split(' ')[0].split('>')[0].strip()

def generate_embed(title, content, color):
	embed = discord.Embed(title=title, description=content, color=color)
	return embed