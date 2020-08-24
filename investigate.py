import json
import os
import argparse
from bs4 import BeautifulSoup
from scrape import get_stats
import requests
import time

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("file")


  args = parser.parse_args()

  if os.path.exists(args.file):
    works = []
    weird_works = []
    with open(args.file, "r") as f:
      text = f.read()
      if len(text) > 0:
        works = json.loads(text)
        pass
      pass
    if len(works) > 0:
      for i in range(1, len(works)):
        w = works[i]
        if "chapters" in w:
          chs = int(w["chapters"])
          if chs == 0:
            #print("Found a weirdo")
            weird_works.append(i)
            pass
          pass
        pass
      print("Num weirdos: {}".format(len(weird_works)))
      base, ext = os.path.splitext(args.file)
      num_changed = 0
      for i in weird_works:
        w = works[i]
        try:
          time.sleep(5)
          res = requests.get(w["title_url"])
          pass
        except requests.exceptions.ConnectionError as e:
          print("Skipping a work...")
          pass
        except KeyboardInterrupt:
          print("Quitting now....")
          break
        else:
          soup = BeautifulSoup(res.text, "html.parser")
          lang, words, chapters, max_chapters, hits = get_stats(soup)
          if chapters != 0 and chapters != "FAILURE":
            num_changed += 1
            w["chapters"] = chapters
            w["max_chapters"] = max_chapters
            works[i] = w
            pass
          if num_changed % 5 == 0:
            print("Changed {}".format(num_changed))
            pass
          pass
        pass
      print("Total num changed: {}".format(num_changed))
      with open(base + "_without_weirdos.json", "w") as f:
        f.write(json.dumps(works, indent="  "))
        f.flush()
        pass
      
      """if len(weird_works) > 0:
        with open(base + "_weirdos.json", "w") as f:
          f.write(json.dumps(weird_works, indent="   "))
          f.flush()
          pass
        pass
      else:
        print("Found no weird works")
        pass"""
      pass
    else:
      print("Found no works.")
      pass
    pass
  else:
    print("Could not find file {}. Please try again.".format(args.file))
    pass
  pass

          
