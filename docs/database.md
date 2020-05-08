# About Databases

## SQLite Commands
SQLite commands have been pre-defined and are stored in JSON files in the `/sql` folder. Each JSON file has a set of commands relating to their filename.
  - Commands are stored in arrays.

#### create.json
CREATE TABLE commands that are needed for initializing databases.
  - `create-tables-mixer` - all the CREATE TABLE statements for initializing the mixer.db file
  - `create-tables-twitch` - all the CREATE TABLE statements for Twitch.

#### select.json
 - `get-all-channel-ids-mixer` - retrieves all channel_ids that are currently in the mixer.db
