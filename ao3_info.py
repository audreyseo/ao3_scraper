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

keys_to_ids = {
  "rating_ids": rating_to_id,
  "category_ids": category_to_id,
  "archive_warning_ids": warning_to_id
}

needs_double_brackets = [
  "category_ids",
  "archive_warning_ids"
]

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
  print(ao3_work_search_url(page=2))
