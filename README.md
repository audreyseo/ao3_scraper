ao3\_scraper
==========

# Description
Allows for easy scraping of stats from [AO3](archiveofourown.org).
You can either use it to scrape stats from a given search url or
give it the search parameters, just as if you were filling out the
advanced work search on AO3. This does not scrape the works themselves,
but instead collects data on each work.

Please note that this is not at all an official scraper for AO3.
(Apparently there has been one in the works or something like that
for a very long, long time, but we have yet to see one.) See other
disclaimers at the bottom of this README.

## Searchable Parameters

The parameters that can be searched from the command line are as
follows:

 - `rating`: G (General Audiences), T (Teen And Up Audiences), M (Mature), E (Explicit), NR (Not Rated)
 - `category`: `FF` (F/F or femslash), `MM` (M/M or slash), `FM` (F/M), Gen, Multi, and Other
 - `warning`: `NAWA` (No Archive Warnings Apply), `RNC` (Rape/Non-Con), `MCD` (Major Character Death), `GDOV` (Graphic Depictions Of Violence), `Underage`, and `CNTUAW` (Choose Not To Use Archive Warnings)

While there currently aren't options to search other parameters
from the command line itself, you can always use the `--from-url`
option and paste in your own AO3 search url (see further details
below).

### Data collection considerations

By default, if you initiate a search by using command line arguments
and not a search url, it will sort the results based on the date
created and in ascending order, i.e. from oldest created to newest.
This eliminates most shifting around of data, since the default search
sorts by best match and in descending order (from best to worst),
which can change from hour to hour, day to day. This also catches works
that are newly posted, since they will appear at the very last page, in
case new works were posted during the scrape (which often happens).

Thus the only problem that can occur is if someone deletes their works,
which will shift data that was in future pages to pages that may have
already been scraped.

### Caveats about how AO3 counts results

Usually, the total number of scraped works will come very close to the
real number, but will not match it exactly. So far, I've observed a
difference of about +/-50, especially for searches that bring up more
than 50,000 works.

This may be a bug, but it's also a difference of about 0.1% (or even less)
in most cases, and since it can only scrape every 5 seconds, it would take
nearly 70 hours to check each work's url, if we assume there are
only 50,000 of them.

I also have to wonder if AO3 is counting the number of results strangely
as well, I noticed that if you do a search for all works with 0-1000 words,
1001-2000 words, 2001-3200 words, 3201-5400 words, 5401-9200 words, 9201-20,200 words,
and >20,200 words, and add up all of the works, you are also missing about
50 works that a search that disregards word count entirely apparently finds.

If anyone has an answer for why any of this might be, please go ahead and
submit an issue, or comment on #49.

# Technical Details

## Dependencies
Uses Python 3. Requires that you have the following installed:

 - `bs4` for `BeautifulSoup`
 - `requests`
 - `ansicolors`

Install (probably in a `venv`) using `pip install bs4 requests ansicolors`


## Usage
The `scrape.py` program performs the actual scraping. If you
run the command `python3 scrape.py --help` or `python3 ao3_scrape.py -h`
you will get the following output:

```
usage: scrape.py [-h] [-c [CATEGORY [CATEGORY ...]]] [-r RATING]
                 [-w [WARNING [WARNING ...]]] [-p PAGE] [-e END_PAGE]
                 [-m MAX_WORKS] [--page_increment PAGE_INCREMENT]
                 [--split_by {none,fandoms}] [--test_run] [-u FROM_URL]
                 [--from-url-file FROM_URL_FILE] [--split-by-word-count]
                 [--ranges [RANGES [RANGES ...]]] [--range-excludes-zero]

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
  -e END_PAGE, --end-page END_PAGE
                        Which page to stop at. Use -1 to go to the end
  -m MAX_WORKS, --max_works MAX_WORKS
                        How many works' stats to include. -1 means all
                        possible.
  --page_increment PAGE_INCREMENT
                        Collect every nth page from a search, defaults to 1,
                        i.e. collecting every page from a search.
  --split_by {none,fandoms}
                        Split a search over every searchable tag. Currently
                        only supports search over all fandoms. (This helps to
                        make a broad search more tractable)
  --test_run            Run a test by only collecting the first 100 works.
                        Saves the resulting scraped data to a file(s) named
                        test_[timestamp][number].json. To collect more or less
                        works for your test run, set using -m/--max_works.
  -u FROM_URL, --from-url FROM_URL
                        Use a given url to start a search. This effectively
                        ignores the commandline options --rating, --warning,
                        --category, and --page. However --max_works/-m should
                        still function as normal. Also note that this will
                        alter what shows up in the params saved at the
                        beginning of every batch file. Only parameters that
                        can be altered via these command line optinos will be
                        saved there.
  --from-url-file FROM_URL_FILE
                        Takes files either ending with .json or .txt. If
                        ending in .json, the program expects that the object
                        contained will have entries named "params_dict" and
                        "urls", containing a dictionary of the parameters that
                        should be assigned to the batch and a list of AO3
                        search URLs to scrape, respectively. If it's a text
                        file, the program expects just a list of AO3 search
                        URLs in the file. Note that as in --from-url, any
                        search parameters set using commandline options
                        --rating, --warning, etc. will be ignored. But
                        additionally, --from-url will also be ignored.
  --split-by-word-count
                        Uses a chosen parameter to split the search over. This
                        helps to perform searches that would otherwise have
                        more than 100,000 results, and scrape all the data.
                        The only valid choice at the moment is to split by
                        word counts.
  --ranges [RANGES [RANGES ...]]
                        Used with --split-by. Defaults to splitting word count
                        by a distribution that makes every query less than
                        10,000 results (often, much less), for F/F with the
                        rating Teen Up And Audiences. Takes a list of positive
                        integers. Note that it automatically processes 0 as
                        being the first element, and for the last number, it
                        will do a search for >[last number] at the very end.
                        Additionally, if the values aren't sorted, it will do
                        that for you anyway: from smallest to largest.
  --range-excludes-zero
                        Used with --ranges. If you enter --ranges n1 n2 n3 n4
                        n5, it would usually make ranges 0-n1, (n1+1)-n2,
                        (n2+1)-n3, (n3+1)-n4, (n4+1)-n5, and >n5. But with the
                        --range-excludes-zero option, it makes ranges
                        (n1+1)-n2 and onward. Useful for restarting a query
                        for splits.
```

Please note that the command line argument `--page_increment` is not currently
implemented.

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

If your search pulls up more than 100,000 results, then you can split it over
a bunch of word count ranges. (Please note that sometimes this fails to add up
to the full number, which is a baffling fact that I would really love AO3 to
explain to me.) For example, a search for all fics with FF pairings rated Teen
And Up Audiences (T) generates more than 100,000 results, then you can use
`--split-by-word-count` to split up the search into more appropriately-sized
chunks.

```
python3 scrape.py -c FF -r T --split-by-word-count
```

If you want to split up the search into custom chunks, you can use the
`--ranges` option.

```
python3 scrape.py -c FF -r T --split-by-word-count --ranges 100 200 300 400 10000
```

As noted above, a call of `--ranges m n l p` will generate ranges `0-m`, `(m+1)-n`,
`(n+1)-l`, `(l+1)-p`, and `>p`, to find all works with word counts between `0` and `m`, `m+1`
and `n`, `n+1` and `l`, `l+1` and `p`, and greater than `p`. If you don't want to include
the zero part of the range, use `--range-excludes-zero`:

```
python3 scrape.py -c FF -r T --split-by-word-count --range-excludes-zero
```

Note that when you use both the `--max_works` and `--end-page` options, it will
stop scraping when either one is met. For example:

```
python3 scrape.py -c FF -r T --max_works 1000000000 --end-page 5
```

will stop at page 5, and will only scrape 100 works (20 per page). But

```
python3 scrape.py -c FF -r T --max_works 10 --end-page 1000
```

will stop at the first page.

If you want to use your own search url, to, for example, search for all F/F works rated
Teen And Up Audiences in the Naruto fandom with a word count between 801-1000, use
the `--from-url` option:

```
python3 scrape.py --from-url https://archiveofourown.org/works/search?utf8=%E2%9C%93&work_search%5Bquery%5D=&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D=&work_search%5Bcomplete%5D=&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bword_count%5D=801-1000&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=Naruto&work_search%5Brating_ids%5D=11&work_search%5Bcategory_ids%5D%5B%5D=116&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=created_at&work_search%5Bsort_direction%5D=asc&commit=Search
```

### Testing

When making changes, it is useful to run it but not for forever, and to not generate a bunch
of `batch_[...].json` files that could possibly confuse the batch collator (see below).
To test out `scrape.py`, use `--test_run`:

```
python3 scrape.py [other options...] --test_run
```

The `--test_run` option automatically sets the max number of works to collect to 100, but
all other options are unaffected. To collect more works, just set `--max_works`.

### Dealing with scrape failures

Since AO3 has limited resources, about 3% of the time, it responds with to HTTP requests
with a page that simply says `Retry later` instead. The program waits 5 seconds between
each request, which limits the number of failed queries, but they still happen now and
then. Since I have yet to determine the optimal amount of time to wait after a failed query
before trying to scrape the same url again, the program saves all failed urls into a
file called `restart_batch_[timestamp_of_batch].txt`, containing each URL separted by a
newline. You can also use `scrape.py` to re-query these URLs, too.

```
python3 scrape.py --from-url-file restart_batch_[timestamp_of_batch].txt
```

This usually results in retrieving the data correctly the second time around. If any of these
fail, however, it will yet again emit another `restart_batch_[timestamp].txt` file that
you can re-try again.


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

### Collating data

Scraped data is saved periodically throughout the scrape, which prevents
the program from accidentally using all of the memory in memory-constrained
situations. (If you're deploying this on a cloud, in order to scrape faster,
this can be handy.) However, that means that you end up with sometimes 50-ish
small files, which is annoying. `batch_utils.py` allows you to collate all
this data together into one file.

To do this, run

```
python3 batch_utils.py collate batch_[timestamp][number].json
```

This automatically puts all of the data for batch files with the same
timestamp into one big file called `batch_[timestamp]_all.json`. It removes
duplicates that may have been accidentally scraped, or scraped in several
different runs of the program. It automatically takes the newest version that
was most recently updated if there are duplicates.

Note: Only call this when `[number]` is in the single digits. Otherwise,
it will not find the other files correctly.

#### Further examples

If you had to do multiple runs to get all of the data, you can run

```
python3 batch_utils.py collate batch_[timestamp][number].json --all
```

which finds all files matching `batch_*.json` whose search criteria match
`batch_[timestamp][number].json`'s search criteria, and puts the data into
one file called `batch_collate_all_[current_timestamp].json`.


## Future Updates
The following are some ideas for features that would be good to implement,
as well as some extra utilities that would be good to have, in no
particular order:

 - set a page increment (useful for splitting up work amongst n many machines, since there's this whole problem of how you can only get the results of one page (20 works) every 5 seconds)
 - add support for other search parameters (pairing, fandom, etc.)
 - add support for negative search parameters (exclude a rating, a pairing, etc.)
 - add support for exists/forall on certain parameters
 - add basic stats support for examining a batch
 - add support for search by language
 - automatically re-try failed URLs

## Disclaimers
Please use responsibly. Also note that occasionally when scraping a search
with many pages, you will run into an issue where the search fails early.
Since the scraper accessing AO3 every 5 seconds, every once in a while AO3
declines to serve any content at all to the scraper, and the only thing
in the page that is served is the message "Retry later"

This usually only happens after at least scraping data from 100 pages of a
search. However, there are workarounds described above.

## Issues, Bug Reports, Pull Requests
I only made this because all of the other (entirely unofficial)
AO3 scrapers were not exactly what I needed. So there may be problems that
I am unaware of because there is literally one person coding all of this.

But, if you would like to contribute further, please submit an issue via
GitHub's issue tracker above, or a pull request if you'd be so kind!
