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


# Common powershell utilities for use by windows bamboo test scripts.



# WrapCmd
#
# Use this function to wrap external commands for powershell error-checking.
#
# This is necessary so that `$ErrorActionPreference = "Stop"` will have the
# desired effect.
#
# Returns True if command's $LastExitCode was 0, False otherwise
#
# Usage: WrapCmd { cmd arg1 arg2 ... }
#
function WrapCmd
{
  [CmdletBinding()]

  param (
    [Parameter(Position=0, Mandatory=1)]
    [scriptblock]$Command,
    [Parameter(Position=1, Mandatory=0)]
    [string]$ErrorMessage = "ERROR: Command failed.`n$Command"
  )
  & $Command
  if ($LastExitCode -eq 0) {
    return $true
  }
  else {
    Write-Error "WrapCmd: $ErrorMessage"
    return $false
  }
}
