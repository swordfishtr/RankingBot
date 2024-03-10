# Ranking Bot: An ELO tracking Discord bot for Pokemon Showdown replays

## Set up
- Clone this git repository to your local machine
- Create a `.env` file with the following variables:
  - `DISCORD_TOKEN`: Generated bot token
  - `DISCORD_GUILD`: Name of Discord server
  - `MATCH_PREFIX`: Replay prefix used to match valid replays (e.g. `https://replay.pokemonshowdown.com`)
  - `MATCH_CHANNEL`: Channel where replays are posted
- Run the main file: `python Main.py`
  - If this is successful, the console should say `{Bot name} is connected to the following guild: {Discord server name}(id: {Discord server id})`
  - Bot will start to initialize by reading all message history in that channel and scanning for replays
    - This will take a long time depending on how active the server is; Assume 5-15 minutes at least
    - This is a one time action. Once the messages have been scanned, all replays will be stored in DB
    - Even if bot is taken offline, data will persist and account for all missing replays when started again
   
## Bot commands
- `+ranking`
  - Parameters:
    - `rank_type`: Takes values of `month` or `all`, defaults to `month`
    - `unranked`: Takes values of `unranked` or `ranked`, defaults to `unranked`
- `+past_ranking`
  - Parameters:
    - `month`: Takes any two digit integer, defaults to `01`
    - `year`: Takes any four digit integer, defaults to `1970`
    - `unranked`: Takes values of `unranked` or `ranked`, defaults to `unranked`
- `+show_rank`
  - Parameters:
    - `username`: Takes any showdown username
    - `rank_type`: Takes values of `month` or `all`, defaults to `month`
- `+pokemon_usage`
  - Parameters:
    - `username`: Takes any showdown username or `all`, defaults to `all`
    - `usage_type`: Takes values of `most`, `win`, or `lose`, defaults to `most`
    - `rank_type`: Takes values of `month` or `all`, defaults to `month`
- `+rival`
  - Parameters:
    - `username`: Takes any showdown username
    - `rival_type`: Takes values of `most`, `win`, or `lose`, defaults to `most`
    - `rank_type`: Takes values of `month` or `all`, defaults to `month`