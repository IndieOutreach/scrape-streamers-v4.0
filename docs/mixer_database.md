# About Mixer Database

## SQLite Commands
SQLite commands have been pre-defined and are stored in JSON files in the `/sql` folder. Each JSON file has a set of commands relating to their filename.
  - Commands are stored in arrays and can be converted to just be strings where convenient.

#### mixer_create.json
CREATE TABLE commands that are needed for initializing databases.
  - `create-tables-mixer` - all the CREATE TABLE statements for initializing the mixer.db file

#### mixer_select.json
 - `get-all-channel-ids-mixer` - retrieves all channel_ids that are currently in the mixer.db
 - `get-all-game-ids-mixer` - retrieves all game_ids from the games table
 - `get-most-recent-entry-for-channel-mixer` - for an arbitrary channel, retrieve their chronologically most recent entry.
 - `get-channel-ids-that-have-recordings-mixer` - returns list of all channel_ids that are present in recordings table.
 - `get-channel-ids-with-no-recordings-mixer` - returns list of all channel_ids that are present in no_recordings table.

#### mixer_insert.json
  - `insert-new-channel-mixer` - insert into channels table
  - `update-channel-mixer` - update an existing channel's info in channels table
  - `insert-time-series-mixer` - insert into [followers, lifetime_viewers, sparks, experience, partnered] tables
  - `insert-livestream-snapshot-mixer` - insert into livestream_snapshots table
  - `insert-game-mixer` - insert into games table
  - `insert-game-snapshot-mixer` - insert into game_snapshots table
  - `insert-channel-no-recordings-mixer` - insert into no_recordings table
  - `insert-recording-mixer` - insert into recordings table
  - `insert-log-mixer` - insert into logs table


## Database Schema
#### Table: channels
Table containing profile information about a channel.
  1. `channel_id` - int
  2. `user_id` - int
  3. `token` - text
  4. `user_avatar_url` - text
  5. `banner_url` - text
  6. `vods_enabled` - bool
  7. `has_vods` - bool
  8. `description` - text
  9. `user_bio` - text
  10. `language` - text
  11. `date_joined` - epoch int (seconds)
  12. `date_first_scraped` - epoch int (seconds)
  13. `social` - text (JSON)
  14. `verified` - bool
  15. `audience` - text

#### Table: followers
Stores time-series data about the number of followers a channel has.
  1. `channel_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `value` - int  

#### Table: lifetime_viewers
Stores time-series data about the number of unique viewers a channel has.
  1. `channel_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `value` - int  


#### Table: sparks
Stores time-series data about the number of sparks a channel has over time.
  1. `channel_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `value` - int  

#### Table: experience
Stores time-series data about the amount of experience a channel has over time.
  1. `channel_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `value` - int  

#### Table: partnered
Stores time-series data about when channels get (un)partnered.
  1. `channel_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `value` - int  

#### Table: games
Table of all the games played on Mixer.
  1. `game_id` - int
  2. `game_name` - text
  3. `parent` - text
  4. `description` -text
  5. `cover_url` - text
  6. `background_url` - text

#### Table: recordings
Stores all the recordings by channels.
  1. `recording_id` - int
  2. `channel_id` - int
  3. `game_id` - int
  4. `date_scraped` - epoch int (seconds)
  5. `date_uploaded`- epoch int (seconds)
  6. `views` - int
  7. `duration` - double

#### Table: no_recordings
Stores channel_ids for channels that we tried to scrape recordings for (but they had none).
  1. `channel_id` - int
  2. `date_scraped` - epoch int (seconds)

#### Table: livestream_snapshots
Stores time-series data about all live channels on Mixer. This table gets updated roughly every 15 minutes, so it will contain multiple entries per 'livestream'.
  1. `channel_id` - int
  2. `game_id` - int
  3. `date_scraped` - epoch int (seconds)
  4. `viewers` - int

#### Table: livestreams
livestream_snapshots contains way too many entries per livestream to be sustainable for storage purposes. Therefore, we average datapoints from livestream_snapshots into one livestream object that we insert into livestreams. Then, we delete the snapshots from livestream_snapshots.
  1. `livestream_id` - int
  2. `channel_id` - int
  3. `game_id` - int
  4. `date_started` - epoch int (seconds)
  5. `date_ended` - epoch int (seconds)
  6. `times_scraped` - int
  7. `min_viewers` - int
  8. `max_viewers` - int
  9. `mean_viewers` - double
  10. `std_dev_viewers` - double

#### Table: game_snapshots
Stores time-series data about how games are doing on Mixer as a whole.
  1. `game_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `num_channels` - int
  4. `num_zero` - int
  5. `total_viewers` - int
  6. `min_viewers` - int
  7. `max_viewers` - int
  8. `median_viewers` - int
  9. `mean_viewers` - double
  10. `std_dev_viewers` - double

#### Table: logs
Stores TimeLogs and Stats about scraping procedures.
  1. `log_name` - text
  2. `date_started` - epoch int (seconds)
  3. `date_ended` - epoch int (seconds)
  4. `timelogs` - text (JSON)
  5. `stats` - text (JSON)
