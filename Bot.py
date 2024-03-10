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

@bot.command(name='ranking', help='Use this command to get rankings')
async def ranking(ctx, rank_type='month', unranked='unranked'):
	if rank_type == 'all':
		rank_text = service.generate_rank_text(RankType.ALL_TIME, None, unranked == 'unranked')
	else:
		rank_text = service.generate_rank_text(RankType.MONTH, datetime.datetime.now(), unranked == 'unranked')
	await ctx.channel.send(rank_text)
	return

@bot.command(name='past_ranking', help='Use this command to get past rankings')
async def past_ranking(ctx, month='01', year='1970', unranked='unranked'):
	rank_text = service.generate_rank_text(RankType.MONTH, datetime.datetime(year=int(year), month=int(month), day=1), unranked == 'unranked')
	await ctx.channel.send(rank_text)
	return

@bot.command(name='show_rank', help='Use this command to get past rankings')
async def show_rank(ctx, username, rank_type='month'):
	if rank_type == 'all':
		rank_text = service.get_user_rank(username, RankType.ALL_TIME, None)
	else:
		rank_text = service.get_user_rank(username, RankType.MONTH, datetime.datetime.now())
	await ctx.channel.send(f'{username}: {rank_text}')
	return

@bot.command(name='pokemon_usage', help='Use this command to get pokemon usage')
async def pokemon_usage(ctx, username='all', usage_type='most', rank_type='month'):
	if username == 'all':
		if rank_type == 'all':
			usage_text = service.get_all_pokemon_usage(usage_type, RankType.ALL_TIME, None)
		else:
			usage_text = service.get_all_pokemon_usage(usage_type, RankType.MONTH, datetime.datetime.now())
	else:
		if rank_type == 'all':
			usage_text = service.get_pokemon_usage(username, usage_type, RankType.ALL_TIME, None)
		else:
			usage_text = service.get_pokemon_usage(username, usage_type, RankType.MONTH, datetime.datetime.now())
	await ctx.channel.send(f'{username}: {usage_text}')
	return

@bot.command(name='rival', help='Use this command to get rival')
async def rival(ctx, username, rival_type='most', rank_type='month'):
	if rank_type == 'all':
		rival_text = service.get_rival(username, rival_type, RankType.ALL_TIME, None)
	else:
		rival_text = service.get_rival(username, rival_type, RankType.MONTH, datetime.datetime.now())
	await ctx.channel.send(f'{username}: {rival_text}')
	return

def clean_link(message):
	return MATCH_PREFIX + message.split(MATCH_PREFIX)[1].split('\n')[0].split(' ')[0].split('>')[0].strip()