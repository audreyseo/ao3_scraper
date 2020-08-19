import os
import re
from urllib.parse import parse_qs
#from fandom_scrape import fandom_names_json_name
import json
#from functools import reduce

search_keys = [
  "query",
  "title",
  "creators",
  "revised_at",
  "complete",
  "crossover",
  "single_chapter",
  "word_count",
  "language_id",
  "fandom_names",
  "rating_ids",
  "archive_warning_ids",
  "category_ids",
  "character_names",
  "relationship_names",
  "freeform_names",
  "hits",
  "kudos_count",
  "comments_count",
  "bookmarks_count",
  "sort_column",
  "sort_direction"
]

def get_search_parameters(url):
  query_dict = parse_qs(url, keep_blank_values=True)
  #print("{}".format(query_dict))
  ws = "work_search"
  find_key = re.compile(r"work_search\[([^\]]*)\]")
  return {find_key.sub(r"\1", k): v for k,v in query_dict.items() if find_key.match(k)}
  


def validate_ao3_search_url(url):
  def split_fandom_names(entry):
    nonflat_entry = [e.split(',') for e in entry]
    #print('nonflat entry {}'.format(nonflat_entry))
    entry = []
    for sublist in nonflat_entry:
      for s in sublist:
        entry.append(s)
        pass
      pass
    return entry
  def validate_fandom(entry):
    if len(entry) == 0:
      return True
    names = []
    with open("fandom_names.json", "r") as f:
      names_json = json.loads(f.read())
      if "names" in names_json:
        names = names_json["names"]
        pass
      pass
    """if entry not in names:
      print("Uh oh, fandom name {} not in list of all fandom names!".format(entry))
      pass
    else:
      print("Good, fandom name {} in list of all fandom names!".format(entry))"""
    return entry in names
  
  def validate_work_stats(entry):
    if len(entry) == 0:
      return True
    stats_validator = re.compile(r"\s*[><]?\s*\d+\s*(?:-\s*\d+\s*)?")
    if stats_validator.match(entry):
      return re.match(r"^\s*[><]\s*\d+\s*$", entry) or re.match(r"^\s*\d+\s*-\s*\d+\s*$", entry) or re.match(r"^\s*\d+\s*$", entry)
    return False

  def make_forall_predicate(pred, entry_modifier=lambda x:x):
    return lambda entries: all(pred(entry) for entry in entry_modifier(entries))
  
  valid_vals = {
    "complete": lambda x: x in ["", "T", "F"],
    "crossover": lambda x: x in ["", "T", "F"],
    "single_chapter": lambda x: x == ["0"] or x == ["0", "1"],
    "fandom_names": make_forall_predicate(validate_fandom, split_fandom_names),
    "rating_ids": lambda x: x in ["", "9", "10", "11", "12", "13"],
    "archive_warning_ids": lambda x: x in ["", "14", "17", "18", "16", "19", "20"],
    "category_ids": lambda x: x in ["", "116", "22", "21", "23", "2246", "24"],
    "word_count": validate_work_stats,
    "hits": validate_work_stats,
    "kudos_count": validate_work_stats,
    "comments_count": validate_work_stats,
    "bookmarks_count": validate_work_stats,
    "sort_column": lambda x: x in ["_score", "authors_to_sort_on", "title_to_sort_on", "created_at", "revised_at", "word_count", "hits", "kudos_count", "comments_count", "bookmarks_count"],
    "sort_direction": lambda x: x in ["", "asc", "desc"]
  }
  valid_vals = {k: (v if k in ["single_chapter", "fandom_names"] else make_forall_predicate(v)) for k,v in valid_vals.items()}

  only_search_params = get_search_parameters(url)
  #print("{}".format(only_search_params))

  for param in only_search_params:
    if param in valid_vals:
      validator = valid_vals[param]
      if not validator(only_search_params[param]):
        #print("Uh oh, found non-valid value(s) {} of parameter {}".format(only_search_params[param], param))
        return False
      #else:
      #  print("Yay, valid value(s) {} of parameter {}".format(only_search_params[param], param))
      #  pass
      """
      for k in only_search_params[param]:
        # They're all lists, for some reason
        if not validator(k):
          # Found first non-valid value
          print("Uh oh, found non-valid value {} of parameter {}".format(k, param))
          return False
        else:
          print("cool, {} is a valid value of {}".format(k, param))
          pass
        pass"""
      pass
    pass
  """testing_true = [">100", "    >     3430920", "<100", "    <233420   ", "100-1000", "    123   -   12223", "1244950", " 1111 "]
  testing_false = [" 1000 0000", "<>10000", "<>", "<", ">", "10000>", "10000<", "-1000", "<-10000", ">-34930", "393993-"]
  for t in testing_true:
    if validate_work_stats(t):
      print("Yay! Expected \"{}\" to be validated, was valid.".format(t))
      pass
    else:
      print("Uh oh, expected \"{}\" to be validated, but was not".format(t))
      pass
    pass
  for f in testing_false:
    if not validate_work_stats(f):
      print("Yay! Expected \"{}\" to not be validated, was not valid".format(f))
      pass
    else:
      print("Uh oh, expected \"{}\" to not be validated, but was valid".format(f))
      pass
    pass"""
  return True


rating_to_id = {
  "G": 10,
  "General Audiences": 10,
  "T": 11,
  "Teen And Up Audiences": 11,
  "M": 12,
  "Mature": 12,
  "Explicit": 13,
  "E": 13,
  "Not Rated": 9,
  "NR": 9
}

id_to_rating = {
  "9": "NR",
  "10": "G",
  "11": "T",
  "12": "M",
  "13": "E"
}

category_to_id = {
  "FF": 116,
  "MM": 23,
  "F/F": 116,
  "M/M": 23,
  "Multi": 2246,
  "F/M": 22,
  "FM": 22,
  "Gen": 21,
  "Other": 24
}

id_to_category = {
  "116": "FF",
  "23": "MM",
  "2246": "Multi",
  "22": "FM",
  "21": "Gen",
  "24": "Other"
}

warning_to_id = {
  "No Archive Warnings Apply": 16,
  "NAWA": 16,
  "Rape/Non-Con": 19,
  "RNC": 19,
  "Major Character Death": 18,
  "MCD": 18,
  "Choose Not To Use Archive Warnings": 14,
  "CNTUAW": 14,
  "Underage": 20
}

id_to_warning = {
  "16": "NAWA",
  "19": "RNC",
  "18": "MCD",
  "14": "CNTUAW",
  "20": "Underage"
}

def save_url_params(params_dict, url):
  # looks at rating_ids          (rating)
  #          category_ids        (category)
  #          archive_warning_ids (warning)
  def alert_to_error(param_name, value, id_to_param):
    print("Could not match value {} to an accepted value of {}! Expected: {}\n\tBad url: {}".format(value, param_name, [i for i in id_to_param], url))
  search_params = get_search_parameters(url)
  other_params = parse_qs(url)
  if "page" in other_params:
    if len(other_params["page"]) >= 1:
      params_dict["page"] = int(other_params["page"][0])
      pass
    pass
  if "rating_ids" in search_params:
    ratings = search_params["rating_ids"]
    if len(ratings) > 0 and len(ratings[0]) > 0:
      # cannot choose more than one rating
      assert len(ratings) == 1
      rating = ratings[0]
      if rating in id_to_rating:
        params_dict["rating"] = id_to_rating[rating]
        pass
      else:
        alert_to_error("rating_ids", rating, id_to_rating)
        pass
      pass
    elif params_dict["rating"] != "":
      # Apparently no ratings were chosen, but someone tried to put one in
      # via the commandline
      params_dict["rating"] = ""
      pass
    pass
  else:
    params_dict["rating"] = ""
    pass
  if "category_ids[]" in search_params:
    keyname = "category_ids[]"
    category_ids = search_params[keyname]
    if len(category_ids) > 0:
      if all(c in id_to_category for c in category_ids):
        params_dict["category"] = [id_to_category[c] for c in category_ids]
        pass
      else:
        alert_to_error(keyname, category_ids, id_to_category)
        pass
      pass
    elif len(params_dict["category"]) > 0:
      params_dict["category"] = []
      pass
    pass
  else:
    params_dict["category"] = []
    pass
  if "archive_warning_ids[]" in search_params:
    keyname = "archive_warning_ids[]"
    warning_ids = search_params[keyname]
    if len(warning_ids) > 0:
      if all(w in id_to_warning for w in warning_ids):
        params_dict["warning"] = [id_to_warning[w] for w in warning_ids]
        pass
      else:
        alert_to_error("archive_warning_ids", warning_ids, id_to_warning)
        pass
      pass
    elif len(params_dict["warning"]) > 0:
      params_dict["warning"] = []
      pass
    pass
  else:
    params_dict["warning"] = []
    pass
  pass

keys_to_ids = {
  "rating_ids": rating_to_id,
  "category_ids": category_to_id,
  "archive_warning_ids": warning_to_id
}

needs_double_brackets = [
  "category_ids",
  "archive_warning_ids"
]

def get_work_id(title_url):
  myid = os.path.basename(title_url)
  #print("myid: {}".format(myid))
  if re.match("^\d+$", myid):
    return myid
  return None

def ao3_work_search_url(query="",
                        title="",
                        creators=[],
                        revised_at="",
                        complete="",
                        crossover="",
                        single_chapter=0,
                        word_count="",
                        language_id="",
                        fandom_names=[],
                        rating_ids="",
                        archive_warning_ids=[],
                        category_ids=[],
                        character_names=[],
                        relationship_names=[],
                        freeform_names=[],
                        hits="",
                        kudos_count="",
                        comments_count="",
                        bookmarks_count="",
                        sort_column="_score",
                        sort_direction="desc",
                        page=1):
  keys = {
    "query": query,
    "title": title,
    "creators": creators,
    "revised_at": revised_at,
    "complete": complete,
    "single_chapter": single_chapter,
    "word_count": word_count,
    "language_id": language_id,
    "fandom_names": fandom_names,
    "rating_ids": rating_ids,
    "archive_warning_ids": archive_warning_ids,
    "category_ids": category_ids,
    "character_names": character_names,
    "relationship_names": relationship_names,
    "freeform_names": freeform_names,
    "hits": hits,
    "kudos_count": kudos_count,
    "comments_count": comments_count,
    "bookmarks_count": bookmarks_count,
    "sort_column": sort_column,
    "sort_direction": sort_direction
  }
  stub = "https://archiveofourown.org/works/search?"
  utf8 = "utf8=✓"
  ws = "&work_search"
  lb = "%5B"
  rb = "%5D"
  sep = "&"
  commit = "commit=Search"
  lrb = lb + rb
  url = stub
  searches = search_keys if page == 1 else sorted(search_keys)
  #for s in searches:
  #  print(s)
  # First put the page on, if necessary
  if page > 1:
    url += commit + sep + "page=" + str(page)
    url += sep + utf8
    pass
  else:
    url += utf8
    pass

  def convert_value(search_key, search_value):
    if search_key in keys_to_ids:
      if search_value in keys_to_ids[search_key]:
        return str(keys_to_ids[search_key][search_value])
    return search_value
  
  for s in searches:
    
    if s in keys:
      #print(s)
      value = keys[s]
      #print(value)
      sk =  ws + lb + s + rb
      if s in needs_double_brackets:
        sk += lrb
        pass
      sk += "="
      if isinstance(value, list):
        # BTW, apparently they just don't put in archive warning ids or category ids
        # if you don't specify any
        # so it's fine if those don't show up
        if s not in needs_double_brackets and len(value) == 0:
          url += sk
          pass
        for v in value:
          url += sk + convert_value(s, v)
      elif isinstance(value, str):
        url += sk + convert_value(s, value)
      elif isinstance(value, int):
        url += sk + str(value)
        pass
      pass
    pass
  if page == 1:
    url += sep + commit
    pass
  return url


if __name__ == "__main__":
  #print(ao3_work_search_url(page=2))
  validate_ao3_search_url(ao3_work_search_url(page=2))
  validate_ao3_search_url("https://archiveofourown.org/works/search?utf8=✓&work_search%5Bquery%5D=&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D=&work_search%5Bcomplete%5D=&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bword_count%5D=2067&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=Destiny+%28Video+Games%29&work_search%5Brating_ids%5D=&work_search%5Bcategory_ids%5D%5B%5D=116&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=_score&work_search%5Bsort_direction%5D=desc&commit=Search")
  validate_ao3_search_url("https://archiveofourown.org/works/search?utf8=✓&work_search%5Bquery%5D=&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D=&work_search%5Bcomplete%5D=T&work_search%5Bcrossover%5D=F&work_search%5Bsingle_chapter%5D=0&work_search%5Bsingle_chapter%5D=1&work_search%5Bword_count%5D=&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=Naruto&work_search%5Brating_ids%5D=&work_search%5Bcategory_ids%5D%5B%5D=116&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=_score&work_search%5Bsort_direction%5D=desc&commit=Search")

  validate_ao3_search_url("https://archiveofourown.org/works/search?utf8=✓&work_search%5Bquery%5D=&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D=&work_search%5Bcomplete%5D=T&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bsingle_chapter%5D=1&work_search%5Bword_count%5D=&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=Naruto%2CBleach&work_search%5Brating_ids%5D=&work_search%5Bcategory_ids%5D%5B%5D=116&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=_score&work_search%5Bsort_direction%5D=desc&commit=Search")
  save_url_params({"rating": "", "warning": [], "category": [], "page": 1}, ao3_work_search_url(page=2, archive_warning_ids=["MCD", "CNTUAW"]))
