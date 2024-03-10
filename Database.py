from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum
import os
from dotenv import load_dotenv

load_dotenv()
guild_name = os.getenv('DISCORD_GUILD')
db_url = f'sqlite:///{guild_name.replace(" ", "_").lower()}.db'
engine = create_engine(db_url)
base = declarative_base()

class BaseModel(base):
	__abstract__ = True
	__allow_unmapped__ = True

	id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)

class User(BaseModel):
	__tablename__ = 'user'

	username = Column(String, unique=True, nullable=False)
	won_matches = relationship('Match', primaryjoin='User.id==Match.winner_id')
	lost_matches = relationship('Match', primaryjoin='User.id==Match.loser_id')
	ranks = relationship('Rank', primaryjoin='User.id==Rank.user_id')

	def __init__(self, username):
		self.username = username

	def __repr__(self):
		return vars(self)

class RankType(enum.Enum):
	MONTH = 1
	ALL_TIME = 2

class Rank(BaseModel):
	__tablename__ = 'rank'

	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	value = Column(Integer, nullable=False)
	rank_type = Column(Enum(RankType), nullable=False)
	month = Column(Integer)
	year = Column(Integer)

	def __init__(self, user_id, value, rank_type, month, year):
		self.user_id = user_id
		self.value = value
		self.rank_type = rank_type
		self.month = month
		self.year = year

	def __repr__(self):
		return vars(self)

class Match(BaseModel):
	__tablename__ = 'match'

	replay_id = Column(String, unique=True, nullable=False)
	format = Column(String, nullable=False)
	date = Column(DateTime, nullable=False)
	winner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	winning_roster = Column(String, nullable=False)
	loser_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	losing_roster = Column(String, nullable=False)

	def __init__(self, replay_id, format, date, winner_id, winning_roster, loser_id, losing_roster):
		self.replay_id = replay_id
		self.format = format
		self.date = date
		self.winner_id = winner_id
		self.winning_roster = winning_roster
		self.loser_id = loser_id
		self.losing_roster = losing_roster

	def __repr__(self):
		return vars(self)

base.metadata.create_all(engine)
session_maker = sessionmaker(bind=engine)
session = session_maker()