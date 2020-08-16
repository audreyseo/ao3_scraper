ao3\_scraper
==========

# Description
Allows for easy scraping of stats from [AO3](archiveofourown.org).
You can either use it to scrape stats from a given search url or
give it the search parameters, just as if you were filling out the
advanced search on AO3.

Please note that this is not at all an official scraper for AO3.
(Apparently there has been one in the works or something like that
for a very long, long time, but we have yet to see one.) See other
disclaimers at the bottom of the README.

# Technical Details

## Dependencies
Uses Python 3. Requires that you have the following installed:

 - `bs4` for `BeautifulSoup`
 - `requests`

Install (probably in a `venv`) using `pip install bs4 requests`


## Usage
The `scrape.py` program performs the actual scraping. If you
run the command `python3 scrape.py --help` or `python3 ao3_scrape.py -h`
you will get the following output:

```
usage: scrape.py [-h] [-c [CATEGORY [CATEGORY ...]]] [-r RATING]
                 [-w [WARNING [WARNING ...]]] [-p PAGE] [-e END_PAGE]
                 [-m MAX_WORKS] [--page_increment PAGE_INCREMENT]

optional arguments:
  -h, --help            show this help message and exit
  -c [CATEGORY [CATEGORY ...]], --category [CATEGORY [CATEGORY ...]]
                        List (without commas) of any of FF, MM, FM, Gen,
                        Multi, or Other
  -r RATING, --rating RATING
                        Rating, if any, of content. Valid values are G, T, M,
                        E, and NR
  -w [WARNING [WARNING ...]], --warning [WARNING [WARNING ...]]
                        List (without commas) of any of NAWA (No Archive
                        Warnings Apply), RNC (Rape/Non-Con), MCD (Major
                        Character Death), CNTUAW (Choose Not To Use Archive
                        Warnings), and Underage
  -p PAGE, --page PAGE  Which page of the search to start from
  -e END_PAGE, --end_page END_PAGE
                        Which page to stop at. Use -1 to go to the end
  -m MAX_WORKS, --max_works MAX_WORKS
                        How many works' stats to include. -1 means all
                        possible.
  --page_increment PAGE_INCREMENT
                        Collect every nth page from a search, defaults to 1,
                        i.e. collecting every page from a search.
```

Please note that the last three commandline options are currently
not completely implemented.

### Examples

If you wanted to scrape all fics with both M/M and F/F pairings rated M (mature):

```
python3 scrape.py --category MM FF --rating M
```

To get all fics with the archive warning Major Character Death (MCD) and Gen pairings:

```
python3 scrape.py --category Gen --warning MCD
```

If your scrape for Major Character Death and Gen pairings failed to retrieve page 5 of the search, but it's already recorded data for pages 1-4, then you can use:
```
python3 scrape.py --category Gen --warning MCD --page 5
```


## Scrape Data

Scraped data is saved into a file of the format `batch_[timestamp][number].json`.
The `json` file contains an array with all of the works scraped, plus
a single entry at the beginning that gives you the parameters for the search,
to aid in some replicability.

The information that is contained for each work is as follows:

 - title
 - url
 - author
 - url to the author's page
 - fandom URL(s)
 - rating
 - archive warnings
 - pairing categories (M/M, F/F, F/M, Multi, Gen, Other)
 - whether the work is complete
 - date last updated
 - relationship(s) in the fic
 - character(s) in the fic
 - other tags
 - summary
 - language
 - number of words
 - number of chapters
 - number of planned chapters/total number of chapters (-1 if unknown)
 - number of hits

This scraper does not actually capture the contents of each work, since
the goal for this AO3 scraper is to collect large amounts of data for
many fics, in order to analyze it, though this is a possible update for
the future.

## Future Updates
The following are some ideas for features that would be good to implement,
as well as some extra utilities that would be good to have, in no
particular order:

 - include an end page for the search (inclusive)
 - set a max number of works to add
 - set a page increment (useful for splitting up work amongst n many machines, since there's this whole problem of how you can only get the results of one page (20 works) every 5 seconds)
 - add support for other search parameters (pairing, fandom, etc.)
 - add support for negative search parameters (exclude a rating, a pairing, etc.)
 - add support for exists/forall on certain parameters
 - add a batch collator (that takes all of the batch files and makes them into one json file, instead of multiple)
 - add basic stats support for examining a batch

## Disclaimers
Please use responsibly. Also note that occasionally when scraping a search
with many pages, you will run into an issue where the search fails early.
Since the scraper accessing AO3 every 5 seconds, every once in a while AO3
declines to serve any content at all to the scraper, and the only thing
in the page that is served is the message "Retry later"

This usually only happens after at least scraping data from 100 pages of a
search.

## Issues, Bug Reports, Pull Requests
I only made this because all of the other (entirely unofficial)
AO3 scrapers were not exactly what I needed. So there may be problems that
I am unaware of because there is literally one person coding all of this.

But, if you would like to contribute further, please submit an issue via
GitHub's issue tracker above, or a pull request if you'd be so kind!
