# IndieOutreach Streamers Scraper v4.0

## Getting Started

#### Installation
  1. Clone this repo.
  2. Run `pip install --user twilio` (the scraper's use twilio to notify you when they stop running).
  3. Run `mkdir data` and `mkdir tmp` in the root folder of the repo. This will initialize the folders that are necessary for running the scrapers.
  4. Copy over your own `credentials.json` file into the root folder.

#### Running Manually
  1. `python mixer_scraper_runner.py -t` will start the mixer scraper, likewise Twitch. The -t flag is optional and will send notification texts to the number you specify in `credentials.json` when enabled.


#### Running with Cron
The better way to run the scrapers is to set them on cron jobs.
  1. Use crontab -l to view your current cronjobs.
  2. Use crontab -e to edit your cronjobs.
  3. Add the specified cron jobs. This will run the scraper and status checkers every 15 minutes.
  4. Wait for a text message telling you the scraper has started.
  5. If any scraping procedure fails to log its results in time, status_checker.py will notify the admin via text.

Cron Jobs to Add:
  1. `*/15 * * * * cd ~/.../scraper/ && python mixer_scraper_runner.py -t`
  2. `*/15 * * * * cd ~/.../scraper/ && python twitch_scraper_runner.py -t`
  3. `*/15 * * * * cd ~/.../scraper/ && python status_checker.py`


Note
  - the scraper runners keep track of process IDs to ensure they won't run if an existing version of the scraper is already running. Therefore, running the scraper on a cron job will only ever result in 1 scraper running at a time.



## Documentation
  - `mixer_database.md` - contains the schema for mixer.db
  - `twitch_database.md` - contains the schema for twitch.db
