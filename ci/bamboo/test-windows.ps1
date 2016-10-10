#!/bin/bash
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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
# -----------------------------------------------------------------------------

# Run NuPIC tests on Windows.

# ASSUMES:
#   1. Current working directory is root of nupic source tree
#   2. The nupic wheel is in the current working directory


# Stop and fail script if any command fails
$ErrorActionPreference = "Stop"

# Trace script lines as they run
Set-PsDebug -Trace 1


$NupicRootDir = $(get-location).Path


. .\ci\bamboo\win-utils.ps1  # WrapCmd



WrapCmd { pip install "$((Get-ChildItem .\nupic-*.whl)[0].FullName)" }

# Python unit tests
WrapCmd { py.test --verbose tests\unit }

# Python integration tests
$env:NUPIC = $NupicRootDir  # Some tests rely on this to find the config files
WrapCmd { py.test --verbose tests\integration }
