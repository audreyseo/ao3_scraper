import json
import os
import argparse
import scrape
import ao3_info

def get_param(p_dict, key):
  if key in p_dict:
    return p_dict[key]
  return None

def get_searchables_to_ids():
  searchables_to_ids = {}
  for p, ids in ao3_info.keys_to_ids.items():
    if p in scrape.ao3_params_to_searchables:
      searchables_to_ids[scrape.ao3_params_to_searchables[p]] = ids
      pass
    pass
  return searchables_to_ids

def check_work(work, rating, category, warning):
  search_to_ids = get_searchables_to_ids()
  checker = {
    "rating": rating,
    "warnings": warning,
    "category": category
  }
  for k, v in checker.items():
    if k in work and v is not None:
      if isinstance(v, list) and isinstance(work[k], list):
        if len(v) > len(work[k]):
          return False
        transformed = []
        try:
          transformed = [search_to_ids[k][t] for t in work[k] if t in search_to_ids[k]]
          pass
        except KeyError:
          print("Got weird stuff {}".format(work[k]))
          print("Work url:\n{}".format(work["title_url"]))
          return False
        for value in v:
          if search_to_ids[k][value] not in transformed:
            print("{} does not contain {}".format(transformed, value))
            return False
          pass
        pass
      elif isinstance(v, str) and isinstance(work[k], str):
        try:
          if search_to_ids[k][v] != search_to_ids[k][work[k]]:
            print("Mismatch: expected {} but found {}".format(v, work[k]))
            return False
          pass
        except KeyError:
          # try to see if it is a rare work that has two ratings chosen somehow
          values = work[k].split(", ")
          if search_to_ids[k][v] not in [search_to_ids[k][t] for t in values if t in search_to_ids[k]]:
            print("Got weird stuff {}".format(work[k]))
            print("Work url:\n{}".format(work["title_url"]))
            return False
        pass
      pass
    pass
  return True


def check_for_duplicates_advanced(works):
  dupes = {}
  for i in range(len(works)):
    w = works[i]
    if w["title"] not in dupes:
      dupes[w["title"]] = [i]
      pass
    else:
      dupes[w["title"]].append(i)
      pass
    pass
  dupe_works = [[works[i] for i in indices] for title, indices in dupes.items() if len(indices) > 1]
  print("Found {} potential dupe pairs".format(len(dupe_works)))
  return dupe_works
            

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("file", help=("Name of the json file to verify the contents of"))

  parser.add_argument("-r", "--rating", default=None, help=("The rating we'd like every fic to have."))
  parser.add_argument("-c", "--category", nargs="*", default=None, help=("The categories that every fic should have"))
  parser.add_argument("-w", "--warning", nargs="*", default=None, help=("The warnings that every fic should have"))

  args = parser.parse_args()

  if os.path.exists(args.file):
    works = []
    with open(args.file, "r") as j:
      works = json.loads(j.read())
      pass
    if len(works) >= 2:
      # Should have params dict and at least one work, hopefully
      params_dict = works[0]
      rating = args.rating or get_param(params_dict, "rating")
      category = args.category or get_param(params_dict, "category")
      warning = args.warning or get_param(params_dict, "warning")
      print("{}, {}, {}".format(rating, category, warning))
      only_works = works[1:]
      bad_works = []
      for w in only_works:
        if not check_work(w, rating, category, warning):
          bad_works.append(w)
          pass
        pass
      for w in only_works:
        if w["title"] == "" or w["author"] == "":
          bad_works.append(w)
      if len(bad_works) > 0:
        print("Found {} bad works".format(len(bad_works)))
        with open("bad_works.json", "w") as j:
          j.write(json.dumps([params_dict] + bad_works, indent="  "))
          j.flush()
          pass
        pass
      else:
        print("Didn't find any bad works.")
        pass
      dupe_works = check_for_duplicates_advanced(only_works)
      if len(dupe_works) > 0:
        with open("dupe_works.json", "w") as j:
          j.write(json.dumps(dupe_works, indent="  "))
          j.flush()
          pass
        pass
      pass
    else:
      print("Too few works in file {}".format(args.file))
      pass
    pass
  else:
    print("File {} does not exist".format(args.file))
