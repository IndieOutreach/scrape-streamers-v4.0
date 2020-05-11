# IndieOutreach Streamers Scraper v4.0

## Getting Started

#### Installation
  1. Clone this repo.
  2. Run `pip install --user twilio` (the scraper's use twilio to notify you when they stop running).
  3. Run `mkdir data` and `mkdir tmp` in the root folder of the repo. This will initialize the folders that are necessary for running the scrapers.
  4. Copy over your own `credentials.json` file into the root folder.

#### Running Manually
  1. `python mixer_scraper_runner.py -t` will start the mixer scraper. The -t flag is optional and will send notification texts to the number you specify in `credentials.json` when enabled.

#### Running with Cron
The better way to run the scrapers is to set them on cron jobs.
  1. Use crontab -l to view your current cronjobs.
  2. Use crontab -e to edit your cronjobs.
  3. Add `*/15 * * * * cd ~/.../scraper/ && python mixer_scraper_runner.py -t`. This will run the scraper every 15 minutes.
  4. Wait for a text message telling you the scraper has started.

Note 
  - the scraper runners keep track of process IDs to ensure they won't run if an existing version of the scraper is already running. Therefore, running the scraper on a cron job will only ever result in 1 scraper running at a time.



## Documentation
  - `mixer_database.md` - contains the schema for mixer.db
