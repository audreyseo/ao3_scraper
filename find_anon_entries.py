import argparse
import json
import os
import glob
import time
from ao3_info import ao3_work_search_url
from scrape import search_start
import requests


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
  word_count = anon["words"]
  rating_ids = anon["rating"]
  #language_id = anon["language"]
  hits = anon["hits"]
  fandoms = ",".join([f[0] for f in anon["fandom"]])
  return ao3_work_search_url(rating_ids=rating_ids,
                             word_count=word_count,
                             archive_warning_ids=anon["warnings"],
                             #language_id=language_id,
                             hits=">" + str(int(hits) - 1),
                             fandom_names=fandoms)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("file", help=("The first of many batch files to look through for missed anonymous works"))
  args = parser.parse_args()
  counter = 0
  fname = args.file

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
    anons += wks
    counter += 1
    cur_file = bbase + str(counter) + ext
    pass
  searches = [turn_anon_into_search_string(a) for a in anons]

  fetch_time = time.ctime(time.time())
  fetch_time = fetch_time.replace(":", ".")
  fetch_time = fetch_time.replace(" ", "_")
  
  result_name = "stubborn_anons_" + fetch_time + ".json"
  

  print("Found {} anons".format(len(anons)))
  ambiguous_anons = []
  failed_anons = []
  works = [params]

  dumps = 0

  with open("anons_dump.txt", "w") as f:
    f.write("\n".join(searches) + "\n")
    f.flush()
    pass

  batch_name = "batch_anons_" + fetch_time + "_"
  restart_name = "restart_" + batch_name[:-1] + ".json"

  print("Retrieving anons' information...")
  counter = 0
  for a in searches:
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
        failed_anons.append(a)
        pass
      elif len(temp_works) == 1:
        print("Got just the right number of works")
        works += temp_works
        pass
      elif len(temp_works) >= 2:
        print("Search {} brought up ambiguous results. May need to be refined.".format(a))
        ambiguous_anons.append(a)
        pass
      if len(works) > 1 and (len(works) - 1) % 5 == 0:
        print("Done with {} works".format(counter))
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
  
