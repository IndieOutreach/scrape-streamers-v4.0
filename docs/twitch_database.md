# About Twitch Database

## Database Schema

#### Table: streamers
Contains basic profile info about streamers
  1. `streamer_id` - int (called `user_id` on Twitch)
  2. `login` - text
  3. `display_name` - text
  4. `description` - text
  5. `profile_image_url` - text
  6. `offline_image_url` - text
  7. `date_first_scraped` - epoch int (seconds)


#### Table: followers
  1. `streamer_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `value` - int

#### Table: total_views
  1. `streamer_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `value` - int


#### Table: broadcaster_type
  1. `streamer_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `value` - int (0 if "", 1 if "affiliate", 2 if "partner")


#### Table: livestream_snapshots
  1. `livestream_id` - int
  2. `streamer_id` - int
  3. `game_id` - int
  4. `viewers` - int
  5. `date_started` - epoch int (seconds)
  6. `date_scraped` - epoch int (seconds)
  7. `tag_ids` - text(JSON)
  8. `language` - text

#### Table: videos
  1. `video_id` - int
  2. `streamer_id` - int
  3. `game_id` - int
  4. `view_count` - int
  5. `video_type` - text ('upload', 'archive', or 'highlight')
  6. `date_created` - epoch int (seconds)
  7. `date_published` - epoch int (seconds)
  8. `date_scraped` - epoch int (seconds)
  8. `duration` - double
  9. `language` - text

#### Table: no_videos
  1. `streamer_id` - int
  2. `date_scraped` - epoch int (seconds)

#### Table: games
  1. `game_id` - int
  2. `game_name` - text
  3. `box_art_url` - text

#### Table: game_snapshots
  1. `game_id` - int
  2. `date_scraped` - epoch int (seconds)
  3. `num_streamers` - int
  4. `num_zero` - int
  5. `total_viewers` - int
  6. `min_viewers` - int
  7. `max_viewers` - int
  8. `median_viewers` - int
  9. `mean_viewers` - double
  10. `std_dev_viewers` - double

#### Table: tags
  1. `tag_id` - int
  2. `is_auto` - boolean
  3. `english_name` - text
  4. `localization_names` - text(JSON)
  5. `english_description` - text
  6. `localization_descriptions` - text(JSON)

#### Table: logs
  1. `log_name` - text
  2. `date_started` - epoch int (seconds)
  3. `date_ended` - epoch int (seconds)
  4. `timelogs` - text(JSON)
  5. `stats` - text(JSON)
