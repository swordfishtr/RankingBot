from urllib.request import Request, urlopen
import json
import datetime
from Database import User, Match, Rank, RankType, session
from sqlalchemy import select

class Service:
	def __init__(self):
		self.__elo_floor = 100
		self.__k_factor = 32
		self.__rating = 400

		self.latest_rank_update_text = {}

	def get_latest_match_date(self):
		response = session.execute(select(Match).order_by(Match.date.desc()))
		for match in response.scalars():
			return match.date
		return None

	def get_pokemon_usage(self, username, usage_type, rank_type, date):
		response = session.execute(select(User).where(User.username == username.strip().lower()))
		for user in response.scalars():
			if user.username == username:
				if rank_type == RankType.MONTH:
					won_matches = [x for x in user.won_matches if x.date.month == date.month and x.date.year == date.year]
					lost_matches = [x for x in user.lost_matches if x.date.month == date.month and x.date.year == date.year]
				else:
					won_matches = user.won_matches
					lost_matches = user.lost_matches
				if usage_type == 'most':
					pokemon = []
					for match in won_matches:
						pokemon.extend(match.winning_roster.split(','))
					for match in lost_matches:
						pokemon.extend(match.losing_roster.split(','))
					return max(set(pokemon), key=pokemon.count)
				elif usage_type == 'win':
					pokemon = []
					for match in won_matches:
						pokemon.extend(match.winning_roster.split(','))
					return max(set(pokemon), key=pokemon.count)
				elif usage_type == 'lose':
					pokemon = []
					for match in lost_matches:
						pokemon.extend(match.losing_roster.split(','))
					return max(set(pokemon), key=pokemon.count)

	def get_all_pokemon_usage(self, usage_type, rank_type, date):
		response = session.execute(select(User))
		all_won_matches = []
		all_lost_matches = []
		for user in response.scalars():
			all_won_matches.extend(user.won_matches)
			all_lost_matches.extend(user.lost_matches)

		if rank_type == RankType.MONTH:
			won_matches = [x for x in all_won_matches if x.date.month == date.month and x.date.year == date.year]
			lost_matches = [x for x in all_lost_matches if x.date.month == date.month and x.date.year == date.year]
		else:
			won_matches = all_won_matches
			lost_matches = all_lost_matches
		if usage_type == 'most':
			pokemon = []
			for match in won_matches:
				pokemon.extend(match.winning_roster.split(','))
			for match in lost_matches:
				pokemon.extend(match.losing_roster.split(','))
			return max(set(pokemon), key=pokemon.count)
		elif usage_type == 'win':
			pokemon = []
			for match in won_matches:
				pokemon.extend(match.winning_roster.split(','))
			return max(set(pokemon), key=pokemon.count)
		elif usage_type == 'lose':
			pokemon = []
			for match in lost_matches:
				pokemon.extend(match.losing_roster.split(','))
			return max(set(pokemon), key=pokemon.count)

	def get_user_rank(self, username, rank_type, date):
		response = session.execute(select(User).where(User.username == username.strip().lower()))
		for user in response.scalars():
			if user.username == username:
				if rank_type == RankType.MONTH:
					user_rank = next((x for x in user.ranks if x.rank_type == rank_type and x.month == date.month and x.year == date.year), None)
				else:
					user_rank = next((x for x in user.ranks if x.rank_type == rank_type), None)
				return round(user_rank.value)

	def generate_rank_text(self, rank_type, date, unranked):
		response = session.execute(select(User))
		user_rank_list = []
		for user in response.scalars():
			if rank_type == RankType.MONTH:
				user_rank = next((x for x in user.ranks if x.rank_type == rank_type and x.month == date.month and x.year == date.year), None)
			else:
				user_rank = next((x for x in user.ranks if x.rank_type == rank_type), None)
			if user_rank:
				user_rank_list.append({'user': user, 'rank': user_rank.value})
		user_rank_list.sort(key=lambda x: x['rank'], reverse=True)
		output_text = ''
		idx = 1
		for ur in user_rank_list:
			if rank_type == RankType.MONTH:
				won_matches = [x for x in ur['user'].won_matches if x.date.month == date.month and x.date.year == date.year]
				lost_matches = [x for x in ur['user'].lost_matches if x.date.month == date.month and x.date.year == date.year]
			else:
				won_matches = ur['user'].won_matches
				lost_matches = ur['user'].lost_matches
			total_games = len(won_matches) + len(lost_matches)
			wins = len(won_matches)
			losses = len(lost_matches)
			if (total_games >= 10):
				output_text += f'{idx}. **{ur["user"].username}**: {round(ur["rank"])} ({total_games}/{wins}/{losses})\n'
				idx += 1
			elif unranked:
				output_text += f'**{ur["user"].username}**: {round(ur["rank"])} ({total_games}/{wins}/{losses}) (ur)\n'
		return output_text

	def process_match(self, link):
		link = link + '.json'
		try:
			req = Request(url=link, headers={'User-Agent': 'Mozilla/5.0'})
			raw_data = json.loads(urlopen(req).read())
			log = raw_data['log']
			replay_id = raw_data['id']
			format = raw_data['formatid']
			date = datetime.datetime.fromtimestamp(raw_data['uploadtime'])

			user_one = self.__create_user(log.split('|player|p1|')[1].split('|')[0].strip().lower())
			user_two = self.__create_user(log.split('|player|p2|')[1].split('|')[0].strip().lower())

			player_one_roster = []
			for token in log.split('|poke|p1|')[1:]:
				player_one_roster.append(token.split('|')[0].split(',')[0].strip())

			player_two_roster = []
			for token in log.split('|poke|p2|')[1:]:
				player_two_roster.append(token.split('|')[0].split(',')[0].strip())

			winner_username = log.split('|win|')[1].split('|')[0].strip()

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
		except:
			print(f'Link not found: {link}')

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
				return match
		else:
			match = Match(replay_id, format, date, winner.id, winning_roster, loser.id, losing_roster)
			session.add(match)
			session.commit()
			self.__create_rank(winner, loser, date)
			return match

	def __create_rank(self, winner, loser, date):
		winner_monthly_rank = self.__create_monthly_rank(winner.id, date)
		loser_monthly_rank = self.__create_monthly_rank(loser.id, date)
		self.__update_rank(RankType.MONTH, winner, winner_monthly_rank, loser, loser_monthly_rank)
		winner_all_time_rank = self.__create_all_time_rank(winner.id)
		loser_all_time_rank = self.__create_all_time_rank(loser.id)
		self.__update_rank(RankType.ALL_TIME, winner, winner_all_time_rank, loser, loser_all_time_rank)

	def __create_monthly_rank(self, user_id, date):
		response = session.execute(select(Rank).where(Rank.user_id == user_id).where(Rank.rank_type == RankType.MONTH).where(Rank.month == date.month).where(Rank.year == date.year))
		for rank in response.scalars():
			if rank.user_id == user_id and rank.rank_type == RankType.MONTH and rank.month == date.month and rank.year == date.year:
				return rank
		else:
			rank = Rank(user_id, 1000, RankType.MONTH, date.month, date.year)
			session.add(rank)
			session.commit()
			return rank

	def __create_all_time_rank(self, user_id):
		response = session.execute(select(Rank).where(Rank.user_id == user_id).where(Rank.rank_type == RankType.ALL_TIME))
		for rank in response.scalars():
			if rank.user_id == user_id and rank.rank_type == RankType.ALL_TIME:
				return rank
		else:
			rank = Rank(user_id, 1000, RankType.ALL_TIME, None, None)
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
		self.latest_rank_update_text[rank_type] = f'{winner.username}: {original_winner_rank_value} --> {winner_rank.value}\n' \
		                                f'{loser.username}: {original_loser_rank_value} --> {loser_rank.value}'