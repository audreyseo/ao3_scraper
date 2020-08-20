import argparse
import json
import os
import glob
import time
from ao3_info import ao3_work_search_url
from scrape import search_start
import requests
from colors import color
import sys

def find_anon_works(batch_file_name):
  works = []
  params = {}
  anons = []
  with open(batch_file_name, "r") as f:
    works = json.loads(f.read())
  params = works.pop(0)
  for w in works:
    if "title" in w and "title_url" in w and "author" in w and "author_url" in w:
      if w["title"] is None:
        # Yep this should be an anon work
        #print("{}, {}, {}, {}".format(w["title"], w["title_url"], w["author"], w["author_url"]))
        anons.append(w)
  return anons, params


def turn_anon_into_search_string(anon):
  word_count = (">" + str(int(anon["words"].replace(",", "")) - 1)) if not anon["complete"] else (anon["words"] if anon["words"] != "0" else "0-1")
  rating_ids = anon["rating"]
  #language_id = anon["language"]
  hits = anon["hits"]
  fandoms = ",".join([f[0] for f in anon["fandom"]])
  return ao3_work_search_url(rating_ids=rating_ids,
                             word_count=word_count,
                             category_ids=anon["category"],
                             #archive_warning_ids=anon["warnings"],
                             #language_id=language_id,
                             #hits=">" + str(int(hits) - 1),
                             character_names=",".join([character[0] for character in anon["characters"]]),
                             freeform_names=",".join([tag[0] for tag in anon["tags"]]),
                             fandom_names=fandoms)


def read_json(file_name):
  obj = {}
  with open(file_name, "r") as f:
    obj = json.loads(f.read())
  return obj

if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("action", choices=["scrape", "intersection"])

  parser.add_argument("file", help=("The first of many batch files to look through for missed anonymous works"))

  parser.add_argument("--other-file", help=("The file to intersect with"))
  args = parser.parse_args()
  counter = 0
  fname = args.file

  if args.action == "intersection":
    oname = args.other_file
    if os.path.exists(fname) and os.path.exists(oname):
      anons1 = read_json(fname)
      anons2 = read_json(oname)
      fetch_time = time.ctime(time.time())
      fetch_time = fetch_time.replace(":", ".")
      fetch_time = fetch_time.replace(" ", "_")
      if "urls" in anons1 and "urls" in anons2 and ("params_dict" in anons1 and "params_dict" in anons2):
        params_dict1 = anons1["params_dict"]
        params_dict2 = anons2["params_dict"]
        for k in params_dict1:
          if k not in params_dict2:
            params_dict2[k] = ""
        for k in params_dict2:
          if k not in params_dict1:
            params_dict1[k] = ""
        params_dict = {k: [params_dict1[k], params_dict2[k]] for k in params_dict1} if params_dict1 != params_dict2 else params_dict1
        works1 = [a[0] for a in anons1["urls"]]
        works2 = [a[0] for a in anons2["urls"]]
        intersection = [w for w in works1 if w in works2]
        print("Most ambiguous anons: {}".format(len(intersection)))
        if len(intersection) > 0:
          with open("stubbornest_anons_" + fetch_time + ".json", "w") as f:
            f.write(json.dumps([params_dict] + intersection, indent="  "))
            f.flush()
            pass
          pass
        pass
      pass
    else:
      print("Warning: one of the files {} and {} does not exist".format(fname, oname))
      pass
    sys.exit()
    pass
        
  

  base, ext = os.path.splitext(fname)
  bbase = base[:-1]

  cur_file = bbase + str(counter) + ext
  anons = []
  params = {}
  while os.path.exists(cur_file):
    wks, pms = find_anon_works(cur_file)
    if not params:
      print("params is empty, filling params now")
      params = pms
      pass
    anons += wks
    counter += 1
    cur_file = bbase + str(counter) + ext
    pass
  searches = [(a, turn_anon_into_search_string(a)) for a in anons]

  fetch_time = time.ctime(time.time())
  fetch_time = fetch_time.replace(":", ".")
  fetch_time = fetch_time.replace(" ", "_")
  
  result_name = "stubborn_anons_" + fetch_time + ".json"
  

  print("Found {} anons".format(len(anons)))
  ambiguous_anons = []
  failed_anons = []
  works = [params]

  dumps = 0

  with open("anons_dump.json", "w") as f:
    f.write(json.dumps([[a,s] for a,s in searches], indent="  "))
    f.flush()
    pass

  batch_name = "batch_anons_" + fetch_time + "_"
  restart_name = "restart_" + batch_name[:-1] + ".json"

  print("Retrieving anons' information...")
  counter = 0
  for info, a in searches:
    time.sleep(5)
    try:
      res = requests.get(a, headers={"user-agent": ""})
      pass
    except requests.exceptions.ConnectionError:
      failed_anons.append(a)
      print("Failed to retrieve {}".format(a))
      pass
    else:
      temp_works = []
      counter += 1
      next_url, is_problem = search_start(res.text, temp_works)
      if is_problem and len(temp_works) == 0:
        print("Uh oh, anon failed.")
        failed_anons.append([info, a])
        pass
      elif len(temp_works) == 1:
        print("Got just the right number of works")
        works += temp_works
        pass
      elif len(temp_works) >= 2:
        print("Found {} works, instead of just one: Search {} brought up ambiguous results. May need to be refined.".format(len(temp_works), color(a, fg="blue")))
        ambiguous_anons.append([info, a])
        pass
      if counter % 5 == 0:
        print("Done with {} works, {} ambiguous anons, and {} failed anons".format(len(works), len(ambiguous_anons), len(failed_anons)))
      if len(works) > 1 and (len(works) - 1) % 2000 == 0:
        print("Writing out some works...")
        with open(batch_name + str(dumps) + ".json", "w") as f:
          f.write(json.dumps(works, indent="  "))
          f.flush()
          pass
        dumps += 1
        works = [params]
        pass
      pass
    pass

  with open(batch_name + str(dumps) + ".json", "w") as f:
    f.write(json.dumps(works, indent="  "))
    f.flush()
    pass
  
  if len(ambiguous_anons) > 0:
    print("Outputting {} ambiguous anons in file {}".format(len(ambiguous_anons), result_name))
    with open(result_name, "w") as f:
      f.write(json.dumps({"params_dict": params, "urls": ambiguous_anons}, indent="  "))
      f.flush()
      pass
    pass
  else:
    print("No ambiguous anons!")
    pass
  if len(failed_anons) > 0:
    print("Outputting {} failed anons in file {}".format(len(failed_anons), restart_name))
    with open(restart_name, "w") as f:
      f.write(json.dumps({"params_dict": params, "urls": failed_anons}, indent="  "))
      f.flush()
      pass
    pass
  else:
    print("No failed anons!")
    pass
  pass
  
