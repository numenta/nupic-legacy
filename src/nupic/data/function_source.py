# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2015, Numenta, Inc.  Unless you have an agreement
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


import types
import marshal

class FunctionSource(object):
  """A source of programmatically-generated data.
  This class is a shell for a user-supplied function
  and user-supplied state. It knows how to serialize
  its function -- this allows a network to be saved."""

  SEQUENCEINFO_RESET_ONLY = 0
  SEQUENCEINFO_SEQUENCEID_ONLY = 1
  SEQUENCEINFO_BOTH = 2
  SEQUENCEINFO_NONE = 3


  def __init__(self,
               func,
               state=None,
               resetFieldName=None,
               sequenceIdFieldName=None):

    self.func = func
    self.state = state
    self.resetFieldName = resetFieldName
    self.sequenceIdFieldName = sequenceIdFieldName
    self._cacheSequenceInfoType()


  def _cacheSequenceInfoType(self):
    """Figure out whether reset, sequenceId,
    both or neither are present in the data.
    Compute once instead of every time.

    Taken from filesource.py"""

    hasReset = self.resetFieldName is not None
    hasSequenceId = self.sequenceIdFieldName is not None

    if hasReset and not hasSequenceId:
      self._sequenceInfoType = self.SEQUENCEINFO_RESET_ONLY
      self._prevSequenceId = 0
    elif not hasReset and hasSequenceId:
      self._sequenceInfoType = self.SEQUENCEINFO_SEQUENCEID_ONLY
      self._prevSequenceId = None
    elif hasReset and hasSequenceId:
      self._sequenceInfoType = self.SEQUENCEINFO_BOTH
    else:
      self._sequenceInfoType = self.SEQUENCEINFO_NONE

  def getNextRecordDict(self):
    result = self.func(self.state)

    # Automatically add _sequenceId and _reset fields
    if self._sequenceInfoType == self.SEQUENCEINFO_SEQUENCEID_ONLY:
      sequenceId = result[self.sequenceIdFieldName]
      reset = sequenceId != self._prevSequenceId
      self._prevSequenceId = sequenceId
    elif self._sequenceInfoType == self.SEQUENCEINFO_NONE:
      reset = 0
      sequenceId = 0
    elif self._sequenceInfoType ==  self.SEQUENCEINFO_RESET_ONLY:
      reset = result[self.resetFieldName]
      if reset:
        self._prevSequenceId += 1
      sequenceId = self._prevSequenceId
    elif self._sequenceInfoType == self.SEQUENCEINFO_BOTH:
      reset = result[self.resetFieldName]
      sequenceId = result[self.sequenceIdFieldName]
    else:
      raise RuntimeError(
          "Internal error -- sequence info type not set in RecordSensor")

    # convert to int. Note hash(int) = same value
    sequenceId = hash(sequenceId)
    reset = int(bool(reset))

    result["_reset"] = reset
    result["_sequenceId"] = sequenceId
    result["_category"] = [None]

    return result


  def __getstate__(self):
    state = dict(
      state = self.state,
      resetFieldName = self.resetFieldName,
      sequenceIdFieldName = self.sequenceIdFieldName,
      sequenceInfoType = self._sequenceInfoType,
      prevSequenceId = getattr(self, "_prevSequenceId", None)
      )
    func = dict()
    func['code'] = marshal.dumps(self.func.func_code)
    func['name'] = self.func.func_name
    func['doc'] = self.func.func_doc
    state['func'] = func

    return state

  def __setstate__(self, state):
    funcinfo = state['func']
    self.func = types.FunctionType(marshal.loads(funcinfo['code']), globals())
    self.func.func_name = funcinfo['name']
    self.func.func_doc = funcinfo['doc']

    self.state = state['state']
    self.resetFieldName = state['resetFieldName']
    self.sequenceIdFieldName = state['sequenceIdFieldName']
    self._sequenceInfoType = state['sequenceInfoType']
    self._prevSequenceId = state['prevSequenceId']
