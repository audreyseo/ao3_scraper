import sys
import requests
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import json
import time
import argparse
from ao3_info import ao3_work_search_url

ao3_home = "https://archiveofourown.org"

def is_work(tag):
  #print(tag.prettify())
  return 'class' in tag.attrs and 'work' in tag['class'] and 'blurb' in tag['class'] and 'group' in tag['class']

def has_class(tag):
  return 'class' in tag.attrs

def has_href(tag):
  return 'href' in tag.attrs

def get_title_and_author(work_tag):
  found = work_tag.find_all("h4")
  found = [f for f in found if has_class(f) and "heading" in f['class']]
  #print(found)
  if len(found) == 1:
    parts = found[0].find_all("a")
    if len(parts) >= 2:
      title_tag = parts[0]
      author_tag = parts[1]
      title_href = title_tag["href"] if has_href(title_tag) else None
      author_href = author_tag["href"] if has_href(author_tag) else None
      title = str(title_tag.string)
      author = str(author_tag.string)
      return (title, title_href, author, author_href)
    #else:
    #  print("Too many parts found: {}, in:\n{}".format(parts, work_tag))
    pass
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

def get_next_url(soup):
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
  print("Uh oh, no more next in soup!:\n{}".format(soup.prettify()))
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



def search_start(contents, works):
  '''Given the contents as a string of a search page and an array for works,
     returns the next url in the sequence of url's to look at, and whether or
     not the next url being None is a problem (if the next url is None and
     the bool is false, then there is no problem, i.e. this was the last page
     in the search. If the next url is None and the bool is True, then
     there must have been some sort of issue with parsing the page.
  '''
  soup = BeautifulSoup(contents, "html.parser")
  next_url, problem = get_next_url(soup)
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
  return (next_url, problem)
    
#def search_next(contents, works)


if __name__ == '__main__':
  # Commandline arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("-c", "--category", nargs="*", default=["FF"], help="List (without commas) of any of FF, MM, FM, Gen, Multi, or Other")
  parser.add_argument("-r", "--rating", default="", help="Rating, if any, of content. Valid values are G, T, M, E, and NR")
  parser.add_argument("-w", "--warning", nargs="*", default=[], help="List (without commas) of any of NAWA (No Archive Warnings Apply), RNC (Rape/Non-Con), MCD (Major Character Death), CNTUAW (Choose Not To Use Archive Warnings), and Underage")
  parser.add_argument("-p", "--page", default=1, help="Which page of the search to start from")
  # These aren't actually being implemented at the moment
  # But they're here so that I can actually do something with them
  # soon hopefully
  parser.add_argument("-e", "--end_page", default=-1, help="Which page to stop at. Use -1 to go to the end")
  parser.add_argument("-m", "--max_works", default=-1, help="How many works' stats to include. -1 means all possible.")
  parser.add_argument("--page_increment", default=1, help="Collect every nth page from a search, defaults to 1, i.e. collecting every page from a search.")
  
  args = parser.parse_args()

  params_dict = {
    "category": args.category,
    "rating": args.rating,
    "warning": args.warning,
    "page": args.page,
    "end_page": args.end_page,
    "max_works": args.max_works,
    "page_increment": args.page_increment
  }
  print(params_dict)
  
  url = ao3_work_search_url(category_ids=args.category, rating_ids=args.rating, archive_warning_ids=args.warning, page=int(args.page))

  # Save params url into params dict for good ole replicability purposes
  params_dict["url"] = url
  '''print(len(sys.argv) >= 2)
  if len(sys.argv) >= 2:
    url = sys.argv[1]
    pass
  else:
    #url = "https://archiveofourown.org/works/search?utf8=✓&work_search%5Bquery%5D=&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D=&work_search%5Bcomplete%5D=&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bword_count%5D=&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=&work_search%5Brating_ids%5D=&work_search%5Bcategory_ids%5D%5B%5D=23&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=_score&work_search%5Bsort_direction%5D=desc&commit=Search"
    url = "https://archiveofourown.org/works/search?utf8=✓&work_search%5Bquery%5D=&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D=&work_search%5Bcomplete%5D=&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bword_count%5D=&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=&work_search%5Brating_ids%5D=&work_search%5Bcategory_ids%5D%5B%5D=116&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=_score&work_search%5Bsort_direction%5D=desc&commit=Search"'''
  content = ""
  #split_url = list(urllib.parse.urlsplit(url))
  #print(split_url)
  #if len(split_url) > 1:
  #  split_url[3] = urllib.parse.quote(split_url[3])
  #  url = urllib.parse.urlunsplit(split_url)
  #print(url)
  headers = {'user-agent' : ''}
  res = requests.get(url, headers=headers)
  fetch_time = time.ctime(time.time())
  fetch_time = fetch_time.replace(":", ".")
  batch_name = "batch_" + fetch_time
  params_dict["fetch_time"] = fetch_time
  content = res.text
  works = []
  # make sure that params_dict is inside of works
  # so it's a part of the data that gets written
  works.append(params_dict)
  next_url, problem = search_start(content, works)
  counter = 1
  dumps = 0
  num_works = 0
  page = int(args.page) + 1
  while next_url is not None:
    # 5 seconds in between requests, per AO3 terms of service
    # had to reference another implementation:
    # https://github.com/radiolarian/AO3Scraper/blob/master/ao3_work_ids.py
    # to figure this out
    time.sleep(5)
    try:
      res1 = requests.get(next_url, headers=headers)
      content = res1.text
      old_next_url = next_url
      next_url, isProblem = search_start(content, works)
      if next_url is None:
        print("Last page!: {}".format(old_next_url))
        if isProblem:
          print("Left off trying to get page number {}".format(page))
      counter += 1
      page += 1
      if (counter % 5) == 0 and (counter % 100) != 0:
        print("Done with {}".format(counter))
        pass
      elif (counter % 100) == 0:
        print("Done with {}".format(counter))
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
      print("Connection error occurred while accessing page: {}".format(next_url))
      print("Last page attempted: {}".format(page))
      # Make the loop condition invalid
      next_url = None
    except:
      print("Some other error occurred. Please try again.")
      print("next_url: {}".format(next_url))
      print("old_next_url: {}".format(old_next_url))
      print("Last page attempted: {}".format(page))
  num_works += len(works) - 1
  with open("{}{}.json".format(batch_name, dumps), "w") as f:
    f.write(json.dumps(works, indent="  "))
    f.flush()
  print(num_works)
