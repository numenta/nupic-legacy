#!/bin/bash
# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
        if [[ $file == *html || "$file" = prerelease || "$file" == stable ]]; then
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
    echo "<link rel='stylesheet' href='prerelease/_static/alabaster.css' type='text/css' />" >> $indexFile
    echo "</head>" >> $indexFile

    echo "<body role='document'>" >> $indexFile
    echo "<div class='document'>" >> $indexFile
    echo "<div class='documentwrapper'>" >> $indexFile

    echo "<ul>" >> $indexFile
    echo "<h1>NuPIC API Documentation</h1>" >> $indexFile
    echo "<h2>Versions</h2>" >> $indexFile
    for version in $versions; do
        echo "<li><a href='$version/index.html'>$version</a></li>" >> $indexFile
    done
    echo "</ul>" >> $indexFile
    echo "</div></div>" >> $indexFile
    echo "</body></html>" >> $indexFile
}

create_prerelease_and_stable_shortcuts() {
    declare docRoot="$1"
    declare versions="${!2}"
    local prerelease=false
    local stable=false
    echo "Building shortcut to stable and prerelease versions..."
    for version in $versions; do
        echo "  checking $version..."
        if [[ $version == *dev0 && "$prerelease" == false ]]; then
            # First dev version found should be prerelease
            echo "    Found prerelease version $version"
            rm -rf "$docRoot/prerelease"
            cp -rf "$docRoot/$version" "$docRoot/prerelease"
            prerelease=true
        elif [[ $version == "stable" || $version == "prerelease" ]]; then
            echo "    Skipping $version"
        elif [[ "$stable" == false && $version != *dev0 ]]; then
            echo "    Found stable version $version"
            rm -rf "$docRoot/stable"
            cp -rf "$docRoot/$version" "$docRoot/stable"
            stable=true
        fi
        if [[ "$prerelease" = true && "$stable" = true ]]; then
            # We've already found them.
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
# Nuke any existing version of these docs
git rm -rf $VERSION
git commit -m "Removing old docs for $VERSION..."
# Get the docs from the temp folder
mv "$TMP_DIR/$VERSION" $NUPIC

find_existing_versions $NUPIC
create_prerelease_and_stable_shortcuts $NUPIC versions[@]
# Add new shortcuts to version list for HTML render.
versions=("stable" "${versions[@]}");
versions=("prerelease" "${versions[@]}");
echo "${versions[@]}"
build_html_index "$NUPIC/index.html" versions[@]

# Add prerelease/stable version builds and new index
git add "$VERSION" index.html
# Runnning these individually in case they don't exist yet.
git add prerelease
git add stable
if [[ `git status --porcelain` ]]; then
  git commit -am "Development documentation build."
  git push upstream gh-pages --force
else
    echo "No doc changes"
fi

cd $CWD
