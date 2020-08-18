from bs4 import BeautifulSoup
import requests
import os
from scrape import find_all_of_classes, ao3_home, has_href
import re
import json
import time

fandom_urls = {
  "Anime & Manga": "https://archiveofourown.org/media/Anime%20*a*%20Manga/fandoms",
  "Books & Literature": "https://archiveofourown.org/media/Books%20*a*%20Literature/fandoms",
  "Cartoons & Comics & Graphic Novels": "https://archiveofourown.org/media/Cartoons%20*a*%20Comics%20*a*%20Graphic%20Novels/fandoms",
  "Celebrities & Real People": "https://archiveofourown.org/media/Celebrities%20*a*%20Real%20People/fandoms",
  "Movies": "https://archiveofourown.org/media/Movies/fandoms",
  "Music & Bands": "https://archiveofourown.org/media/Music%20*a*%20Bands/fandoms",
  "Other Media": "https://archiveofourown.org/media/Other%20Media/fandoms",
  "Theater": "https://archiveofourown.org/media/Theater/fandoms",
  "TV Shows": "https://archiveofourown.org/media/TV%20Shows/fandoms",
  "Video Games": "https://archiveofourown.org/media/Video%20Games/fandoms"#,
# Commented out since none of the fandoms on this page are actually used
#  "Uncategorized Fandoms": "https://archiveofourown.org/media/Uncategorized%20Fandoms/fandoms"
}

def get_fandom_info(tag):
  # tag should be the li tag holding the entirety of the info about the tag
  a_tag = tag.find("a")
  if a_tag is None:
    return None, None, None
  name = str(a_tag.string)
  url = ""
  if has_href(a_tag):
    url = ao3_home + a_tag["href"]
    pass
  countstring = ""
  #print(tag.contents)
  for c in tag.contents:
    if re.match(r"\s*\(\d+\)\s*", str(c)):
      countstring = str(c)
      pass
    pass
  #print("countstring: {}".format(countstring))
  count = 0
  if re.match(r"\s*\(\d+\)\s*", countstring):
    countstring = re.sub(r'\s*\((\d+)\)\s*', r"\1", countstring)
    #print("countstring: {}".format(countstring))
    count = int(countstring)
  return name, url, count

def scrape_fandom_names(content):
  soup = BeautifulSoup(content, features="html.parser")
  indices = find_all_of_classes(soup, "ul", "tags", "index", "group")
  entries = []
  for i in indices:
    lis = i.find_all("li")
    for li in lis:
      name, url, count = get_fandom_info(li)
      if name is not None:
        entries.append({
          "name": name,
          "url": url,
          "count": count})
        pass
      else:
        print("Could not find fandom info in:\n{}".format(li.prettify()))
        pass
      pass
    if len(lis) == 0:
      print("Could not find any fandom listings in:\n{}".format(i.prettify()))
      pass
    pass
  return entries

fandom_info_json_name = "fandom_info.json"
fandom_names_json_name = "fandom_names.json"

def scrape_all_fandoms():
  entries = []
  headers = {'user-agent' : ''}
  for name, url in fandom_urls.items():
    print("Scraping fandom names for {}".format(name))
    try:
      res = requests.get(url, headers)
      entries += scrape_fandom_names(res.text)
      pass
    except requests.exceptions.ConnectionError:
      print("requests.exceptions.ConnectionError occurred while accessing page {}".format(url))
      # Break out of the loop
      break
    pass
  return entries

def save_fandoms():
  names = scrape_all_fandoms()
  # make a timestamp
  fetch_time = time.ctime(time.time())
  # put the timestamp in an object with the names
  info = {
    "last_updated": fetch_time,
    "info": names
  }
  
  print("Writing all fandom info...")
  with open(fandom_info_json_name, "w") as f:
    f.write(json.dumps(info, indent="  "))
    f.flush()
    pass
  print("Writing fandom names list...")
  just_names = {
    "names": [n["name"] for n in names],
    "last_updated": fetch_time
  }
  with open(fandom_names_json_name, "w") as f:
    f.write(json.dumps(just_names, indent="  "))
    f.flush()
    pass
  pass

if __name__ == '__main__':
  save_fandoms()
  pass
