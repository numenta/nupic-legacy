# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------


# TODO for NUPIC 2 -- document the interface!
# TODO for NuPIC 2 -- should this move to inferenceanalysis?




def _calculateColumnsFromLine(line):
  if "," in line:
    splitLine = line.strip().split(",")
    n = len(splitLine)
    if n:
      if not splitLine[-1].strip():
        return n-1
      else:
        return n
    else:
      return 0
  else:
    # Too flexible.
    # return len([x for x in line.strip().split() if x != ","])
    return len(line.strip().split())

def _isComment(strippedLine):
  if strippedLine:
    return strippedLine.startswith("#")
  else:
    return True

def _calculateColumnsFromFile(f, format, rewind):
  # Calculate the number of columns.
  # We will put more trust in the second line that the first, in case the
  # first line includes header entries.
  if format not in [0, 2, 3]:
    raise RuntimeError("Supported formats are 0, 2, and 3.")

  if format == 0:
    line0 = f.readline()
    csplit = line0.split()
    if len(csplit) != 1:
      raise RuntimeError("Expected first line of data file to  "
                         "contain a single number of columns. "
                         " Found %d fields" % len(csplit))
    try:
      numColumns = int(csplit[0])
    except:
      raise RuntimeError("Expected first line of data file to "
                         "contain a single number of columns. Found '%s'" % csplit[0])
    if rewind:
      f.seek(0)

    return numColumns

  elif format == 2:
    numColumns = 0
    numLinesRead = 0
    for line in f:
      strippedLine = line.strip()
      if not _isComment(strippedLine):
        curColumns = _calculateColumnsFromLine(strippedLine)
        numLinesRead += 1
        if numColumns and (numColumns != curColumns):
          raise RuntimeError("Different lines have different "
            "numbers of columns.")
        else:
          numColumns = curColumns
        if numLinesRead > 1:
          break
    if rewind:
      f.seek(0)
    return numColumns

  # CSV file: we'll just check the first line
  elif format == 3:
    strippedLine = f.readline().strip()
    numColumns = calculateColumnsFromLine(strippedLine)
    if rewind:
      f.seek(0)
    return numColumns

def processCategoryFile(f, format, categoryColumn=None, categoryColumns=None, count=1):
  """Read the data out of the given category file, returning a tuple
  (categoryCount, listOfCategories)

  @param  f                A file-like object containing the category info.
  @param  format           The format of the category file.  TODO: describe.
  @param  categoryColumn   If non-None, this is the column number (zero-based)
                           where the category info starts in the file.  If
                           None, indicates that the file only contains category
                           information (same as passing 0, but allows some
                           extra sanity checking).
  @param  categoryColumns  Indicates how many categories are active per
                           timepoint (how many elements wide the category info
                           is).  If 0, we'll determine this from the file.  If
                           None (the default), means that the category info
                           is 1 element wide, and that the list we return
                           will just be a list of ints (rather than a list of
                           lists)
  @param  count            Determines the size of chunks that will be aggregated
                           into a single entry. The default is 1, so each entry
                           from the file will be represented in the result. If
                           count > 1 then 'count' categories (all identical) will
                           be collapsed into a single entry. This is helpful for
                           aggregating explorers like EyeMovements where multiple
                           presentaions are conceptually the same item.
  @return categoryCount    The number of categories (aka maxCat + 1)
  @return allCategories    A list of the categories read in, with one item per
                           time point.  If 'categoryColumns' is None, each item
                           will be an int.  Otherwise, each item will be a list
                           of ints. If count > 1 then the categories will be
                           aggregated, so that each chunk of 'count' categories
                           will result in only one entry (all categories in a chunk
                           must be identical)
  """
  calculatedCategoryColumns = _calculateColumnsFromFile(f, format=format,
    rewind=(format==2 or format==3))

  # If the user passed categoryColumns as None, we'll return a list of ints
  # directly; otherwise we'll return a list of lists...
  wantListOfInts = (categoryColumns is None)

  # Get arguments sanitized...
  if categoryColumns == 0:
    # User has told us to auto-calculate the # of categories / time point...

    # If categoryColumn is not 0 or None, that's an error...
    if categoryColumn:
      raise RuntimeError("You can't specify an offset for category data "
                         "if using automatic width.")

    categoryColumn = 0
    categoryColumns = calculatedCategoryColumns
  elif categoryColumns is None:
    # User has told us that there's just one category...

    if categoryColumn is None:
      if calculatedCategoryColumns != 1:
        raise RuntimeError("Category file must contain exactly one column.")
      categoryColumn = 0

    categoryColumns = 1
  else:
    # User specified exactly how big the category data is...

    if (categoryColumns + categoryColumn) > calculatedCategoryColumns:
      raise RuntimeError("Not enough categories in file")

  maxCategory = 0

  allCategories = []
  for line in f:
    strippedLine = line.strip()
    if not _isComment(strippedLine):
      if wantListOfInts:
        category = int(strippedLine.split()[categoryColumn])
        allCategories.append(category)
        maxCategory = max(maxCategory, category)
      else:
        categories = strippedLine.split()[categoryColumn:
                                          categoryColumn+categoryColumns]
        categories = map(int, categories)
        allCategories.append(categories)
        maxCategory = max(maxCategory, max(categories))

  categoryCount = maxCategory + 1

  # Aggregate categories
  result = []
  if count > 1:
    # Make sure there the number of categories can be aggregated
    # exactly by chunks of size 'count'
    assert len(allCategories) % count == 0
    start = 0
    for i in range(len(allCategories) / count):
      end = start + count
      # Make sure each chunk of size 'count' contains exactly one category
      assert (min(allCategories[start:end]) == max(allCategories[start:end]))
      # Add just one entry for each chunk
      result.append(allCategories[start])
      start = end
  else:
    result = allCategories

  return categoryCount, result
