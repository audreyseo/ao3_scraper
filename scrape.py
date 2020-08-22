import sys
import requests
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import json
import time
import argparse
from ao3_info import ao3_work_search_url, validate_ao3_search_url, save_url_params, get_page_number
#import fandom_scrape
from utils import VerifyPositiveIntAction, eprint
import utils
from urllib.parse import parse_qs
from colors import color
import os
import re

ao3_home = "https://archiveofourown.org"

def is_work(tag):
  #print(tag.prettify())
  return 'class' in tag.attrs and 'work' in tag['class'] and 'blurb' in tag['class'] and 'group' in tag['class']

def has_class(tag):
  return 'class' in tag.attrs

def has_href(tag):
  return 'href' in tag.attrs

def get_title_and_author(work_tag):
  def find_by_index(contents):
    for i in range(len(contents)):
      if str(contents[i]).find("by") >= 0:
        return i
      pass
    return -1
  found = work_tag.find_all("h4")
  found = [f for f in found if has_class(f) and "heading" in f['class']]
  #print("get_title_and_author: found:\n{}".format(found))
  if len(found) == 1:
    parts = found[0].find_all("a")
    if len(parts) == 0:
      # I actually have no idea what to do about this
      return (None, None, None, None)
    # So we know that there's at least 1
    title_tag = parts[0]
    title_href = title_tag["href"] if has_href(title_tag) else None
    title = str(title_tag.string)
    author = None
    author_href = None
    if len(parts) >= 2:
      author_tag = parts[1]
      author_href = author_tag["href"] if has_href(author_tag) else None
      author = str(author_tag.string)
      pass
    elif len(parts) == 1:
      # Probably anonymous
      #print(found[0].contents)
      by_index = find_by_index(found[0].contents)
      
      if by_index > -1 and by_index + 2 < len(found[0].contents):
        if found[0].contents[by_index + 2].find("Anonymous") >= 0:
          author = "Anonymous"
          pass
        pass
      pass
    #else:
    #  print("Too many parts found: {}, in:\n{}".format(parts, work_tag))
    return (title, title_href, author, author_href)
    
  elif len(found) > 1:
    print("More than one title possibility found: {}".format(found))
  else:
    print("Strange, nothing found in work_tag for h4 for title: {}".format(work_tag.prettify()))
      
  return (None, None, None, None)

def has_all_classes(tag, *classes):
  if not has_class(tag):
    return False
  for c in classes:
    if c not in tag['class']:
      return False
  return True

def get_fandoms(work_tag):
  finds = work_tag.find_all("h5")
  finds = [f for f in finds if has_class(f) and has_all_classes(f, "heading", "fandoms")]
  #print(finds)
  if len(finds) == 1:
    fandoms = []
    fandom_tags = finds[0].find_all("a")
    for ft in fandom_tags:
      fandom = str(ft.string)
      fandom_url = (ao3_home + ft['href']) if has_href(ft) else ""
      fandoms.append([fandom, fandom_url])
    return fandoms
  return []

def find_all_of_classes(work_tag, name, *classes):
  finds = work_tag.find_all(name)
  finds = [f for f in finds if has_all_classes(f, *classes)]
  return finds

def find_of_classes(work_tag, name, *classes):
  finds = work_tag.find_all(name)
  finds = [f for f in finds if has_all_classes(f, *classes)]
  if len(finds) >= 1:
    if len(finds) > 1:
      print("multiple finds of {} of classes {} in {}".format(name, classes, work_tag))
    return finds[0]
  #print("0 finds of {} of classes {} in {}".format(name, classes, work_tag))
  return None
def find_completeness(tag):
  find = find_of_classes(tag, "span", "iswip")
  if find is not None:
    return find

def has_title(tag):
  return "title" in tag.attrs
  
def get_required(work_tag):
  finds = find_all_of_classes(work_tag, "ul", "required-tags")
  if len(finds) == 1:
    found = finds[0]
    #print(found)
    ratings_tag = find_of_classes(found, "span", "rating")
    warnings_tag = find_of_classes(found, "span", "warnings")
    categories_tag = find_of_classes(found, "span", "category")
    complete_tag = find_completeness(found)
    rating = ratings_tag['title'] if ratings_tag is not None and has_title(ratings_tag) else "FAILURE"
    warnings = warnings_tag['title'].split(", ") if has_title(warnings_tag) else ["FAILURE"]
    categories = categories_tag['title'].split(", ") if has_title(categories_tag) else ["FAILURE"]
    complete = complete_tag['title'] != "Work in Progress" if complete_tag is not None and has_title(complete_tag) else "FAILURE"
    return (rating, warnings, categories, complete)
  return ("", [], [], False)

def get_last_updated(work_tag):
  find = find_of_classes(work_tag, "p", "datetime")
  if find is not None:
    return str(find.string)
  return ""

def get_tag_info(listing):
  link = find_of_classes(listing, "a", "tag")
  if link is None:
    return ["", ""]
  url = (ao3_home + link["href"]) if has_href(link) else ""
  name = str(link.string)
  #print("tag_info: {}, {}".format(name, url))
  return [name, url]

def get_tags(work_tag):
  find = find_of_classes(work_tag, "ul", "tags", "commas")
  
  relationships = find_all_of_classes(find, "li", "relationships")
  characters = find_all_of_classes(find, "li", "characters")
  tags = find_all_of_classes(find, "li", "freeforms")
  relationships = [get_tag_info(r) for r in relationships]
  characters = [get_tag_info(c) for c in characters]
  tags = [get_tag_info(t) for t in tags]
  return (relationships, characters, tags)


def get_summary(work_tag):
  find = find_of_classes(work_tag, "blockquote", "userstuff", "summary")
  if find is not None:
    return "".join(list(map(lambda x: str(x), find.contents)))
  return ""

def get_string(t):
  if t is not None:
    return str(t.string)
  return ""


def get_stats(work_tag):
  stats = find_of_classes(work_tag, "dl", "stats")
  if stats is not None:
    lang_tag = find_of_classes(stats, "dd", "language")
    words_tag = find_of_classes(stats, "dd", "words")
    chapters_tag = find_of_classes(stats, "dd", "chapters")
    hits_tag = find_of_classes(stats, "dd", "hits")
    lang = get_string(lang_tag)
    words = get_string(words_tag)
    chapters_text = get_string(chapters_tag)
    chs_split = chapters_text.split("/")
    chapters = 0
    max_chapters = -1
    if len(chs_split) == 2:
      chapters = int(chs_split[0])
      max_ch = chs_split[1]
      if max_ch != "?":
        max_chapters = int(max_ch)
    hits = get_string(hits_tag)
    if len(hits) > 0:
      hits = int(hits)
    return (lang, words, chapters, max_chapters, hits)
  return ("FAILURE", "FAILURE", "FAILURE", "FAILURE", "FAILURE")

def abbreviate_soup(soup):
  mystr = str(soup) if not isinstance(soup, str) else soup
  if len(mystr) > 100:
    last_50 = max(51, len(mystr)-50)
    return mystr[:50] + "\n<!-- Omitting lots and lots of HTML and other output... -->\n" + mystr[last_50:]
  return mystr

def get_next_url(soup, page, max_page, num_results):
  def shorten(mystr):
    if len(mystr) > 100:
      last_50 = max(51, len(mystr)-50)
      return mystr[:50] + "\n<!-- Omitting lots and lots of HTML and other output... -->\n" + mystr[last_50:]
    return mystr
  if num_results <= 20 and num_results > -1:
    # It is not a problem that there is no next
    return (None, False)
  elif num_results == -1:
    return (None, True)
  
  find = find_of_classes(soup, "li", "next")
  if find is not None:
    oldFind = find
    find = find.find("a")
    if find is not None:
      if has_href(find):
        return (ao3_home + find['href'], False)
      pass
    else:
      find = find_of_classes(oldFind, "span", "disabled")
      if find is not None:
        return (None, False)
      pass
    pass
  if max_page > -1 and page < max_page:
    print("Uh oh, no more next in soup!:\n{}".format(color(shorten(soup.prettify()), fg="blue")))
    return (None, True)
  else:
    # There probably shouldn't be a next in this case
    print("Did not find next. Please verify if okay:\n{}".format(color(shorten(soup.prettify()), fg="blue")))
    return (None, True)
    
  


def make_entry(title="", title_url="", author="", author_url="", fandom=[], rating="", warnings="", category="", complete=False, last_updated="", relationships=[], characters=[], tags=[], summary="", language="", words=0, chapters=0, max_chapters=-1, hits=0):
  title_url = ao3_home + title_url if title_url is not None else ""
  author_url = ao3_home + author_url if author_url is not None else ""
  return {
    "title": title,
    "title_url": title_url,
    "author": author,
    "author_url": author_url,
    "fandom": fandom,
    "rating": rating,
    "warnings": warnings,
    "category": category,
    "complete": complete,
    "last_updated": last_updated,
    "relationships": relationships,
    "characters": characters,
    "tags": tags,
    "summary": summary,
    "language": language,
    "words": words,
    "chapters": chapters,
    "max_chapters": max_chapters,
    "hits": hits
  }

searchable_parameters = ["rating", "warnings", "category"]
searchables_to_params_dict_keys = {
  "rating": "rating",
  "warnings": "warning",
  "category": "category"
}

ao3_params_to_searchables = {
  "rating_ids": "rating",
  "category_ids": "category",
  "archive_warning_ids": "warnings"
}

def find_num_results(soup):
  results_found = re.compile("\s*(\d+)\s+Found\s*")
  candidates = find_all_of_classes(soup, "h3", "heading")
  candidates = [c for c in candidates if has_class(c) and len(c["class"]) == 1]
  if len(candidates) == 1:
    candidate = candidates[0]
    for c in candidate.contents:
      #print(c)
      if results_found.match(str(c)):
       # print("Found match: {}".format(c))
        num_results = results_found.sub(r"\1", str(c))
        #print("Results found: {}".format(num_results))
        return int(num_results)
  print(color("Warning: could not find number of results", fg="red"))
  #print("strings length: {}".format(len(candidates)))
  #print("strings: {}".format(candidates))
  return -1

def find_max_page(soup):
  def find_next_index(li_list):
    for i in range(len(li_list)):
      if has_class(li_list[i]):
        if "next" in li_list[i]["class"]:
          return i
        pass
      pass
    return -1
  if isinstance(soup, str):
    # in this case, soup is content instead
    soup = BeautifulSoup(soup, "html.parser")
    '''if len(soup.attrs.keys()) == 0:
      # Houston, we have a problem
      # This is most likely a case of "Retry later"
      eprint("Warning: soup is weirdly empty.")
      print("Abbreviated soup:\n{}".format(color(abbreviate_soup(soup), fg="blue")))
      return -1'''
  num_results = find_num_results(soup)
  if num_results > -1 and num_results <= 20:
    return 1
  paginations = find_all_of_classes(soup, "ol", "pagination", "actions")
  if len(paginations) >= 1:
    assert len(paginations) == 1
    pages = paginations[0]("li")
    next_index = find_next_index(pages)
    last_page_index = next_index - 1
    last_page = pages[last_page_index]
    inside = last_page.find("a")
    inside = inside if inside is not None else last_page.find("span")
    # inside should have a string if it isn't none
    return -1 if inside is None else int(str(inside.string))
  print("Found no paginations, so either an error occurred or this is the only page, or both.")
  return 1



def search_start(contents, works, page):
  '''Given the contents as a string of a search page and an array for works,
     returns the next url in the sequence of url's to look at, and whether or
     not the next url being None is a problem (if the next url is None and
     the bool is false, then there is no problem, i.e. this was the last page
     in the search. If the next url is None and the bool is True, then
     there must have been some sort of issue with parsing the page.
  '''
  soup = BeautifulSoup(contents, "html.parser")
  max_page = find_max_page(soup)
  num_results = find_num_results(soup)
  
  
  
  #print("Max page: {}".format(find_max_page(soup)))
  
  #print(soup.prettify())
  raw_works = soup.find_all("li")
  raw_works = [t for t in raw_works if is_work(t)]
  #print(raw_works)
  for w in raw_works:
    title, title_link, author, author_link = get_title_and_author(w)
    fandoms = get_fandoms(w)
    rating, warnings, categories, complete = get_required(w)
    last_updated = get_last_updated(w)
    relationships, characters, tags = get_tags(w)
    summary = get_summary(w)
    language, words, chapters, max_chapters, hits = get_stats(w)
    #print(title, title_link, author, author_link)
    
    #print(fandoms)
    #print(rating, warnings, categories, complete)
    #print(last_updated)
    #print(relationships, characters, tags)
    #print(summary)
    #print(language, words, chapters, max_chapters, hits)
    works.append(make_entry(title=title,
                            title_url=title_link,
                            author=author,
                            author_url=author_link,
                            fandom=fandoms,
                            rating=rating,
                            warnings=warnings,
                            category=categories,
                            complete=complete,
                            last_updated=last_updated,
                            relationships=relationships,
                            characters=characters,
                            tags=tags,
                            summary=summary,
                            language=language,
                            words=words,
                            chapters=chapters,
                            max_chapters=max_chapters,
                            hits=hits))
  #return (next_url, problem, max_page)
  next_url, problem = get_next_url(soup, page, max_page, num_results)
  return (next_url, problem)



def scrape_search_pages(content, params_dict, batch_name, max_works, restart_from_file=None, url_list=[],
                        end_page=-1):
  works = []
  using_from_file = len(url_list) > 0
  using_max_works = max_works > 0
  using_end_page = end_page > 0
  num_urls = -1 if not using_from_file else (len(url_list) + 1)
  # make sure that params_dict is inside of works
  # so it's a part of the data that gets written
  works.append(params_dict)
  page = params_dict["page"]
  if using_end_page and page > end_page:
    # Problematic since we're already starting off past what we meant to
    eprint("Error: cannot use an end_page {} that is smaller than the starting page number {}".format(end_page, page))
    eprint("       Please check that the commandline arguments you entered were correct.")
    return

  max_page_number = find_max_page(content)
  num_results = find_num_results(BeautifulSoup(content, "html.parser"))
  pages_to_retry = []
  failed_problematically = False
  attempts_left = -1
  if num_results > 100000:
    # AO3 only displays 100,000 results, max
    print(color("Warning: this search has {} results, but only the first 100,000 can be scraped. Conisder narrowing your search if you want to scrape all of them.".format(num_results), fg="red"))
  next_url, problem = search_start(content, works, page)
  # I just added this if statement on Friday, Aug 21 2020
  # why was this not here earlier goddddd
  if using_from_file:
    if len(url_list) > 0:
      next_url = url_list.pop(0)
      pass
    pass
  elif problem or num_results < 0:
    # Bad times
    if next_url is None:
      eprint("Error: Problem with finding next_url: Is Problem: {}, Num Results: {}".format(problem, num_results))
      eprint("Attempting to just try the next page number, {}".format(page + 1))
      eprint("If the next 75 consecutive attempts fail, then this search will terminate.")
      eprint("Stop it at any time by using CTRL-C")
      failed_problematically = True
      attempts_left = 75
      next_url = ao3_work_search_url(category_ids=params_dict["category"],
                                     rating_ids=params_dict["rating"],
                                     archive_warning_ids=params_dict["warning"],
                                     page=page + 1,
                                     word_count=params_dict["query"])
      # Add the current URL to the list of URLs to retry next time
      pages_to_retry.append(params_dict["url"])
  counter = 1
  dumps = 0
  num_works = 0
  def get_num_collected():
    return (len(works) - 1) + num_works

  def not_done_yet():
    return max_works <= 0 or get_num_collected() < max_works

  if using_end_page and page >= end_page:
    # Stopping before we enter the loop
    # Honestly I don't know why you would have it do exactly one page but I'm not going to judge
    next_url = None
    pass
  
  if using_from_file:
    if next_url != None:
      page = get_page_number(next_url)
      pass
    pass
  else:
    if max_page_number <= 0 or page <= max_page_number:
      page += 1
      pass
    elif max_page_number > 0 and page > max_page_number:
      # We need to stop
      eprint("Went past the last recorded maximimum page number, {}".format(max_page_number))
      eprint("Quitting now...")
      next_url = None
    pass
  # assume the worst, lol
  old_next_url = ""

  def write_to_restart_from_file(url_to_write):
    if restart_from_file is not None:
      with open(restart_from_file, "a") as f:
        f.write(url_to_write + "\n")
        f.flush()
        pass
      pass
    pass

  def write_to_restart_from_file(urls_to_write):
    if restart_from_file is not None and len(urls_to_write) > 0:
      with open(restart_from_file, "a") as f:
        f.write("\n".join(urls_to_write) + "\n")
        f.flush()
        pass
      pass
    elif len(urls_to_write) == 0:
      print("No urls to restart")
    pass

  
  
  while next_url is not None and not_done_yet():

    # Need try catch since sometimes it doesn't work right
    try:
      # 5 seconds in between requests, per AO3 terms of service
      # had to reference another implementation:
      # https://github.com/radiolarian/AO3Scraper/blob/master/ao3_work_ids.py
      # to figure this out
      # Though I also could no longer find any reference to this in the AO3
      # terms of service anymore (though I could have sworn it used to be in there)
      time.sleep(5)
      res1 = requests.get(next_url, headers=headers)
      content = res1.text
      old_next_url = next_url
      next_url, isProblem = search_start(content, works, page)

      failing_out = False
      if failed_problematically and next_url is None and isProblem:
        attempts_left -= 1
        if attempts_left <= 0:
          # Prevent it from trying to assign a next_url.
          failing_out = True
          pass
        pass
      elif next_url is not None and failed_problematically:
        # Don't need to worry anymore
        failed_problematically = False
        attempts_left = -1
        pass
      
      if next_url is None and (not using_from_file or isProblem) and not failing_out:
        print("Last page!: {}".format(old_next_url))
        if isProblem:
          print("Left off trying to get page number {}".format(page))
          # TRYING THIS, DUNNO IF IT WILL WORK
          pages_to_retry.append(old_next_url)
          if max_page_number > 0 and page + 1 <= max_page_number and not using_from_file:
            next_url = ao3_work_search_url(category_ids=params_dict["category"],
                                           rating_ids=params_dict["rating"],
                                           archive_warning_ids=params_dict["warning"],
                                           page=page + 1,
                                           word_count=params_dict["query"])
            pass
          elif using_from_file and len(url_list) > 0:
            next_url = url_list.pop(0)
          pass
        pass
      elif using_from_file:
        # Change next_url to the next url
        if len(url_list) > 0:
          next_url = url_list.pop(0)
          pass
        else:
          # We're done
          next_url = None
      
      counter += 1

      if (counter % 5) == 0 or page >= max_page_number - 10:
        new_max = find_max_page(content)
        if new_max > 0 and new_max > max_page_number:
          print("Updating max page number from {} to {}...".format(max_page_number, new_max))
          max_page_number = new_max

      if using_end_page and page >= end_page:
        # STOP, we've already done the last page
        # This also affects urls_from_file too btw
        #print("Page: {}, End page: {}".format(page, end_page))
        print("Page number {} is greater than or equal to end_page {}. Quitting now.".format(page, end_page))
        next_url = None
        pass
      
      # Update the page number
      if using_from_file:
        if next_url != None:
          page = get_page_number(next_url)
          pass
        pass
      else:
        page += 1
        pass

      
        
      
      if using_max_works and get_num_collected() >= max_works:
        # STOP
        next_url = None
        print("Went over maximum {} by {} works".format(max_works, get_num_collected() - max_works))
        while get_num_collected() > max_works:
          print("Popping off: {}".format(works.pop(len(works) - 1)))
          pass
        pass

      
      
      if (counter % 5) == 0:
        if not using_from_file:
          print("Done with {}, finished page number {}".format(counter, ("{} out of {}".format(page-1, max_page_number)) if max_page_number > 0 else (page - 1)))
          pass
        else:
          print("Done with {} out of {}".format(counter, num_urls))
        pass
      if (counter % 100) == 0:
        #print("Done with {}".format(counter))
        with open("{}{}.json".format(batch_name, dumps), "w") as f:
          f.write(json.dumps(works, indent="  "))
          f.flush()
          pass
        
        dumps += 1
        num_works += len(works) - 1
        works = [params_dict]
        pass
      pass
    except requests.exceptions.ConnectionError:
      eprint("Connection error occurred while accessing page: {}".format(next_url))
      #if not using_from_file:
      eprint("Last page attempted: {}".format(page))
      pages_to_retry.append(old_next_url)
      # Make the loop condition invalid
      next_url = None
      pass
    except KeyboardInterrupt:
      print("")
      eprint(color("Program interrupted.", fg="red"))
      eprint("Scraped {} works".format(get_num_collected()))
      eprint("Left off at page:\n{}".format(next_url))
      #if not using_from_file:
      eprint("Page number last attempted: {}".format(page))
      # make the loop condition invalid
      next_url = None
      eprint("Quitting now...")
      pass
    except:
      eprint("Some other error occurred. Please try again.")
      eprint("next_url: {}".format(next_url))
      eprint("old_next_url: {}".format(old_next_url))
      #if not using_from_file:
      eprint("Last page attempted: {}".format(page))
      pages_to_retry.append(old_next_url)
      # Make the loop condition invalid
      next_url = None
      pass
    pass
  num_works += len(works) - 1
  with open("{}{}.json".format(batch_name, dumps), "w") as f:
    f.write(json.dumps(works, indent="  "))
    f.flush()
    pass
  write_to_restart_from_file(pages_to_retry)
  print("Num works: {}".format(num_works))
  pass

def get_argument_parser():
  # Commandline arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("-c", "--category",
                      nargs="*",
                      default=["FF"],
                      help=("List (without commas) of any of FF, MM"\
                            ", FM, Gen, Multi, or Other"))
  parser.add_argument("-r", "--rating",
                      default="",
                      help=("Rating, if any, of content. Valid values "\
                            "are G, T, M, E, and NR"))
  parser.add_argument("-w", "--warning",
                      nargs="*",
                      default=[],
                      help=("List (without commas) of any of NAWA "\
                            "(No Archive Warnings Apply), RNC (Rape/Non-Con), "\
                            "MCD (Major Character Death), CNTUAW "\
                            "(Choose Not To Use Archive Warnings), and Underage"))
  parser.add_argument("-p", "--page",
                      default=1,
                      type=int,
                      action=VerifyPositiveIntAction,
                      help="Which page of the search to start from")
  # --end_page, --page_increment aren't actually being implemented at the moment
  # But they're here so that I can actually do something with them
  # soon hopefully
  parser.add_argument("-e", "--end-page",
                      default=-1,
                      type=int,
                      action=VerifyPositiveIntAction,
                      help="Which page to stop at. Use -1 to go to the end")
  parser.add_argument("-m", "--max_works",
                      default=-1,
                      type=int,
                      action=VerifyPositiveIntAction,
                      help="How many works' stats to include. -1 means all possible.")
  parser.add_argument("--page_increment",
                      default=1,
                      type=int,
                      help=("Collect every nth page from a search, "\
                            "defaults to 1, i.e. collecting every page from a search."))
  parser.add_argument("--split_by",
                      default="none",
                      choices=["none", "fandoms"],
                      help=("Split a search over every searchable tag. "\
                            "Currently only supports search over all "\
                            "fandoms. (This helps to make a broad search more tractable)"))
  parser.add_argument("--test_run",
                      action="store_true",
                      help=("Run a test by only collecting the first "\
                            "100 works. Saves the resulting scraped "\
                            "data to a file(s) named test_[timestamp][number].json. "\
                            "To collect more or less works for your test "\
                            "run, set using -m/--max_works."))
  parser.add_argument("-u", "--from-url",
                      default="",
                      help=("Use a given url to start a search. This effectively "\
                            "ignores the commandline options --rating, "\
                            "--warning, --category, and --page. However --max_works/-m "\
                            "should still function as normal. Also note that this will "\
                            "alter what shows up in the params saved at the beginning of "\
                            "every batch file. Only parameters that can be altered via "\
                            "these command line optinos will be saved there."))
  parser.add_argument("--from-url-file",
                      default="",
                      help=("Takes files either ending with .json or .txt. If ending in "\
                            ".json, the program expects that the object contained will "\
                            "have entries named \"params_dict\" and \"urls\", containing "\
                            "a dictionary of the parameters that should be assigned to the "\
                            "batch and a list of AO3 search URLs to scrape, respectively. "\
                            "If it's a text file, the program expects just a list of AO3 "\
                            "search URLs in the file. Note that as in --from-url, any "\
                            "search parameters set using commandline options --rating, "\
                            "--warning, etc. will be ignored. But additionally, --from-url "\
                            "will also be ignored."))
  parser.add_argument("--split-by-word-count", action="store_true",
                      help=("Uses a chosen parameter to split the search over. This helps to "\
                            "perform searches that would otherwise have more than 100,000 "\
                            "results, and scrape all the data. The only valid choice at the "\
                            "moment is to split by word counts."))
  parser.add_argument("--ranges",
                      nargs="*",
                      action=utils.VerifyPositiveIntListAction,
                      default=[200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2600, 2800, 3200, 3600, 4000, 4400, 4800, 5400, 6000, 6600, 7400, 8000, 9000, 10000, 12000, 20000, 30000, 40000],
                      help=("Used with --split-by. Defaults to splitting word count by a distribution that makes every query less than 10,000 results (often, much less), for F/F with the rating Teen Up And Audiences. Takes a list of positive integers. Note that it automatically processes 0 as being the first element, and for the last number, it will do a search for >[last number] at the very end. Additionally, if the values aren't sorted, it will do that for you anyway: from smallest to largest."))
  parser.add_argument("--range-excludes-zero", action="store_true",
                      help=("Used with --ranges. If you enter --ranges n1 n2 n3 n4 n5, it would usually make ranges 0-n1, (n1+1)-n2, (n2+1)-n3, (n3+1)-n4, (n4+1)-n5, and >n5. But with the --range-excludes-zero option, it makes ranges (n1+1)-n2 and onward. Useful for restarting a query for splits."))
  parser.add_argument("--range-from-file",
                      default=None,
                      help=("Used instead of the --ranges argument. Takes in a file containing numbers separated by newlines, and then that basically becomes the contents of the --ranges argument, essentially."))
  return parser

def get_timestamp():
  fetch_time = time.ctime(time.time())
  fetch_time = fetch_time.replace(":", ".")
  # Get rid of pesky spaces in batch file names
  fetch_time = fetch_time.replace(" ", "_")
  return fetch_time

def get_url_list(params_dict, from_url_file):
  url_list = []
  is_json = from_url_file.endswith(".json")
  if os.path.exists(from_url_file):
    succeeded = True
    obj = {}
    with open(from_url_file, "r") as f:
      text = f.read()
      if is_json:
        obj = json.loads(text)
        if "params_dict" in obj and "urls" in obj:
          params_dict = obj["params_dict"]
          params_dict["loaded_from_url_file"] = True
          url_list = obj["urls"]
          pass
        else:
          succeeded = False
          pass
        pass
      else:
        # is .txt
        lines = text.split("\n")
        url_list = [l for l in lines if l != ""]
        pass
      pass
    if not succeeded:
      print("Make sure that \"params_dict\" and \"urls\" are both entries in your url file {}".format(from_url_file))
      print("Could not find one of them. Please try again.")
      sys.exit()
      pass
    old_url_list = url_list
    url_list = [u for u in url_list if validate_ao3_search_url(u)]
    if len(old_url_list) > len(url_list):
      print("Please note that {} out of {} of the urls in the file {} were invalid.".format(len(old_url_list) - len(url_list), len(old_url_list), args.from_url_file))
      print("Invalid URLs:\n{}".format("\n".join([u for u in old_url_list if u not in url_list])))
      print("Continuing without processing invalid URLs...")
      pass
    if len(url_list) == 0:
      print("Did not find any URLs in file {}".format(args.from_url_file))
      print("Please check that you input the right file and try again.")
      sys.exit()
      pass
    pass
  else:
    # file does not exist, which is a Big Problem
    print("Error - Could not find url file {}".format(args.from_url_file))
    sys.exit()
    pass
  return url_list
if __name__ == '__main__':
  parser = get_argument_parser()
  
  args = parser.parse_args()
  
  params_dict = {
    "category": args.category,
    "rating": args.rating,
    "warning": args.warning,
    "page": args.page,
    "end_page": args.end_page,
    "max_works": args.max_works,
    "page_increment": args.page_increment,
    "split_by": args.split_by,
    "test_run": args.test_run,
    "from_url": args.from_url,
    "from_url_file": args.from_url_file,
    "split_by_word_count": args.split_by_word_count,
    "ranges": args.ranges,
    "range_excludes_zero": args.range_excludes_zero,
    "range_from_file": args.range_from_file
  }

  # Needs this just in case, because I realized scrape_search_pages was accessing
  # this without even checking to see if it was in there
  # I'm honestly surprised this hasn't come up as an issue before.
  params_dict["query"] = ""

  if args.range_from_file is not None and not args.split_by_word_count:
    eprint("Error: used --range-from-file without specifying --split-by-word-count.")
    eprint("Exiting.")
    sys.exit()
    pass

  using_from_url = len(args.from_url) > 0
  using_from_file = len(args.from_url_file) > 0
  url_list = []
  if using_from_file and (args.from_url_file.endswith(".json") or args.from_url_file.endswith(".txt")):
    # Ignore args.from_url
    using_from_url = False
    url_list = get_url_list(params_dict, args.from_url_file)
    print("Found {} urls".format(len(url_list)))
    pass
  elif using_from_file:
    print("Error - Files passed to --from-url-file must end in .json or .txt, but found {}".format(args.from_url_file))
    sys.exit()
    pass
  

  if using_from_url and not validate_ao3_search_url(args.from_url):
    print(("The url \"{}\" is not a valid AO3 search url. "\
           "Please make sure it is correct and try again.").format(args.from_url))
    print("Exiting now.")
    sys.exit()
    pass
  word_count_queries = []
  if using_from_file:
    params_dict["urls_from_file"] = url_list
  url = ""
  if not args.split_by_word_count:
    url = ao3_work_search_url(category_ids=args.category,
                              rating_ids=args.rating,
                              archive_warning_ids=args.warning,
                              page=int(args.page)) if not using_from_url and not using_from_file else (args.from_url if using_from_url else url_list.pop(0))
  else:
    #word_count_queries = []
    ranges = args.ranges
    if args.range_from_file is not None:
      if os.path.exists(args.range_from_file):
        with open(args.range_from_file, "r") as f:
          ranges = (f.read()).split("\n")
          pass
        try:
          ranges = [int(r) for r in ranges if len(r) > 0]
          pass
        except ValueError:
          eprint("Expected the file {} to contain positive integers, but found {}".format(args.range_from_file, ranges))
          eprint("Exiting. Please check the file again.")
          sys.exit()
          pass
        else:
          ranges = sorted(ranges)
          if any(r <= 0 for r in ranges):
            eprint("Expected only positive integers for a range, but found zeros/negatives: {}".format(ranges))
            eprint("Exiting. Please try again.")
            sys.exit()
            pass
          # Replace the ranges attribute
          params_dict["ranges"] = ranges
          pass
    if len(ranges) > 0:
      if not args.range_excludes_zero:
        word_count_queries.append("0-{}".format(ranges[0]))
        pass
      for i in range(1, len(ranges)):
        i1 = int(ranges[i-1]) + 1
        i2 = int(ranges[i])
        word_count_queries.append("{}-{}".format(i1, i2))
        pass
      word_count_queries.append(">{}".format(ranges[len(ranges)-1]))
      url_list = [ao3_work_search_url(category_ids=args.category,
                                      rating_ids=args.rating,
                                      archive_warning_ids=args.warning,
                                      word_count=w) for w in word_count_queries]
      #url = url_list.pop(0)
      pass
    pass
  
  
  # Save params url into params dict for good ole replicability purposes
  if not using_from_file:
    params_dict["url"] = url
    pass
    
  if using_from_url or using_from_file:
    if "loaded_from_url_file" not in params_dict or not params_dict["loaded_from_url_file"]:
      save_url_params(params_dict, url)
      pass
    elif using_from_file:
      # Just save page number actually
      save_url_params(params_dict,
                      url,
                      save_rating_ids=False,
                      save_category_ids=False,
                      save_archive_warning_ids=False)
    pass

  # too much info lmao if there's a lot of urls
  if not using_from_file:
    print(params_dict)
    pass
  #content = ""
  headers = {'user-agent' : ''}
  max_works = args.max_works
  max_works = 100 if args.test_run and max_works < 0 else max_works
  if args.split_by_word_count:
    counter = 0
    word_count_file_names = [query.replace(">", "gt").replace("<", "lt") for query in word_count_queries]
    while len(url_list) > 0:
      url = url_list.pop(0)
      print("Fetching {}".format(url))
      try:
        time.sleep(5)
        res = requests.get(url, headers=headers)
      except requests.exceptions.ConnectionError as e:
        print("Got an connection error {}".format(e))
        print("Going on now...")
        pass
      except requests.exceptions.RequestException as e:
        print("Got a request exception {}".format(e))
        print("Going on now...")
        pass
      else:
        fetch_time = get_timestamp()
        batch_name = ("batch_" if not args.test_run else "test_") + word_count_file_names[counter] + "_" + fetch_time
        restart_from_file = "restart_" + batch_name + ".txt"
        params_dict["fetch_time"] = fetch_time
        params_dict["url"] = url
        params_dict["query"] = word_count_queries[counter]
        content = res.text
        scrape_search_pages(content,
                            params_dict,
                            batch_name,
                            max_works,
                            restart_from_file=restart_from_file,
                            end_page=args.end_page)
        #if len(url_list) == 0:
        #  break
        #url = url_list.pop(0)
        counter += 1
        pass
      pass
    print("Done with {} split batches. Exiting...".format(len(word_count_queries)))
    sys.exit()
    pass
  
        
        
        
  #headers = {'user-agent' : ''}
  res = requests.get(url, headers=headers)
  fetch_time = get_timestamp()
  batch_name = "batch_" + fetch_time if not args.test_run else "test_" + fetch_time
  restart_from_file = "restart_" + batch_name + ".txt"
  params_dict["fetch_time"] = fetch_time
  content = res.text
  
  scrape_search_pages(content,
                      params_dict,
                      batch_name,
                      max_works,
                      restart_from_file=restart_from_file,
                      url_list=url_list,
                      end_page=args.end_page)
