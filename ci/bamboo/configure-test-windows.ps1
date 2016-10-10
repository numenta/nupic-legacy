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

# Install what's necessary on top of the Windows 10 Vagrant image for testing a
# NuPIC wheel.
#
# NOTE much of this will eventually go into a VM image
#
# ASSUMES:
#   1. Current working directory is root of nupic source tree


# Stop and fail script if any command fails
$ErrorActionPreference = "Stop"

# Trace script lines as they run
Set-PsDebug -Trace 1


. .\ci\bamboo\win-utils.ps1  # WrapCmd


# Install and start mysql without prompts
WrapCmd { chocolatey.exe install mysql -y }

# NOTE If you need to access the just-installed executables, refresh environment
# variables configured by chocolatey via `refreshenv` command
