import argparse
import os
import json
from ao3_info import get_work_id
import readline
import time

def get_bbase_ext(filename):
  base, ext = os.path.splitext(filename)
  bbase = base[:-1]
  return bbase, ext

def collate(filename, collate_all=False):
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
  works = []
  while os.path.exists(f):
    with open(f, "r") as j:
      if len(works) == 0:
        works = json.loads(j.read())
      else:
        tempworks = json.loads(j.read())
        # exclude the first one, which is
        # just the params anyway
        works += tempworks[1:]
        if "urls" not in works[0]:
          works[0]["urls"] = []
          if "url" in works[0]:
            works[0]["urls"].append(works[0]["url"])
          pass
        temp = tempworks[0]
        if "url" in temp:
          works[0]["urls"].append(temp["url"])
          pass
        pass
      pass
    f = bbase + strindex() + ext
    pass
  seen_ids = []
  indices_to_remove = []
  for i in range(1, len(works)):
    if "title_url" in works[i]:
      myid = get_work_id(works[i]["title_url"])
      if myid in seen_ids:
        print("Found a duplicate of {}".format(works[i]["title"]))
        indices_to_remove.append(i)
        pass
      pass
    pass
  if len(indices_to_remove) > 0:
    # remove them backwards
    for i in range(len(indices_to_remove) - 1, -1, -1):
      works.pop(indices_to_remove[i])
      pass
    pass
  

  
  print("Writing collated data to file")
  print("Found {} entries".format(len(works) - 1))
  # file for all of them
  fall = bbase + "_all" + ext
  with open(fall, "w") as j:
    j.write(json.dumps(works, indent="  "))
    j.flush()
  return fall






if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("action", choices=["collate", "stats"], help="Which action to take. collate takes all of the files from the same run and puts them together. stats will preform some rudimentary statistics on a given file.")
  parser.add_argument("file", help="The name of the batch file to process")
  parser.add_argument("-a", "--all", action="store_true", help="Used only when collating. If present, then it will actually collate together all batch files run with the same search parameters. Otherwise, only files that have the same timestamp will be collated together.")
  
  #parser.add_argument("-h", "--help", help="Display help/usage details.")
  args = parser.parse_args()

  # Add tab completion in the case of trying a different file name
  readline.set_completer_delims(' \t\n=')
  readline.parse_and_bind("tab: complete")
  
  if args.action == "collate":
    bbase, ext = get_bbase_ext(args.file)
    pickDiffFile = True
    quitting_out = False
    while os.path.exists(bbase + "_all" + ext) and pickDiffFile:
      answer = input("A collated file {} already exists. Continue? (y/n): ")
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
          pass
        pass
      pass
    
    if not quitting_out:
      dest = collate(args.file, collate_all = args.all)
      print("Collated in {}".format(dest))
      pass
