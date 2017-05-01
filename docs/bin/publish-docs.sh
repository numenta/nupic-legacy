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

DOC_HTML_ROOT="/Users/mtaylor/Desktop/newdocs"
versions=()
mkdir -p $DOC_HTML_ROOT

find_existing_versions() {
    declare docRoot="$1"
    versions=()
    for file in `ls $docRoot | sort -r`; do
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
    echo "<body" >> $indexFile
    echo "style='font-size:xx-large'" >> $indexFile
    echo ">" >> $indexFile
    echo "<ul>" >> $indexFile
    echo "<h1>NuPIC API Documentation Versions</h1>" >> $indexFile
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
# rm -rf "$DOC_HTML_ROOT/$VERSION"
# mv ./build/html "$DOC_HTML_ROOT/$VERSION"

cd $NUPIC

# Get versions

find_existing_versions $DOC_HTML_ROOT
copy_latest_build $DOC_HTML_ROOT versions[@]
build_html_index "$DOC_HTML_ROOT/index.html" versions[@]
echo "${versions[@]}"

# # Context switch to GH Pages branch
# git checkout gh-pages
# # Get rid of any nupic artifacts
# git clean -fd
# # Get the docs from the temp folder
# cp -r $HOME/html/* .

# # Add and force push all. Nukes everything. Who cares.
# git add guides contributing quick-start api _sources _static _images objects.inv *.html *.css *.js .nojekyll
# if [[ `git status --porcelain` ]]; then
#   git commit -am "Development documentation build."
#   git push upstream gh-pages
# else
#   echo "No doc changes"
# fi



cd -
