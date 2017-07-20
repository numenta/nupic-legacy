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

import time
import json
import itertools
import pprint
from operator import itemgetter

import numpy


class HsState(object):
  """This class encapsulates the Hypersearch state which we share with all
  other workers. This state gets serialized into a JSON dict and written to
  the engWorkerState field of the job record.

  Whenever a worker changes this state, it does an atomic setFieldIfEqual to
  insure it has the latest state as updated by any other worker as a base.

  Here is an example snapshot of this state information:
  swarms = {'a': {'status': 'completed',        # 'active','completing','completed',
                                               # or 'killed'
                   'bestModelId': <modelID>,   # Only set for 'completed' swarms
                   'bestErrScore': <errScore>, # Only set for 'completed' swarms
                   'sprintIdx': 0,
                   },
           'a.b': {'status': 'active',
                   'bestModelId': None,
                   'bestErrScore': None,
                   'sprintIdx': 1,
                  }
           }

  sprints = [{'status': 'completed',      # 'active','completing','completed'
              'bestModelId': <modelID>,   # Only set for 'completed' sprints
              'bestErrScore': <errScore>, # Only set for 'completed' sprints
             },
             {'status': 'completing',
              'bestModelId': <None>,
              'bestErrScore': <None>
             }
             {'status': 'active',
              'bestModelId': None
              'bestErrScore': None
             }
             ]
  """

  def __init__(self, hsObj):
    """ Create our state object.

    Parameters:
    ---------------------------------------------------------------------
    hsObj:     Reference to the HypersesarchV2 instance
    cjDAO:     ClientJobsDAO instance
    logger:    logger to use
    jobID:     our JobID
    """
    # Save constructor parameters
    self._hsObj = hsObj

    # Convenient access to the logger
    self.logger = self._hsObj.logger

    # This contains our current state, and local working changes
    self._state = None

    # This contains the state we last read from the database
    self._priorStateJSON = None

    # Set when we make a change to our state locally
    self._dirty = False

    # Read in the initial state
    self.readStateFromDB()

  def isDirty(self):
    """Return true if our local copy of the state has changed since the
    last time we read from the DB.
    """
    return self._dirty

  def isSearchOver(self):
    """Return true if the search should be considered over."""
    return self._state['searchOver']

  def readStateFromDB(self):
    """Set our state to that obtained from the engWorkerState field of the
    job record.


    Parameters:
    ---------------------------------------------------------------------
    stateJSON:    JSON encoded state from job record

    """
    self._priorStateJSON = self._hsObj._cjDAO.jobGetFields(self._hsObj._jobID,
                                                    ['engWorkerState'])[0]

    # Init if no prior state yet
    if self._priorStateJSON is None:
      swarms = dict()

      # Fast Swarm, first and only sprint has one swarm for each field
      # in fixedFields
      if self._hsObj._fixedFields is not None:
        print self._hsObj._fixedFields
        encoderSet = []
        for field in self._hsObj._fixedFields:
            if field =='_classifierInput':
              continue
            encoderName = self.getEncoderKeyFromName(field)
            assert encoderName in self._hsObj._encoderNames, "The field '%s' " \
              " specified in the fixedFields list is not present in this " \
              " model." % (field)
            encoderSet.append(encoderName)
        encoderSet.sort()
        swarms['.'.join(encoderSet)] = {
                                'status': 'active',
                                'bestModelId': None,
                                'bestErrScore': None,
                                'sprintIdx': 0,
                                }
      # Temporal prediction search, first sprint has N swarms of 1 field each,
      #  the predicted field may or may not be that one field.
      elif self._hsObj._searchType == HsSearchType.temporal:
        for encoderName in self._hsObj._encoderNames:
          swarms[encoderName] = {
                                  'status': 'active',
                                  'bestModelId': None,
                                  'bestErrScore': None,
                                  'sprintIdx': 0,
                                  }


      # Classification prediction search, first sprint has N swarms of 1 field
      #  each where this field can NOT be the predicted field.
      elif self._hsObj._searchType == HsSearchType.classification:
        for encoderName in self._hsObj._encoderNames:
          if encoderName == self._hsObj._predictedFieldEncoder:
            continue
          swarms[encoderName] = {
                                  'status': 'active',
                                  'bestModelId': None,
                                  'bestErrScore': None,
                                  'sprintIdx': 0,
                                  }

      # Legacy temporal. This is either a model that uses reconstruction or
      #  an older multi-step model that doesn't have a separate
      #  'classifierOnly' encoder for the predicted field. Here, the predicted
      #  field must ALWAYS be present and the first sprint tries the predicted
      #  field only
      elif self._hsObj._searchType == HsSearchType.legacyTemporal:
        swarms[self._hsObj._predictedFieldEncoder] = {
                       'status': 'active',
                       'bestModelId': None,
                       'bestErrScore': None,
                       'sprintIdx': 0,
                       }

      else:
        raise RuntimeError("Unsupported search type: %s" % \
                            (self._hsObj._searchType))

      # Initialize the state.
      self._state = dict(
        # The last time the state was updated by a worker.
        lastUpdateTime = time.time(),

        # Set from within setSwarmState() if we detect that the sprint we just
        #  completed did worse than a prior sprint. This stores the index of
        #  the last good sprint.
        lastGoodSprint = None,

        # Set from within setSwarmState() if lastGoodSprint is True and all
        #  sprints have completed.
        searchOver = False,

        # This is a summary of the active swarms - this information can also
        #  be obtained from the swarms entry that follows, but is summarized here
        #  for easier reference when viewing the state as presented by
        #  log messages and prints of the hsState data structure (by
        #  permutations_runner).
        activeSwarms = swarms.keys(),

        # All the swarms that have been created so far.
        swarms = swarms,

        # All the sprints that have completed or are in progress.
        sprints = [{'status': 'active',
                    'bestModelId': None,
                    'bestErrScore': None}],

        # The list of encoders we have "blacklisted" because they
        #  performed so poorly.
        blackListedEncoders = [],
        )

      # This will do nothing if the value of engWorkerState is not still None.
      self._hsObj._cjDAO.jobSetFieldIfEqual(
          self._hsObj._jobID, 'engWorkerState', json.dumps(self._state), None)

      self._priorStateJSON = self._hsObj._cjDAO.jobGetFields(
          self._hsObj._jobID, ['engWorkerState'])[0]
      assert (self._priorStateJSON is not None)

    # Read state from the database
    self._state = json.loads(self._priorStateJSON)
    self._dirty = False

  def writeStateToDB(self):
    """Update the state in the job record with our local changes (if any).
    If we don't have the latest state in our priorStateJSON, then re-load
    in the latest state and return False. If we were successful writing out
    our changes, return True

    Parameters:
    ---------------------------------------------------------------------
    retval:    True if we were successful writing out our changes
               False if our priorState is not the latest that was in the DB.
               In this case, we will re-load our state from the DB
    """
    # If no changes, do nothing
    if not self._dirty:
      return True

    # Set the update time
    self._state['lastUpdateTime'] = time.time()
    newStateJSON = json.dumps(self._state)
    success = self._hsObj._cjDAO.jobSetFieldIfEqual(self._hsObj._jobID,
                'engWorkerState', str(newStateJSON), str(self._priorStateJSON))

    if success:
      self.logger.debug("Success changing hsState to: \n%s " % \
                       (pprint.pformat(self._state, indent=4)))
      self._priorStateJSON = newStateJSON

    # If no success, read in the current state from the DB
    else:
      self.logger.debug("Failed to change hsState to: \n%s " % \
                       (pprint.pformat(self._state, indent=4)))

      self._priorStateJSON = self._hsObj._cjDAO.jobGetFields(self._hsObj._jobID,
                                                      ['engWorkerState'])[0]
      self._state =  json.loads(self._priorStateJSON)

      self.logger.info("New hsState has been set by some other worker to: "
                       " \n%s" % (pprint.pformat(self._state, indent=4)))

    return success


  def getEncoderNameFromKey(self, key):
    """ Given an encoder dictionary key, get the encoder name.

    Encoders are a sub-dict within model params, and in HSv2, their key
    is structured like this for example:
       'modelParams|sensorParams|encoders|home_winloss'

    The encoderName is the last word in the | separated key name
    """
    return key.split('|')[-1]


  def getEncoderKeyFromName(self, name):
    """ Given an encoder name, get the key.

    Encoders are a sub-dict within model params, and in HSv2, their key
    is structured like this for example:
       'modelParams|sensorParams|encoders|home_winloss'

    The encoderName is the last word in the | separated key name
    """
    return 'modelParams|sensorParams|encoders|%s' % (name)


  def getFieldContributions(self):
    """Return the field contributions statistics.

    Parameters:
    ---------------------------------------------------------------------
    retval:   Dictionary where the keys are the field names and the values
                are how much each field contributed to the best score.
    """

    #in the fast swarm, there is only 1 sprint and field contributions are
    #not defined
    if self._hsObj._fixedFields is not None:
      return dict(), dict()
    # Get the predicted field encoder name
    predictedEncoderName = self._hsObj._predictedFieldEncoder

    # -----------------------------------------------------------------------
    # Collect all the single field scores
    fieldScores = []
    for swarmId, info in self._state['swarms'].iteritems():
      encodersUsed = swarmId.split('.')
      if len(encodersUsed) != 1:
        continue
      field = self.getEncoderNameFromKey(encodersUsed[0])
      bestScore = info['bestErrScore']

      # If the bestScore is None, this swarm hasn't completed yet (this could
      #  happen if we're exiting because of maxModels), so look up the best
      #  score so far
      if bestScore is None:
        (_modelId, bestScore) = \
            self._hsObj._resultsDB.bestModelIdAndErrScore(swarmId)

      fieldScores.append((bestScore, field))


    # -----------------------------------------------------------------------
    # If we only have 1 field that was tried in the first sprint, then use that
    #  as the base and get the contributions from the fields in the next sprint.
    if self._hsObj._searchType == HsSearchType.legacyTemporal:
      assert(len(fieldScores)==1)
      (baseErrScore, baseField) = fieldScores[0]

      for swarmId, info in self._state['swarms'].iteritems():
        encodersUsed = swarmId.split('.')
        if len(encodersUsed) != 2:
          continue

        fields = [self.getEncoderNameFromKey(name) for name in encodersUsed]
        fields.remove(baseField)

        fieldScores.append((info['bestErrScore'], fields[0]))

    # The first sprint tried a bunch of fields, pick the worst performing one
    #  (within the top self._hsObj._maxBranching ones) as the base
    else:
      fieldScores.sort(reverse=True)

      # If maxBranching was specified, pick the worst performing field within
      #  the top maxBranching+1 fields as our base, which will give that field
      #  a contribution of 0.
      if self._hsObj._maxBranching > 0 \
              and len(fieldScores) > self._hsObj._maxBranching:
        baseErrScore = fieldScores[-self._hsObj._maxBranching-1][0]
      else:
        baseErrScore = fieldScores[0][0]


    # -----------------------------------------------------------------------
    # Prepare and return the fieldContributions dict
    pctFieldContributionsDict = dict()
    absFieldContributionsDict = dict()

    # If we have no base score, can't compute field contributions. This can
    #  happen when we exit early due to maxModels or being cancelled
    if baseErrScore is not None:

      # If the base error score is 0, we can't compute a percent difference
      #  off of it, so move it to a very small float
      if abs(baseErrScore) < 0.00001:
        baseErrScore = 0.00001
      for (errScore, field) in fieldScores:
        if errScore is not None:
          pctBetter = (baseErrScore - errScore) * 100.0 / baseErrScore
        else:
          pctBetter = 0.0
          errScore = baseErrScore   # for absFieldContribution

        pctFieldContributionsDict[field] = pctBetter
        absFieldContributionsDict[field] = baseErrScore - errScore

    self.logger.debug("FieldContributions: %s" % (pctFieldContributionsDict))
    return pctFieldContributionsDict, absFieldContributionsDict


  def getAllSwarms(self, sprintIdx):
    """Return the list of all swarms in the given sprint.

    Parameters:
    ---------------------------------------------------------------------
    retval:   list of active swarm Ids in the given sprint
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if info['sprintIdx'] == sprintIdx:
        swarmIds.append(swarmId)

    return swarmIds

  def getActiveSwarms(self, sprintIdx=None):
    """Return the list of active swarms in the given sprint. These are swarms
    which still need new particles created in them.

    Parameters:
    ---------------------------------------------------------------------
    sprintIdx:    which sprint to query. If None, get active swarms from all
                      sprints
    retval:   list of active swarm Ids in the given sprint
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if sprintIdx is not None and info['sprintIdx'] != sprintIdx:
        continue
      if info['status'] == 'active':
        swarmIds.append(swarmId)

    return swarmIds

  def getNonKilledSwarms(self, sprintIdx):
    """Return the list of swarms in the given sprint that were not killed.
    This is called when we are trying to figure out which encoders to carry
    forward to the next sprint. We don't want to carry forward encoder
    combintations which were obviously bad (in killed swarms).

    Parameters:
    ---------------------------------------------------------------------
    retval:   list of active swarm Ids in the given sprint
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if info['sprintIdx'] == sprintIdx and info['status'] != 'killed':
        swarmIds.append(swarmId)

    return swarmIds

  def getCompletedSwarms(self):
    """Return the list of all completed swarms.

    Parameters:
    ---------------------------------------------------------------------
    retval:   list of active swarm Ids
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if info['status'] == 'completed':
        swarmIds.append(swarmId)

    return swarmIds

  def getCompletingSwarms(self):
    """Return the list of all completing swarms.

    Parameters:
    ---------------------------------------------------------------------
    retval:   list of active swarm Ids
    """
    swarmIds = []
    for swarmId, info in self._state['swarms'].iteritems():
      if info['status'] == 'completing':
        swarmIds.append(swarmId)

    return swarmIds

  def bestModelInCompletedSwarm(self, swarmId):
    """Return the best model ID and it's errScore from the given swarm.
    If the swarm has not completed yet, the bestModelID will be None.

    Parameters:
    ---------------------------------------------------------------------
    retval:   (modelId, errScore)
    """
    swarmInfo = self._state['swarms'][swarmId]
    return (swarmInfo['bestModelId'],
            swarmInfo['bestErrScore'])

  def bestModelInCompletedSprint(self, sprintIdx):
    """Return the best model ID and it's errScore from the given sprint.
    If the sprint has not completed yet, the bestModelID will be None.

    Parameters:
    ---------------------------------------------------------------------
    retval:   (modelId, errScore)
    """
    sprintInfo = self._state['sprints'][sprintIdx]
    return (sprintInfo['bestModelId'],
            sprintInfo['bestErrScore'])

  def bestModelInSprint(self, sprintIdx):
    """Return the best model ID and it's errScore from the given sprint,
    which may still be in progress. This returns the best score from all models
    in the sprint which have matured so far.

    Parameters:
    ---------------------------------------------------------------------
    retval:   (modelId, errScore)
    """
    # Get all the swarms in this sprint
    swarms = self.getAllSwarms(sprintIdx)

    # Get the best model and score from each swarm
    bestModelId = None
    bestErrScore = numpy.inf
    for swarmId in swarms:
      (modelId, errScore) = self._hsObj._resultsDB.bestModelIdAndErrScore(swarmId)
      if errScore < bestErrScore:
        bestModelId = modelId
        bestErrScore = errScore

    return (bestModelId, bestErrScore)

  def setSwarmState(self, swarmId, newStatus):
    """Change the given swarm's state to 'newState'. If 'newState' is
    'completed', then bestModelId and bestErrScore must be provided.

    Parameters:
    ---------------------------------------------------------------------
    swarmId:      swarm Id
    newStatus:    new status, either 'active', 'completing', 'completed', or
                    'killed'
    """
    assert (newStatus in ['active', 'completing', 'completed', 'killed'])

    # Set the swarm status
    swarmInfo = self._state['swarms'][swarmId]
    if swarmInfo['status'] == newStatus:
      return

    # If some other worker noticed it as completed, setting it to completing
    #  is obviously old information....
    if swarmInfo['status'] == 'completed' and newStatus == 'completing':
      return

    self._dirty = True
    swarmInfo['status'] = newStatus
    if newStatus == 'completed':
      (modelId, errScore) = self._hsObj._resultsDB.bestModelIdAndErrScore(swarmId)
      swarmInfo['bestModelId'] = modelId
      swarmInfo['bestErrScore'] = errScore

    # If no longer active, remove it from the activeSwarms entry
    if newStatus != 'active' and swarmId in self._state['activeSwarms']:
      self._state['activeSwarms'].remove(swarmId)

    # If new status is 'killed', kill off any running particles in that swarm
    if newStatus=='killed':
      self._hsObj.killSwarmParticles(swarmId)

    # In case speculative particles are enabled, make sure we generate a new
    #  swarm at this time if all of the swarms in the current sprint have
    #  completed. This will insure that we don't mark the sprint as completed
    #  before we've created all the possible swarms.
    sprintIdx = swarmInfo['sprintIdx']
    self.isSprintActive(sprintIdx)

    # Update the sprint status. Check all the swarms that belong to this sprint.
    #  If they are all completed, the sprint is completed.
    sprintInfo = self._state['sprints'][sprintIdx]

    statusCounts = dict(active=0, completing=0, completed=0, killed=0)
    bestModelIds = []
    bestErrScores = []
    for info in self._state['swarms'].itervalues():
      if info['sprintIdx'] != sprintIdx:
        continue
      statusCounts[info['status']] += 1
      if info['status'] == 'completed':
        bestModelIds.append(info['bestModelId'])
        bestErrScores.append(info['bestErrScore'])

    if statusCounts['active'] > 0:
      sprintStatus = 'active'
    elif statusCounts['completing'] > 0:
      sprintStatus = 'completing'
    else:
      sprintStatus = 'completed'
    sprintInfo['status'] = sprintStatus

    # If the sprint is complete, get the best model from all of its swarms and
    #  store that as the sprint best
    if sprintStatus == 'completed':
      if len(bestErrScores) > 0:
        whichIdx = numpy.array(bestErrScores).argmin()
        sprintInfo['bestModelId'] = bestModelIds[whichIdx]
        sprintInfo['bestErrScore'] = bestErrScores[whichIdx]
      else:
        # This sprint was empty, most likely because all particles were
        #  killed. Give it a huge error score
        sprintInfo['bestModelId'] = 0
        sprintInfo['bestErrScore'] = numpy.inf


      # See if our best err score got NO BETTER as compared to a previous
      #  sprint. If so, stop exploring subsequent sprints (lastGoodSprint
      #  is no longer None).
      bestPrior = numpy.inf
      for idx in range(sprintIdx):
        if self._state['sprints'][idx]['status'] == 'completed':
          (_, errScore) = self.bestModelInCompletedSprint(idx)
          if errScore is None:
            errScore = numpy.inf
        else:
          errScore = numpy.inf
        if errScore < bestPrior:
          bestPrior = errScore

      if sprintInfo['bestErrScore'] >= bestPrior:
        self._state['lastGoodSprint'] = sprintIdx-1

      # If ALL sprints up to the last good one are done, the search is now over
      if self._state['lastGoodSprint'] is not None \
            and not self.anyGoodSprintsActive():
        self._state['searchOver'] = True

  def anyGoodSprintsActive(self):
    """Return True if there are any more good sprints still being explored.
    A 'good' sprint is one that is earlier than where we detected an increase
    in error from sprint to subsequent sprint.
    """
    if self._state['lastGoodSprint'] is not None:
      goodSprints = self._state['sprints'][0:self._state['lastGoodSprint']+1]
    else:
      goodSprints = self._state['sprints']

    for sprint in goodSprints:
      if sprint['status'] == 'active':
        anyActiveSprints = True
        break
    else:
      anyActiveSprints = False

    return anyActiveSprints

  def isSprintCompleted(self, sprintIdx):
    """Return True if the given sprint has completed."""
    numExistingSprints = len(self._state['sprints'])
    if sprintIdx >= numExistingSprints:
      return False

    return (self._state['sprints'][sprintIdx]['status'] == 'completed')

  def killUselessSwarms(self):
    """See if we can kill off some speculative swarms. If an earlier sprint
    has finally completed, we can now tell which fields should *really* be present
    in the sprints we've already started due to speculation, and kill off the
    swarms that should not have been included.
    """
    # Get number of existing sprints
    numExistingSprints = len(self._state['sprints'])

    # Should we bother killing useless swarms?
    if self._hsObj._searchType == HsSearchType.legacyTemporal:
      if numExistingSprints <= 2:
        return
    else:
      if numExistingSprints <= 1:
        return

    # Form completedSwarms as a list of tuples, each tuple contains:
    #  (swarmName, swarmState, swarmBestErrScore)
    # ex. completedSwarms:
    #    [('a', {...}, 1.4),
    #     ('b', {...}, 2.0),
    #     ('c', {...}, 3.0)]
    completedSwarms = self.getCompletedSwarms()
    completedSwarms = [(swarm, self._state["swarms"][swarm],
                        self._state["swarms"][swarm]["bestErrScore"]) \
                                                for swarm in completedSwarms]

    # Form the completedMatrix. Each row corresponds to a sprint. Each row
    #  contains the list of swarm tuples that belong to that sprint, sorted
    #  by best score. Each swarm tuple contains (swarmName, swarmState,
    #  swarmBestErrScore).
    # ex. completedMatrix:
    #    [(('a', {...}, 1.4), ('b', {...}, 2.0), ('c', {...}, 3.0)),
    #     (('a.b', {...}, 3.0), ('b.c', {...}, 4.0))]
    completedMatrix = [[] for i in range(numExistingSprints)]
    for swarm in completedSwarms:
      completedMatrix[swarm[1]["sprintIdx"]].append(swarm)
    for sprint in completedMatrix:
      sprint.sort(key=itemgetter(2))

    # Form activeSwarms as a list of tuples, each tuple contains:
    #  (swarmName, swarmState, swarmBestErrScore)
    # Include all activeSwarms and completingSwarms
    # ex. activeSwarms:
    #    [('d', {...}, 1.4),
    #     ('e', {...}, 2.0),
    #     ('f', {...}, 3.0)]
    activeSwarms = self.getActiveSwarms()
    # Append the completing swarms
    activeSwarms.extend(self.getCompletingSwarms())
    activeSwarms = [(swarm, self._state["swarms"][swarm],
                     self._state["swarms"][swarm]["bestErrScore"]) \
                                                for swarm in activeSwarms]

    # Form the activeMatrix. Each row corresponds to a sprint. Each row
    #  contains the list of swarm tuples that belong to that sprint, sorted
    #  by best score. Each swarm tuple contains (swarmName, swarmState,
    #  swarmBestErrScore)
    # ex. activeMatrix:
    #    [(('d', {...}, 1.4), ('e', {...}, 2.0), ('f', {...}, 3.0)),
    #     (('d.e', {...}, 3.0), ('e.f', {...}, 4.0))]
    activeMatrix = [[] for i in range(numExistingSprints)]
    for swarm in activeSwarms:
      activeMatrix[swarm[1]["sprintIdx"]].append(swarm)
    for sprint in activeMatrix:
      sprint.sort(key=itemgetter(2))


    # Figure out which active swarms to kill
    toKill = []
    for i in range(1, numExistingSprints):
      for swarm in activeMatrix[i]:
        curSwarmEncoders = swarm[0].split(".")

        # If previous sprint is complete, get the best swarm and kill all active
        #  sprints that are not supersets
        if(len(activeMatrix[i-1])==0):
          # If we are trying all possible 3 field combinations, don't kill any
          #  off in sprint 2
          if i==2 and (self._hsObj._tryAll3FieldCombinations or \
                self._hsObj._tryAll3FieldCombinationsWTimestamps):
            pass
          else:
            bestInPrevious = completedMatrix[i-1][0]
            bestEncoders = bestInPrevious[0].split('.')
            for encoder in bestEncoders:
              if not encoder in curSwarmEncoders:
                toKill.append(swarm)

        # if there are more than two completed encoders sets that are complete and
        # are worse than at least one active swarm in the previous sprint. Remove
        # any combinations that have any pair of them since they cannot have the best encoder.
        #elif(len(completedMatrix[i-1])>1):
        #  for completedSwarm in completedMatrix[i-1]:
        #    activeMatrix[i-1][0][2]<completed

    # Mark the bad swarms as killed
    if len(toKill) > 0:
      print "ParseMe: Killing encoders:" + str(toKill)

    for swarm in toKill:
      self.setSwarmState(swarm[0], "killed")

    return

  def isSprintActive(self, sprintIdx):
    """If the given sprint exists and is active, return active=True.

    If the sprint does not exist yet, this call will create it (and return
    active=True). If it already exists, but is completing or complete, return
    active=False.

    If sprintIdx is past the end of the possible sprints, return
      active=False, noMoreSprints=True

    IMPORTANT: When speculative particles are enabled, this call has some
    special processing to handle speculative sprints:

      * When creating a new speculative sprint (creating sprint N before
      sprint N-1 has completed), it initially only puts in only ONE swarm into
      the sprint.

      * Every time it is asked if sprint N is active, it also checks to see if
      it is time to add another swarm to the sprint, and adds a new swarm if
      appropriate before returning active=True

      * We decide it is time to add a new swarm to a speculative sprint when ALL
      of the currently active swarms in the sprint have all the workers they
      need (number of running (not mature) particles is _minParticlesPerSwarm).
      This means that we have capacity to run additional particles in a new
      swarm.

    It is expected that the sprints will be checked IN ORDER from 0 on up. (It
    is an error not to) The caller should always try to allocate from the first
    active sprint it finds. If it can't, then it can call this again to
    find/create the next active sprint.

    Parameters:
    ---------------------------------------------------------------------
    retval:   (active, noMoreSprints)
                active: True if the given sprint is active
                noMoreSprints: True if there are no more sprints possible
    """

    while True:
      numExistingSprints = len(self._state['sprints'])

      # If this sprint already exists, see if it is active
      if sprintIdx <= numExistingSprints-1:

        # With speculation off, it's simple, just return whether or not the
        #  asked for sprint has active status
        if not self._hsObj._speculativeParticles:
          active = (self._state['sprints'][sprintIdx]['status'] == 'active')
          return (active, False)

        # With speculation on, if the sprint is still marked active, we also
        #  need to see if it's time to add a new swarm to it.
        else:
          active = (self._state['sprints'][sprintIdx]['status'] == 'active')
          if not active:
            return (active, False)

          # See if all of the existing swarms are at capacity (have all the
          # workers they need):
          activeSwarmIds = self.getActiveSwarms(sprintIdx)
          swarmSizes = [self._hsObj._resultsDB.getParticleInfos(swarmId,
                              matured=False)[0] for swarmId in activeSwarmIds]
          notFullSwarms = [len(swarm) for swarm in swarmSizes \
                           if len(swarm) < self._hsObj._minParticlesPerSwarm]

          # If some swarms have room return that the swarm is active.
          if len(notFullSwarms) > 0:
            return (True, False)

          # If the existing swarms are at capacity, we will fall through to the
          #  logic below which tries to add a new swarm to the sprint.

      # Stop creating new sprints?
      if self._state['lastGoodSprint'] is not None:
        return (False, True)

      # if fixedFields is set, we are running a fast swarm and only run sprint0
      if self._hsObj._fixedFields is not None:
        return (False, True)

      # ----------------------------------------------------------------------
      # Get the best model (if there is one) from the prior sprint. That gives
      # us the base encoder set for the next sprint. For sprint zero make sure
      # it does not take the last sprintidx because of wrapping.
      if sprintIdx > 0  \
            and self._state['sprints'][sprintIdx-1]['status'] == 'completed':
        (bestModelId, _) = self.bestModelInCompletedSprint(sprintIdx-1)
        (particleState, _, _, _, _) = self._hsObj._resultsDB.getParticleInfo(
                                                                  bestModelId)
        bestSwarmId = particleState['swarmId']
        baseEncoderSets = [bestSwarmId.split('.')]

      # If there is no best model yet, then use all encoder sets from the prior
      #  sprint that were not killed
      else:
        bestSwarmId = None
        particleState = None
        # Build up more combinations, using ALL of the sets in the current
        #  sprint.
        baseEncoderSets = []
        for swarmId in self.getNonKilledSwarms(sprintIdx-1):
          baseEncoderSets.append(swarmId.split('.'))

      # ----------------------------------------------------------------------
      # Which encoders should we add to the current base set?
      encoderAddSet = []

      # If we have constraints on how many fields we carry forward into
      # subsequent sprints (either nupic.hypersearch.max.field.branching or
      # nupic.hypersearch.min.field.contribution was set), then be more
      # picky about which fields we add in.
      limitFields = False
      if self._hsObj._maxBranching > 0 \
            or self._hsObj._minFieldContribution >= 0:
        if self._hsObj._searchType == HsSearchType.temporal or \
            self._hsObj._searchType == HsSearchType.classification:
          if sprintIdx >= 1:
            limitFields = True
            baseSprintIdx = 0
        elif self._hsObj._searchType == HsSearchType.legacyTemporal:
          if sprintIdx >= 2:
            limitFields = True
            baseSprintIdx = 1
        else:
          raise RuntimeError("Unimplemented search type %s" % \
                                  (self._hsObj._searchType))


      # Only add top _maxBranching encoders to the swarms?
      if limitFields:

        # Get field contributions to filter added fields
        pctFieldContributions, absFieldContributions = \
                                                self.getFieldContributions()
        toRemove = []
        self.logger.debug("FieldContributions min: %s" % \
                          (self._hsObj._minFieldContribution))
        for fieldname in pctFieldContributions:
          if pctFieldContributions[fieldname] < self._hsObj._minFieldContribution:
            self.logger.debug("FieldContributions removing: %s" % (fieldname))
            toRemove.append(self.getEncoderKeyFromName(fieldname))
          else:
            self.logger.debug("FieldContributions keeping: %s" % (fieldname))


        # Grab the top maxBranching base sprint swarms.
        swarms = self._state["swarms"]
        sprintSwarms = [(swarm, swarms[swarm]["bestErrScore"]) \
            for swarm in swarms if swarms[swarm]["sprintIdx"] == baseSprintIdx]
        sprintSwarms = sorted(sprintSwarms, key=itemgetter(1))
        if self._hsObj._maxBranching > 0:
          sprintSwarms = sprintSwarms[0:self._hsObj._maxBranching]

        # Create encoder set to generate further swarms.
        for swarm in sprintSwarms:
          swarmEncoders = swarm[0].split(".")
          for encoder in swarmEncoders:
            if not encoder in encoderAddSet:
              encoderAddSet.append(encoder)
        encoderAddSet = [encoder for encoder in encoderAddSet \
                         if not str(encoder) in toRemove]

      # If no limit on the branching or min contribution, simply use all of the
      # encoders.
      else:
        encoderAddSet = self._hsObj._encoderNames


      # -----------------------------------------------------------------------
      # Build up the new encoder combinations for the next sprint.
      newSwarmIds = set()

      # See if the caller wants to try more extensive field combinations with
      #  3 fields.
      if (self._hsObj._searchType == HsSearchType.temporal \
           or self._hsObj._searchType == HsSearchType.legacyTemporal) \
          and sprintIdx == 2 \
          and (self._hsObj._tryAll3FieldCombinations or \
               self._hsObj._tryAll3FieldCombinationsWTimestamps):

        if self._hsObj._tryAll3FieldCombinations:
          newEncoders = set(self._hsObj._encoderNames)
          if self._hsObj._predictedFieldEncoder in newEncoders:
            newEncoders.remove(self._hsObj._predictedFieldEncoder)
        else:
          # Just make sure the timestamp encoders are part of the mix
          newEncoders = set(encoderAddSet)
          if self._hsObj._predictedFieldEncoder in newEncoders:
            newEncoders.remove(self._hsObj._predictedFieldEncoder)
          for encoder in self._hsObj._encoderNames:
            if encoder.endswith('_timeOfDay') or encoder.endswith('_weekend') \
                or encoder.endswith('_dayOfWeek'):
              newEncoders.add(encoder)

        allCombos = list(itertools.combinations(newEncoders, 2))
        for combo in allCombos:
          newSet = list(combo)
          newSet.append(self._hsObj._predictedFieldEncoder)
          newSet.sort()
          newSwarmId = '.'.join(newSet)
          if newSwarmId not in self._state['swarms']:
            newSwarmIds.add(newSwarmId)

            # If a speculative sprint, only add the first encoder, if not add
            #   all of them.
            if (len(self.getActiveSwarms(sprintIdx-1)) > 0):
              break

      # Else, we only build up by adding 1 new encoder to the best combination(s)
      #  we've seen from the prior sprint
      else:
        for baseEncoderSet in baseEncoderSets:
          for encoder in encoderAddSet:
            if encoder not in self._state['blackListedEncoders'] \
                and encoder not in baseEncoderSet:
              newSet = list(baseEncoderSet)
              newSet.append(encoder)
              newSet.sort()
              newSwarmId = '.'.join(newSet)
              if newSwarmId not in self._state['swarms']:
                newSwarmIds.add(newSwarmId)

                # If a speculative sprint, only add the first encoder, if not add
                #   all of them.
                if (len(self.getActiveSwarms(sprintIdx-1)) > 0):
                  break


      # ----------------------------------------------------------------------
      # Sort the new swarm Ids
      newSwarmIds = sorted(newSwarmIds)

      # If no more swarms can be found for this sprint...
      if len(newSwarmIds) == 0:
        # if sprint is not an empty sprint return that it is active but do not
        #  add anything to it.
        if len(self.getAllSwarms(sprintIdx)) > 0:
          return (True, False)

        # If this is an empty sprint and we couldn't find any new swarms to
        #   add (only bad fields are remaining), the search is over
        else:
          return (False, True)

      # Add this sprint and the swarms that are in it to our state
      self._dirty = True

      # Add in the new sprint if necessary
      if len(self._state["sprints"]) == sprintIdx:
        self._state['sprints'].append({'status': 'active',
                                       'bestModelId': None,
                                       'bestErrScore': None})

      # Add in the new swarm(s) to the sprint
      for swarmId in newSwarmIds:
        self._state['swarms'][swarmId] = {'status': 'active',
                                            'bestModelId': None,
                                            'bestErrScore': None,
                                            'sprintIdx': sprintIdx}

      # Update the list of active swarms
      self._state['activeSwarms'] = self.getActiveSwarms()

      # Try to set new state
      success = self.writeStateToDB()

      # Return result if successful
      if success:
        return (True, False)

      # No success, loop back with the updated state and try again


class HsSearchType(object):
  """This class enumerates the types of search we can perform."""
  temporal = 'temporal'
  legacyTemporal = 'legacyTemporal'
  classification = 'classification'
