import argparse
import os
import json
from ao3_info import get_work_id, save_url_params, full_rating_to_abbr, warning_to_abbr
from scrape import searchable_parameters, searchables_to_params_dict_keys
import readline
import time
import glob
import re
import sys
from utils import eprint
from colors import color

from datetime import datetime


def get_last_updated_date(work):
  if "last_updated" in work:
    date_str = work["last_updated"]
    return datetime.strptime(date_str, "%d %b %Y")
  return None

def get_bbase_ext(filename):
  base, ext = os.path.splitext(filename)
  bbase = base[:-1]
  return bbase, ext


def add_files_to_exclude(params):
  if "included_batch_files" in params:
    return params["included_batch_files"]
  return []
def get_files_to_collate(filename, collate_all):
  filenames = []
  duplicate_filenames = []
  if collate_all:
    # get the parameters for the particular file, so that
    # they can all be squished together
    params = {}
    works = []
    exclude = []
    text = ""
    with open(filename, "r") as f:
      text = f.read()
    if len(text.strip()) > 0:
      works = json.loads(text)
      params = works[0]
      exclude = add_files_to_exclude(params)
    else:
      eprint("Warning: the file {} is empty. Please try a different file.")
      eprint("Quitting now.")
      sys.exit()
      pass
    
    for name in glob.glob("./batch_*.json"):
      should_add = True
      batch_params = {}
      name = os.path.basename(name)
      if name not in exclude:
        text = ""
        with open(name, "r") as f:
          text = f.read()
          pass
        if len(text.strip()) == 0:
          # this name is worthless
          exclude.append(name)
          continue
        
        works = json.loads(text)
        batch_params = works[0]
                  
        for param, p in searchables_to_params_dict_keys.items():
          if p in params:
            should_add = should_add and p in batch_params and params[p] == batch_params[p]
            pass
          else:
            should_add = False
          pass
        if should_add:
          exclude = exclude + add_files_to_exclude(batch_params)
          filenames.append(name)
          print("Globbed name: {}".format(name))
          pass
        pass
      pass
    inds_to_remove = []
    
    for i in range(len(filenames)):
      if filenames[i] in exclude:
        inds_to_remove.append(i)
        pass
      pass
    for i in reversed(inds_to_remove):
      #print("indices to remove: {}".format(i))
      duplicate_filenames.append(filenames.pop(i))
      pass
    print("Exclude: {}".format(exclude))
    print("Filenames: {}".format(filenames))
    pass
  else:
    bbase, ext = get_bbase_ext(filename)
    counter = 0
    newname = bbase + str(counter) + ext
    while os.path.exists(newname):
      filenames.append(newname)
      counter += 1
      newname = bbase + str(counter) + ext
      pass
    pass
  return filenames, duplicate_filenames
def collate(filename, collate_all=False, remove_anons=False):
  base, ext = os.path.splitext(filename)
  if ext != ".json":
    return None
  # get rid of the number from the end
  bbase = base[:-1]
  print(base, bbase)
  index = -1
  def strindex():
    nonlocal index
    index += 1
    return str(index)
  f = bbase + strindex() + ext

  # Retrieves all of the files to collate together, depending on the desired
  # parameters
  myfiles, dupes = get_files_to_collate(filename, collate_all)
  works = []
  for f in myfiles:
    with open(f, "r") as j:
      text = j.read()
      if len(text.strip()) > 0:
        print("Text: \"{}\"".format(text if len(text) < 100 else text[:100]))
        if len(works) == 0:
          works = json.loads(text)
          if "included_batch_files" not in works[0]:
            # Start off by noting which files are going to be included
            works[0]["included_batch_files"] = []
            pass
          if len(works[0]["included_batch_files"]) == 0:
            works[0]["included_batch_files"] = dupes
            pass
          else:
            for d in dupes:
              if d not in works[0]["included_batch_files"]:
                works[0]["included_batch_files"].append(d)
                pass
              pass
            pass
          pass
        else:
          tempworks = json.loads(text)
          # exclude the first one, which is
          # just the params anyway
          works += tempworks[1:]
          if "urls" not in works[0]:
            works[0]["urls"] = []
            if "url" in works[0]:
              works[0]["urls"].append(works[0]["url"])
              pass
            pass
          temp = tempworks[0]
          if "url" in temp:
            works[0]["urls"].append(temp["url"])
            pass
          pass
        pass
      pass
    works[0]["included_batch_files"].append(f)
    #f = bbase + strindex() + ext
    pass
  # OOPS, forgot about this
  works[0]["included_batch_files"] += dupes
  if remove_anons:
    #anon_indices = []
    anon_indices = [i for i in range(1, len(works)) if works[i]["title"] is None and works[i]["author"] is None]
    print("Found {} anonymous indices".format(len(anon_indices)))
    for i in reversed(anon_indices):
      works.pop(i)
  
  seen_ids = {}
  indices_to_remove = []
  for i in range(1, len(works)):
    if "title_url" in works[i]:
      myid = get_work_id(works[i]["title_url"])
      if myid in seen_ids:
        #print("Found a duplicate of {}".format(works[i]["title"]))
        this_date = get_last_updated_date(works[i])
        old_latest = seen_ids[myid]["latest_date"]
        this_chapters = int(works[i]["chapters"])
        old_chapters = seen_ids[myid]["chapters"]
        if old_latest is not None and this_date is not None and old_latest < this_date:
          # this_date is newer
          seen_ids[myid]["indices"].append(seen_ids[myid]["latest_index"])
          seen_ids[myid]["latest_index"] = i
          seen_ids[myid]["latest_date"] = this_date
          seen_ids[myid]["chapters"] = this_chapters
          pass
        elif this_chapters > old_chapters:
          seen_ids[myid]["indices"].append(seen_ids[myid]["latest_index"])
          seen_ids[myid]["latest_index"] = i
          seen_ids[myid]["latest_date"] = this_date
          seen_ids[myid]["chapters"] = this_chapters
        else:
          seen_ids[myid]["indices"].append(i)
          pass
        #indices_to_remove.append(i)
        pass
      else:
        if myid is not None and len(myid) > 0:
          seen_ids[myid] = {"indices": [], "latest_index": i, "latest_date": get_last_updated_date(works[i]), "chapters": int(works[i]["chapters"])}
          pass
        else:
          print("Weird, got 0-length id:\n{}".format(json.dumps(works[i], indent="  ")))
          pass
      pass
    else:
      print("Weird, one of the works did not have a title url:\n{}".format(json.dumps(works[i], indent="  ")))
      pass
    pass

  print(len(seen_ids.keys()))
  
  for myid, obj in seen_ids.items():
    indices_to_remove += obj["indices"]
    
  
  if len(indices_to_remove) > 0:
    print("Found {} duplicates".format(len(indices_to_remove)))
    # remove them backwards
    #for i in range(len(indices_to_remove) - 1, -1, -1):
    for i in sorted(indices_to_remove, reverse=True):
      works.pop(i)
      pass
    pass
  

  
  print("Writing collated data to file")
  print("Found {} entries".format(len(works) - 1))
  # file for all of them
  fall = bbase + "_all" + ext
  if collate_all:
    collate_time = time.ctime(time.time())
    collate_time = collate_time.replace(":", ".")
    collate_time = collate_time.replace(" ", "_")
    fall = "batch_all_collated_" + collate_time + ".json"
  with open(fall, "w") as j:
    j.write(json.dumps(works, indent="  "))
    j.flush()
  return fall


def lighten(work,
            keep_title=True,
            keep_title_url=True,
            add_work_id=False,
            keep_author=True,
            keep_author_url=True,
            keep_fandom_names=True,
            keep_fandom_urls=True,
            keep_rating=True,
            abbreviate_rating=False,
            keep_warnings=True,
            abbreviate_warnings=False,
            keep_category=True,
            keep_complete=True,
            keep_last_updated=True,
            keep_relationships_names=True,
            keep_relationships_urls=True,
            keep_characters_names=True,
            keep_characters_urls=True,
            keep_tags_names=True,
            keep_tags_urls=True,
            keep_summary=True,
            keep_language=True,
            keep_words=True,
            keep_chapters=True,
            keep_max_chapters=True,
            keep_hits=True,
            transform=lambda newWork, oldWork: newWork):
  newwork = {}
  def add_key(keyname, should_add_key, accesser=lambda x: x, new_key_name=None, default=""):
    nonlocal newwork
    if new_key_name is None:
      new_key_name = keyname
    if should_add_key:
      if keyname in work:
        newwork[new_key_name] = accesser(work[keyname])
        pass
      else:
        newwork[new_key_name] = default
        pass
      pass
    pass
  def add_lists_of_pairs(keep_item_0, keep_item_1):
    def make_final(list_of_pairs):
      # Always runs in an instance where at least one is true
      if keep_item_0 and keep_item_1:
        return list_of_pairs
      elif keep_item_0:
        return [pair[0] for pair in list_of_pairs]
      elif keep_item_1:
        return [pair[1] for pair in list_of_pairs]
      pass
    return make_final

  def make_abbreviation(add_abbreviation, abbreviator):
    def make_final(mystr):
      if isinstance(mystr, str):
        if mystr.find(",") > -1:
          splits = mystr.split(",")
          splits = [s.strip() for s in splits]
          return [(abbreviator[s] if add_abbreviation and s in abbreviator else s) for s in splits]
        return abbreviator[mystr] if add_abbreviation and mystr in abbreviator else mystr
      elif isinstance(mystr, list):
        return [(abbreviator[s] if add_abbreviation and s in abbreviator else s) for s in mystr]
    return make_final
        
  
  add_key("title", keep_title)
  add_key("title_url", keep_title_url)
  add_key("title_url", add_work_id, accesser=get_work_id, new_key_name="work_id")
  add_key("author", keep_author)
  add_key("author_url", keep_author_url)
  add_key("fandom",
          keep_fandom_names or keep_fandom_urls,
          accesser=add_lists_of_pairs(keep_fandom_names, keep_fandom_urls))
  add_key("rating",
          keep_rating,
          accesser=make_abbreviation(abbreviate_rating, full_rating_to_abbr))
  add_key("warnings", keep_warnings,
          accesser=make_abbreviation(abbreviate_warnings, warning_to_abbr),
          default=[])
  add_key("category", keep_category, default=[])
  add_key("complete", keep_complete, default=None)
  add_key("last_updated", keep_last_updated, default=None)
  add_key("relationships", keep_relationships_names or keep_relationships_urls,
          accesser=add_lists_of_pairs(keep_relationships_names, keep_relationships_urls),
          default=[])
  add_key("characters", keep_characters_names or keep_characters_urls,
          accesser=add_lists_of_pairs(keep_characters_names, keep_characters_urls),
          default=[])
  add_key("tags", keep_tags_names or keep_tags_urls,
          accesser=add_lists_of_pairs(keep_tags_names, keep_tags_urls),
          default=[])
  add_key("summary", keep_summary)
  add_key("language", keep_language)
  add_key("words", keep_words)
  add_key("chapters", keep_chapters)
  add_key("max_chapters", keep_max_chapters)
  add_key("hits", keep_hits)
  return transform(newwork, work)


def lighten_all(filename):
  def my_transformer(newwork, work):
    if "chapters" in work:
      # Deal with both the error case and the normal case
      newwork["multichapter"] = work["chapters"] == 0 or work["chapters"] > 1
    else:
      newwork["multichapter"] = None
    return newwork
  if os.path.exists(filename):
    text = ""
    with open(filename, "r") as f:
      text = f.read()
      pass
    if len(text.strip()) == 0:
      print("Nothing found in file {}. Exiting now...".format(filename))
      sys.exit()
      pass
    works = json.loads(text)
    new_works = []
    params = works[0]
    if "batch_type" not in params:
      params["batch_type"] = "lightweight"
      pass
    else:
      if isinstance(params["batch_type"], list):
        params["batch_type"].append("lightweight")
        pass
      else:
        # Must be somethnig...
        bt = params["batch_type"]
        params["batch_type"] = [bt, "lightweight"]
        pass
      pass
    new_works.append(params)
    for i in range(1, len(works)):
      w = works[i]
      new_works.append(lighten(w,
                               keep_title_url=False,
                               add_work_id=True,
                               keep_author_url=False,
                               keep_fandom_urls=False,
                               abbreviate_rating=True,
                               abbreviate_warnings=True,
                               keep_complete=False,
                               keep_relationships_urls=False,
                               keep_characters_urls=False,
                               keep_tags_urls=False,
                               keep_chapters=False,
                               keep_max_chapters=False,
                               transform=my_transformer))
      pass
    base, ext = os.path.splitext(filename)
    newfilename = base + "_lw" + ext
    print(color("Writing out {} lightened works to {}".format(len(new_works) - 1, newfilename), fg="cyan"))
    with open(newfilename, "w") as f:
      f.write(json.dumps(new_works, indent="  "))
      f.flush()
      pass
    pass
  else:
    print("Warning, file name {} does not exist. Exiting now.".format(filename))
    sys.exit()
    


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("action", choices=["collate", "stats", "convert_restart_file", "lighten"], help="Which action to take. collate takes all of the files from the same run and puts them together. stats will preform some rudimentary statistics on a given file. convert_restart_file takes a json/txt file of urls that need to be re-scraped and turns it into an appropriately formatted txt/json file, respectively. lighten will make the file more lightweight by removing extraneous data, and outputs a new file with name [filename]_lw.json.")
  parser.add_argument("file", help="The name of the batch (or restart) file to process")
  parser.add_argument("-a", "--all", action="store_true", help="Used only when collating. If present, then it will actually collate together all batch files run with the same search parameters. Otherwise, only files that have the same timestamp will be collated together.")
  parser.add_argument("-r", "--rating", default="", choices=["", "G", "T", "M", "E", "NR"], help="Which rating to give a bunch of urls. Only used for converting .txt to json files, for convert_restart_file.")
  parser.add_argument("-c", "--category", nargs="*", default=[], help="category(ies) to include in the resulting params_dict of a restart json file. Only used for converting .txt to json flies, for convert_restart_file. If not specified, automatically resorts to pulling the params from the urls themselves.")

  parser.add_argument('--remove-anons', action="store_true", help=("Used only when collating. If present, it will remove all entries where the title and author are None/null"))
  
  
  #parser.add_argument("-h", "--help", help="Display help/usage details.")
  args = parser.parse_args()


  print(args)
  # Add tab completion in the case of trying a different file name
  readline.set_completer_delims(' \t\n=')
  readline.parse_and_bind("tab: complete")

  if args.action == "lighten":
    lighten_all(args.file)
  elif args.action=="convert_restart_file":
    restart_file = args.file
    base, ext = os.path.splitext(restart_file)
    if ext != ".txt" and ext != ".json":
      print("Restart files must be either txt or json files, but found {}".format(restart_file))
      sys.exit()
    params_dict = {}
    urls = []
    if restart_file.endswith(".txt"):
      print("Ends with .txt")
      params_dict = {
        "category": args.category,
        "rating": args.rating,
        "warning": [],
        "page": 1,
        "end_page": -1,
        "max_works": -1,
        "page_increment": 1,
        "split_by": "none",
        "test_run": False,
        "from_url": "",
        "from_url_file": ""
      }

      with open(restart_file, "r") as f:
        text = f.read()
        lines = text.split("\n")
        lines = [l.strip() for l in lines]
        urls = [l for l in lines if l != ""]
        pass
      pass
    elif restart_file.endswith(".json"):
      with open(restart_file, "r") as f:
        text = f.read()
        j = json.loads(text)
        if "params_dict" in j and "urls" in j:
          params_dict = j["params_dict"]
          urls = j["urls"]
      pass

    if len(urls) > 0:
      print("Saving params...")
      
      save_rating_ids = len(args.rating) == 0
      save_category_ids = len(args.category) == 0
      print("params_dict: {}".format(params_dict))
      save_url_params(params_dict, urls[0],
                      save_rating_ids=save_rating_ids,
                      save_category_ids=save_category_ids)
      print("params_dict: {}".format(params_dict))
      pass
    else:
      print("No urls found in url file {}, please try again.".format(restart_file))
      sys.exit()
    
    other_ext = ".json" if ext == ".txt" else ".txt"
    newname = base + other_ext
    userOK = not os.path.exists(newname)
    while not userOK:
      userInput = input("A file named {} already exists. Would you like to choose a new name? (y/n): ".format(newname))
      userInput = userInput.lower()
      if userInput == "y":
        newname = input("Please enter a name ending in {}: ".format(other_ext))
        userOK = not os.path.exists(newname)
        pass
      else:
        newinput = input("Would you like to (1) quit or (2) continue without choosing a new name? (1/2): ")
        if newinput == "1":
          print("Okay, quitting now.")
          sys.exit()
          pass
        elif newinput == "2":
          print("Okay, continuing without choosing a new name.")
          userOK = True
          pass
        pass
      pass
    with open(newname, "w") as f:
      if restart_file.endswith(".txt"):
        f.write(json.dumps({"params_dict": params_dict, "urls": urls}))
        pass
      else:
        f.write("\n".join(urls) + "\n")
        pass
      f.flush()
      pass
  elif args.action == "collate":
    bbase, ext = get_bbase_ext(args.file)
    pickDiffFile = True
    quitting_out = False
    while os.path.exists(bbase + "_all" + ext) and pickDiffFile:
      answer = input("A collated file {} already exists. Continue? (y/n): ".format(bbase + "_all" + ext))
      if answer == "y":
        pickDiffFile = False
      elif answer == "n":
        newfile = input("Do you want to try a different file name? (y/n): ")
        if newfile in ["y", "Y"]:
          new_filename = input("Please input your new file name: ")
          bbase, ext = get_bbase_ext(new_filename)
        else:
          print("Quitting now. Oops")
          quitting_out = True
          sys.exit()
          pass
        pass
      pass
    
    if not quitting_out:
      dest = collate(args.file, collate_all = args.all, remove_anons=args.remove_anons)
      print("Collated in {}".format(dest))
      pass
