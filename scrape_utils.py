from bs4 import BeautifulSoup
import re

ao3_home = "https://archiveofourown.org"

def is_work(tag):
  #print(tag.prettify())
  return 'class' in tag.attrs and 'work' in tag['class'] and 'blurb' in tag['class'] and 'group' in tag['class']


def has_class(tag):
  return 'class' in tag.attrs


def has_href(tag):
  return 'href' in tag.attrs

def has_all_classes(tag, *classes):
  if not has_class(tag):
    return False
  for c in classes:
    if c not in tag['class']:
      return False
  return True


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

def has_title(tag):
  return "title" in tag.attrs

def get_tag_info(listing):
  link = find_of_classes(listing, "a", "tag")
  if link is None:
    return ["", ""]
  url = (ao3_home + link["href"]) if has_href(link) else ""
  name = str(link.string)
  #print("tag_info: {}, {}".format(name, url))
  return [name, url]


def get_string(t):
  if t is not None:
    if t.string is not None:
      return str(t.string)
    pass
  return ""

def abbreviate_soup(soup):
  mystr = str(soup) if not isinstance(soup, str) else soup
  if len(mystr) > 100:
    last_50 = max(51, len(mystr)-50)
    return mystr[:50] + "\n<!-- Omitting lots and lots of HTML and other output... -->\n" + mystr[last_50:]
  return mystr


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
