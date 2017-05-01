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

# This is NUPIC because we're going to switch to the gh-pages branch.
TMP_DIR="$HOME/tmp"
CWD=`pwd`
versions=()

rm -rf $TMP_DIR
mkdir $TMP_DIR

find_existing_versions() {
    declare docRoot="$1"
    versions=()
    for file in `ls -d $docRoot | sort -r`; do
        if [[ $file == *html ]]
        then
            echo "Skipping $file"
        else
            versions+=($file)
        fi
    done
}

build_html_index() {
    declare indexFile="$1"
    declare versions="${!2}"
    echo "<html>" > $indexFile

    echo "<head>" >> $indexFile
    echo "<style>" >> $indexFile
        echo "body{font-size:xx-large}" >> $indexFile
        echo "ul{margin-left:200px}" >> $indexFile
    echo "</style>" >> $indexFile
    echo "</head>" >> $indexFile

    echo "<body>" >> $indexFile
    echo "<ul>" >> $indexFile
    echo "<h1>NuPIC API Documentation</h1>" >> $indexFile
    echo "<h2>Versions</h2>" >> $indexFile
    for version in $versions; do
        echo "<li><a href='$version/index.html'>$version</a></li>" >> $indexFile
    done
    echo "</ul>" >> $indexFile
    echo "</body></html>" >> $indexFile
}

copy_latest_build() {
    declare docRoot="$1"
    declare versions="${!2}"
    for version in $versions; do
        echo "checking $version..."
        if [[ $version == *dev0 || $version == "latest" ]]; then
            echo "Skipping $version"
        else
            echo "Found latest version $version"
            rm -rf "$docRoot/latest"
            cp -rf "$docRoot/$version" "$docRoot/latest"
            versions=("latest" "${versions[@]}");
            break
        fi
    done
}

cd $NUPIC/docs

VERSION=`cat $NUPIC/VERSION`

# # Clean and build into versioned folder.
# make clean html
# # Replace any old docs for this verison in the documentation root directory.
# mv ./build/html "$TMP_DIR/$VERSION"

# Context switch to GH Pages branch
cd $NUPIC
git checkout gh-pages
# Get rid of any nupic artifacts
git clean -fd
# Get the docs from the temp folder
mv "$TMP_DIR/$VERSION" . || exit

find_existing_versions "$NUPIC"
echo "${versions[@]}"
exit
copy_latest_build $DOC_HTML_ROOT versions[@]
build_html_index "$DOC_HTML_ROOT/index.html" versions[@]

# Add and force push all. Nukes everything. Who cares.
echo git add "$VERSION" latest index.html
if [[ `git status --porcelain` ]]; then
    echo "This is where we would commit and push."
  # git commit -am "Development documentation build."
  # git push upstream gh-pages
else
    echo "No doc changes"
fi

cd $CWD
