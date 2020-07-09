# Extracting Information from the Main Database

1. `SELECT game_name, game_id from games WHERE game_name LIKE '%smash%';`
  - Super Smash Bros. Ultimate | 504461

2. `SELECT DISTINCT(streamer_id) FROM livestreams WHERE game_id=504461;`
  - returns a list of streamer IDs 
