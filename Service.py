from urllib.request import Request, urlopen
import json
import datetime
from Database import User, Match, Rank, RankType, session
from sqlalchemy import select

class Service:
	def __init__(self):
		self.__elo_floor = 100
		self.__k_factor = 60
		self.__rating = 1000
		self.__elo_start = 1000
		self.__ranked_threshold = 15

		self.latest_rank_update_text = {}
		self.ladder_enabled = True

	def get_latest_match_date(self):
		response = session.execute(select(Match).order_by(Match.date.desc()))
		for match in response.scalars():
			return match.date
		return None

	def get_num_matches_between(self, date_1, date_2):
		query = session.query(Match).filter(Match.date.between(date_1, date_2))
		response = session.execute(query)
		size = 0
		for match in response.scalars():
			size += 1
		return size

	def get_rival(self, username, rival_type, rank_type, date, limit, format):
		response = session.execute(select(User).where(User.username == username.strip().lower()))
		for user in response.scalars():
			if user.username == username:
				if rank_type == RankType.MONTH:
					won_matches = [x for x in user.won_matches if x.format == format and x.date.month == date.month and x.date.year == date.year]
					lost_matches = [x for x in user.lost_matches if x.format == format and x.date.month == date.month and x.date.year == date.year]
				else:
					won_matches = [x for x in user.won_matches if x.format == format]
					lost_matches = [x for x in user.lost_matches if x.format == format]
				if rival_type == 'most':
					users = []
					for match in won_matches:
						users.append(match.loser_id)
					for match in lost_matches:
						users.append(match.winner_id)
					return self.__get_rival_text(users, limit, len(won_matches) + len(lost_matches))
				elif rival_type == 'win':
					users = []
					for match in won_matches:
						users.append(match.loser_id)
					return self.__get_rival_text(users, limit, len(won_matches))
				elif rival_type == 'lose':
					users = []
					for match in lost_matches:
						users.append(match.winner_id)
					return self.__get_rival_text(users, limit, len(lost_matches))
				else:
					return 'No rival found'

	def __get_rival_text(self, user_ids, limit, total_matches):
		user_count = {}
		usage_text = ''
		for u in user_ids:
			user_count[u] = user_count.get(u, 0) + 1
		idx = 0
		for k, v in sorted(user_count.items(), key=lambda item: item[1], reverse=True):
			idx += 1
			user_response = session.execute(select(User).where(User.id == k))
			for user in user_response.scalars():
				if user.id == k:
					usage_text += f'{idx}. **{user.username}** ({self.__get_percentage(v, total_matches)})\n'
			if idx == limit:
				break
		return usage_text

	def get_pokemon_usage_one(self, pokemon, usage_type, rank_type, date, format):
		usage_text = self.get_all_pokemon_usage(usage_type, rank_type, date, 99999999, format)
		for line in usage_text.split('\n'):
			pkm_name = line.split("**")[1].split("**")[0].lower()
			if pokemon.lower() == pkm_name:
				return line
		return 'Pokemon not found'

	def get_pokemon_usage(self, username, usage_type, rank_type, date, limit, format):
		response = session.execute(select(User).where(User.username == username.strip().lower()))
		for user in response.scalars():
			if user.username == username:
				if rank_type == RankType.MONTH:
					won_matches = [x for x in user.won_matches if x.format == format and x.date.month == date.month and x.date.year == date.year]
					lost_matches = [x for x in user.lost_matches if x.format == format and x.date.month == date.month and x.date.year == date.year]
				else:
					won_matches = [x for x in user.won_matches if x.format == format]
					lost_matches = [x for x in user.lost_matches if x.format == format]
				if usage_type == 'most':
					pokemon = []
					for match in won_matches:
						pokemon.extend(match.winning_roster.split(','))
					for match in lost_matches:
						pokemon.extend(match.losing_roster.split(','))
					return self.__get_pokemon_usage_text(pokemon, limit, len(won_matches) + len(lost_matches))
				elif usage_type == 'win':
					pokemon = []
					for match in won_matches:
						pokemon.extend(match.winning_roster.split(','))
					return self.__get_pokemon_usage_text(pokemon, limit, len(won_matches))
				elif usage_type == 'lose':
					pokemon = []
					for match in lost_matches:
						pokemon.extend(match.losing_roster.split(','))
					return self.__get_pokemon_usage_text(pokemon, limit, len(lost_matches))
				else:
					return 'No pokemon found'

	def get_all_pokemon_usage(self, usage_type, rank_type, date, limit, format):
		response = session.execute(select(User))
		all_won_matches = []
		all_lost_matches = []
		for user in response.scalars():
			all_won_matches.extend(user.won_matches)
			all_lost_matches.extend(user.lost_matches)

		if rank_type == RankType.MONTH:
			won_matches = [x for x in all_won_matches if x.format == format and x.date.month == date.month and x.date.year == date.year]
			lost_matches = [x for x in all_lost_matches if x.format == format and x.date.month == date.month and x.date.year == date.year]
		else:
			won_matches = [x for x in all_won_matches if x.format == format]
			lost_matches = [x for x in all_lost_matches if x.format == format]
		if usage_type == 'most':
			pokemon = []
			for match in won_matches:
				pokemon.extend(match.winning_roster.split(','))
			for match in lost_matches:
				pokemon.extend(match.losing_roster.split(','))
			return self.__get_pokemon_usage_text(pokemon, limit, len(won_matches) + len(lost_matches))
		elif usage_type == 'win':
			pokemon = []
			for match in won_matches:
				pokemon.extend(match.winning_roster.split(','))
			return self.__get_pokemon_usage_text(pokemon, limit, len(won_matches))
		elif usage_type == 'lose':
			pokemon = []
			for match in lost_matches:
				pokemon.extend(match.losing_roster.split(','))
			return self.__get_pokemon_usage_text(pokemon, limit, len(lost_matches))
		else:
			return 'No pokemon found'

	def __get_pokemon_usage_text(self, pokemon, limit, total_matches):
		pokemon_count = {}
		usage_text = ''
		for p in pokemon:
			pokemon_count[p] = pokemon_count.get(p, 0) + 1
		idx = 0
		for k, v in sorted(pokemon_count.items(), key=lambda item: item[1], reverse=True):
			idx += 1
			usage_text += f'{idx}. **{k}** ({self.__get_percentage(v, total_matches)})\n'
			if idx == limit:
				break
		return usage_text

	def __get_percentage(self, value, total):
		if round((value / total) * 100) == 0:
			return f'{round((value / total) * 100, 2)}%'
		else:
			return f'{round((value / total) * 100)}%'

	def get_user_rank(self, username, rank_type, date, format):
		rank_text = self.generate_rank_text(rank_type, date, True, 99999999, format)
		for line in rank_text.split('\n'):
			if username in line:
				return line
		return 'Username not found'

	def generate_rank_text(self, rank_type, date, unranked, limit, format):
		response = session.execute(select(User))
		user_rank_list = []
		for user in response.scalars():
			if rank_type == RankType.MONTH:
				user_rank = next((x for x in user.ranks if x.rank_type == rank_type and x.format == format and x.month == date.month and x.year == date.year), None)
			else:
				user_rank = next((x for x in user.ranks if x.rank_type == rank_type and x.format == format), None)
			if user_rank:
				user_rank_list.append({'user': user, 'rank': user_rank.value})
		user_rank_list.sort(key=lambda x: x['rank'], reverse=True)
		output_text = ''
		idx = 1
		for i, ur in enumerate(user_rank_list):
			if rank_type == RankType.MONTH:
				won_matches = [x for x in ur['user'].won_matches if x.format == format and x.date.month == date.month and x.date.year == date.year]
				lost_matches = [x for x in ur['user'].lost_matches if x.format == format and x.date.month == date.month and x.date.year == date.year]
			else:
				won_matches = [x for x in ur['user'].won_matches if x.format == format]
				lost_matches = [x for x in ur['user'].lost_matches if x.format == format]
			total_games = len(won_matches) + len(lost_matches)
			wins = len(won_matches)
			losses = len(lost_matches)
			if (total_games >= self.__ranked_threshold):
				output_text += f'{idx}. **{ur["user"].username}**: {round(ur["rank"])} ({total_games}P {wins}W {losses}L)\n'
				idx += 1
			elif unranked:
				output_text += f'**{ur["user"].username}**: {round(ur["rank"])} ({total_games}P {wins}W {losses}L) *unranked*\n'
			if len(output_text.split('\n')) - 1 == limit:
				break
		return output_text

	def process_match(self, link):
		link = link + '.json'
		try:
			req = Request(url=link, headers={'User-Agent': 'Mozilla/5.0'})
			raw_data = json.loads(urlopen(req).read())
		except OSError as err:
			print(f'Process Match Failed: {link}\nOS error: {err}')
			return
		except ValueError as err:
			print(f'Process Match Failed: {link}\nValue error: {err}')
			return
		except Exception as err:
			print(f'Process Match Failed: {link}\nException ({type(err)}): {err}')
			return
		log = raw_data['log']
		replay_id = raw_data['id']
		format = raw_data['formatid']
		date = datetime.datetime.utcfromtimestamp(raw_data['uploadtime'])

		user_one = self.__create_user(log.split('|player|p1|')[1].split('|')[0].strip().lower())
		user_two = self.__create_user(log.split('|player|p2|')[1].split('|')[0].strip().lower())

		player_one_roster = []
		for token in log.split('|poke|p1|')[1:]:
			player_one_roster.append(token.split('|')[0].split(',')[0].strip())

		player_two_roster = []
		for token in log.split('|poke|p2|')[1:]:
			player_two_roster.append(token.split('|')[0].split(',')[0].strip())

		winner_username = log.split('|win|')[1].split('|')[0].strip().lower()

		if winner_username == user_one.username:
			winner = user_one
			winning_roster = ','.join(player_one_roster)
			loser = user_two
			losing_roster = ','.join(player_two_roster)
		else:
			winner = user_two
			winning_roster = ','.join(player_two_roster)
			loser = user_one
			losing_roster = ','.join(player_one_roster)

		return self.__create_match(replay_id, format, date, winner, winning_roster, loser, losing_roster)

	def __create_user(self, username):
		response = session.execute(select(User).where(User.username == username))
		for user in response.scalars():
			if user.username == username:
				return user
		else:
			user = User(username)
			session.add(user)
			session.commit()
			return user

	def __create_match(self, replay_id, format, date, winner, winning_roster, loser, losing_roster):
		response = session.execute(select(Match).where(Match.replay_id == replay_id))
		for match in response.scalars():
			if match.replay_id == replay_id:
				return None
		else:
			match = Match(replay_id, format, date, winner.id, winning_roster, loser.id, losing_roster)
			session.add(match)
			session.commit()
			self.__create_rank(winner, loser, date, format)
			return match

	def __create_rank(self, winner, loser, date, format):
		winner_monthly_rank = self.__create_monthly_rank(winner.id, date, format)
		loser_monthly_rank = self.__create_monthly_rank(loser.id, date, format)
		self.__update_rank(RankType.MONTH, winner, winner_monthly_rank, loser, loser_monthly_rank)
		winner_all_time_rank = self.__create_all_time_rank(winner.id, format)
		loser_all_time_rank = self.__create_all_time_rank(loser.id, format)
		self.__update_rank(RankType.ALL_TIME, winner, winner_all_time_rank, loser, loser_all_time_rank)

	def __create_monthly_rank(self, user_id, date, format):
		response = session.execute(select(Rank).where(Rank.user_id == user_id).where(Rank.rank_type == RankType.MONTH).where(Rank.format == format).where(Rank.month == date.month).where(Rank.year == date.year))
		for rank in response.scalars():
			if rank.user_id == user_id and rank.rank_type == RankType.MONTH and rank.format == format and rank.month == date.month and rank.year == date.year:
				return rank
		else:
			rank = Rank(user_id, self.__elo_start, RankType.MONTH, format, date.month, date.year)
			session.add(rank)
			session.commit()
			return rank

	def __create_all_time_rank(self, user_id, format):
		response = session.execute(select(Rank).where(Rank.user_id == user_id).where(Rank.rank_type == RankType.ALL_TIME).where(Rank.format == format))
		for rank in response.scalars():
			if rank.user_id == user_id and rank.rank_type == RankType.ALL_TIME and rank.format == format:
				return rank
		else:
			rank = Rank(user_id, self.__elo_start, RankType.ALL_TIME, format, None, None)
			session.add(rank)
			session.commit()
			return rank

	def __update_rank(self, rank_type, winner, winner_rank, loser, loser_rank):
		winner_prob = 1 / (1 + (pow(10, ((loser_rank.value - winner_rank.value) / self.__rating))))
		loser_prob = 1 / (1 + (pow(10, ((winner_rank.value - loser_rank.value) / self.__rating))))

		original_winner_rank_value = winner_rank.value
		original_loser_rank_value = loser_rank.value

		winner_rank.value = max(winner_rank.value + (self.__k_factor * (1 - winner_prob)), self.__elo_floor)
		loser_rank.value = max(loser_rank.value + (self.__k_factor * (0 - loser_prob)), self.__elo_floor)

		session.commit()
		self.latest_rank_update_text[rank_type] = f'**{winner.username}**: {round(original_winner_rank_value)} --> {round(winner_rank.value)}\n' \
		                                f'**{loser.username}**: {round(original_loser_rank_value)} --> {round(loser_rank.value)}'