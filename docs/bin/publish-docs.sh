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

# This script assumes you have the latest codebase built locally. It assumes
# that $NUPIC is a complete path to the NuPIC codebase.

TMP_DIR="$HOME/tmp"
CWD=`pwd`
VERSION=`cat $NUPIC/VERSION`
versions=()

find_existing_versions() {
    declare docRoot="$1"
    versions=()
    echo "Looking for published versions in $docRoot..."
    for file in `ls $docRoot | sort -r`; do
        if [[ $file == *html ]]; then
            echo "  Skipping $file"
        elif [[ -d "$docRoot/$file" ]]; then
            echo "  Found $file"
            versions+=($file)
        else
            echo "  Skipping $file"
        fi
    done
}

build_html_index() {
    declare indexFile="$1"
    declare versions="${!2}"
    echo "Building version index at $indexFile..."
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

create_latest_and_dev_shortcuts() {
    declare docRoot="$1"
    declare versions="${!2}"
    local latest=false
    local stable=false
    for version in $versions; do
        echo "checking $version..."
        if [[ $version == *dev0 ]]; then
            # First dev version found should be latest
            echo "Found latest version $version"
            rm -rf "$docRoot/latest"
            cp -rf "$docRoot/$version" "$docRoot/latest"
            # versions=("latest" "${versions[@]}");
            latest=true
        elif [[ $version == "stable" || $version == "latest" ]]; then
            echo "Skipping $version"
        else
            echo "Found stable version $version"
            rm -rf "$docRoot/stable"
            cp -rf "$docRoot/$version" "$docRoot/latest"
            # versions=("latest" "${versions[@]}");
            stable=true
        fi
        if [[ latest && stable ]]; then
            versions=("stable" "${versions[@]}");
            versions=("latest" "${versions[@]}");
            break
        fi
    done
}

# Program start.
rm -rf $TMP_DIR
mkdir $TMP_DIR

cd $NUPIC/docs

# Clean and build into versioned folder.
make clean html
# Replace any old docs for this verison in the documentation root directory.
mv ./build/html "$TMP_DIR/$VERSION"

# Context switch to GH Pages branch
cd $NUPIC
git checkout gh-pages
# Get rid of any nupic artifacts
git clean -fd
# Get the docs from the temp folder
mv "$TMP_DIR/$VERSION" $NUPIC

find_existing_versions $NUPIC
create_latest_and_dev_shortcuts $NUPIC versions[@]
build_html_index "$NUPIC/index.html" versions[@]

# Add latest version build and new index
git add "$VERSION" index.html
git add latest
if [[ `git status --porcelain` ]]; then
  git commit -am "Development documentation build."
  git push upstream gh-pages --force
else
    echo "No doc changes"
fi

cd $CWD
