#!/bin/bash
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

# This script assumes you have the latest codebase built locally.

build_html_index() {
    ROOT="$1"
    HTTP="/"
    OUTPUT="$2"

    i=0
    echo "<UL>" > $OUTPUT
    for filepath in `find "$ROOT" -maxdepth 1 -mindepth 1 -type d| sort`; do
      path=`basename "$filepath"`
      echo "  <LI>$path</LI>" >> $OUTPUT
      echo "  <UL>" >> $OUTPUT
      for i in `find "$filepath" -maxdepth 1 -mindepth 1 -type f| sort`; do
        file=`basename "$i"`
        echo "    <LI><a href=\"/$path/$file\">$file</a></LI>" >> $OUTPUT
      done
      echo "  </UL>" >> $OUTPUT
    done
    echo "</UL>" >> $OUTPUT
}

cd $NUPIC/docs

VERSION=`cat $NUPIC/VERSION`

# Clean and build into versioned folder.
make clean html

# Move the HTML somewhere else for sanity's sake.
mkdir ~/docstash
mv ./build/html ~/docstash/.

cd $NUPIC

# Context switch
git checkout gh-pages
# Get rid of any nupic artifacts
git clean -fd


# Get the docs from the temp folder
cp -r ~/html/* .

# Add a .nojekyll file to ensure static site build
touch .nojekyll

# Add and force push all. Nukes everything. Who cares.
git add guides contributing quick-start api _sources _static _images objects.inv *.html *.css *.js .nojekyll
if [[ `git status --porcelain` ]]; then
  git commit -am "Development documentation build."
  git push upstream gh-pages
else
  echo "No doc changes"
fi

cd -
