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

"""Run OPF benchmarks to ensure that changes don't degrade prediction accuracy.

This is done using a set of standard experiments with thresholds for the
prediction metrics. Limiting the number of permutations can cause the test to
fail if it results in lower accuracy.
"""

import sys
import os
import time
import imp
import json
import shutil
import tempfile

from optparse import OptionParser
from multiprocessing import Process, Queue
from Queue import Empty
from collections import deque

from nupic.database import ClientJobsDAO as cjdao
from nupic.swarming.exp_generator import ExpGenerator
from nupic.frameworks.opf.opfutils import InferenceType
from nupic.support.configuration import Configuration
from nupic.support.unittesthelpers.testcasebase import unittest
from nupic.swarming import permutations_runner
from nupic.swarming.utils import generatePersistentJobGUID



class OPFBenchmarkRunner(unittest.TestCase):


  # AWS tests attribute required for tagging via automatic test discovery via
  # nosetests
  engineAWSClusterTest = 1

  allBenchmarks = ["hotgym",
                   "sine", "twovars",
                   "twovars2", "threevars",
                   "fourvars", "categories",
                   "sawtooth", "hotgymsc"]
  BRANCHING_PROP = "NTA_CONF_PROP_nupic_hypersearch_max_field_branching"
  PARTICLE_PROP = "NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm"


  # Common experiment parameters for all benchmarks
  EXP_COMMON = {"runBaselines":True,
                    "inferenceType":"MultiStep",
                    "inferenceArgs":{
                        "predictedField": None,
                        "predictionSteps":[1],
                    }
                }
  datadir = None
  outdir = None
  benchmarkDB = {}
  resultDB = {}
  splits={}
  descriptions={}
  testQ = []
  __doV2noTerm = None
  __doV2Term = None
  __doClusterDef = None
  __doEnsemble = False
  __maxNumWorkers = 2
  __recordsToProcess = -1
  __timeout = 120
  __maxPermutations = -1
  __clusterRunning = False
  __procs = []
  __numRunningProcs = 0
  __resultQ = Queue()
  __resultList = []
  runBenchmarks = None
  __failures=0
  __metaOptimize=False
  __trainFraction=None
  __expJobMap=Queue()
  swarmJobIDProductionJobIDMap={}
  maxBranchings = None
  maxParticles = None
  iterations = 1
  filesOnly = False
  maxConcurrentJobs = 1
  isSaveResults = True


  @classmethod
  def setUpClass(cls):
    cls.setupBenchmarks()


  @classmethod
  def getTests(cls, tests):
    found = False
    #Ignore case when matching
    tests = tests.lower()
    if('cluster_default' in tests):
      found = True
      cls.__doClusterDef = True
    if('v2noterm' in tests):
      found = True
      cls.__doV2noTerm = True
    if('v2term' in tests):
      found = True
      cls.__doV2Term = True
    return found


  def __updateProcessCounter(self):
    """ Function that iterates through the running Processes
    and counts the number of processes that are currently alive.
    Sets numRunningProcs to this count
    """

    newcounter = 0
    for job in self.__procs:
      if job.is_alive():
        newcounter+=1
    self.__numRunningProcs = newcounter
    return newcounter


  def cancelJobs(self):
    """ Function that cancels all the jobs in the
    process queue.
    """
    print "Terminating all Jobs due to reaching timeout"
    for proc in self.__procs:
      if not proc.is_alive():

        proc.terminate()
    print "All jobs have been terminated"


  def runJobs(self, maxJobs):
    """ Function that launched Hypersearch benchmark jobs.
    Runs jobs contained in self.testQ, until maxJobs are running
    in parallel at which point it waits until some jobs finish.

    """
    jobsrunning = self.__numRunningProcs
    if(maxJobs > 1):
      jobsindx = 0
      while(jobsindx<len(self.testQ) or jobsrunning>0):
        if(jobsindx<len(self.testQ) and jobsrunning<maxJobs):
          curJob = self.testQ[jobsindx]
          p = Process(target = curJob[0], args = curJob[1])
          p.start()
          self.__procs.append(p)
          jobsindx+=1
        if jobsrunning >= maxJobs:
          time.sleep(30)
          print ("Maximum number of jobs running, waiting before launching "
                 "new jobs")
        elif jobsindx == len(self.testQ):

          time.sleep(30)
          print "Waiting for all scheduled tests to finish."
        #Update the number of active running processes.
        jobsrunning = self.__updateProcessCounter()
        for proc in self.__procs:
          # Check that no process has died. If one has died, then kill all
          # running jobs and exit.
          if proc.exitcode == 1:
            self.cancelJobs()
            assert False, ("Some jobs have not been able to complete in the "
                           "allotted time.")

    # Check that each test satisfied the benchmark
    try:
      while True:
        result = self.__resultQ.get(True, 5)
        self.assertBenchmarks(result)
    except Empty:
      pass


  @classmethod
  def setupTrainTestSplits(cls):
    cls.splits['hotgym'] = int(round(cls.__trainFraction*87843))
    cls.splits['sine'] = int(round(cls.__trainFraction*3019))
    cls.splits['twovars'] = int(round(cls.__trainFraction*2003))
    cls.splits['twovars2'] = int(round(cls.__trainFraction*2003))
    cls.splits['threevars'] = int(round(cls.__trainFraction*2003))
    cls.splits['fourvars'] = int(round(cls.__trainFraction*2003))
    cls.splits['categories'] = int(round(cls.__trainFraction*2003))
    cls.splits['sawtooth'] = int(round(cls.__trainFraction*1531))
    # Only the first gym
    cls.splits['hotgymsc'] = int(round(cls.__trainFraction*17500))


  @classmethod
  def setupBenchmarks(cls):

    # BenchmarkDB stores error/margin pairs
    # Margin is in fraction difference. Thus .1 would mean a max of a
    # 10% difference

    cls.benchmarkDB['hotgym' + ',' + 'v2NoTerm'] = (15.69, .1)
    cls.benchmarkDB['hotgym' + ',' + 'v2Term'] = (15.69, .1)
    cls.benchmarkDB['hotgym' + ',' + 'cluster_default'] = (15.69, .1)

    cls.benchmarkDB['sine' + ',' + 'v2NoTerm'] = (0.054, .1)
    cls.benchmarkDB['sine' + ',' + 'v2Term'] = (0.054, .1)
    cls.benchmarkDB['sine' + ',' + 'cluster_default'] = (0.054, .1)

    # TODO: Convert these to altMAPE scores...
    cls.benchmarkDB['twovars' + ',' + 'v2NoTerm'] = (2.5, .1)
    cls.benchmarkDB['twovars' + ',' + 'v2Term'] = (2.5, .1)
    cls.benchmarkDB['twovars' + ',' + 'cluster_default'] = (2.5, .1)

    # TODO: Convert these to altMAPE scores...
    cls.benchmarkDB['twovars2' + ',' + 'v2NoTerm'] = (2.5, .1)
    cls.benchmarkDB['twovars2' + ',' + 'v2Term'] = (2.5, .1)
    cls.benchmarkDB['twovars2' + ',' + 'cluster_default'] = (2.5, .1)

    # TODO: Convert these to altMAPE scores...
    cls.benchmarkDB['threevars' + ',' + 'v2NoTerm'] = (2.5, .1)
    cls.benchmarkDB['threevars' + ',' + 'v2Term'] = (2.5, .1)
    cls.benchmarkDB['threevars' + ',' + 'cluster_default'] = (2.5, .1)

    # TODO: Convert these to altMAPE scores...
    cls.benchmarkDB['fourvars' + ',' + 'v2NoTerm'] = (2.5, .1)
    cls.benchmarkDB['fourvars' + ',' + 'v2Term'] = (2.5, .1)
    cls.benchmarkDB['fourvars' + ',' + 'cluster_default'] = (2.5, .1)

    # TODO: Convert these to altMAPE scores...
    cls.benchmarkDB['categories' + ',' + 'v2NoTerm'] = (1, .1)
    cls.benchmarkDB['categories' + ',' + 'v2Term'] = (1, .1)
    cls.benchmarkDB['categories' + ',' + 'cluster_default'] = (1, .1)

    # TODO: Convert these to altMAPE scores...
    cls.benchmarkDB['sawtooth' + ',' + 'v2NoTerm'] = (100, .1)
    cls.benchmarkDB['sawtooth' + ',' + 'v2Term'] = (100, .1)
    cls.benchmarkDB['sawtooth' + ',' + 'cluster_default'] = (100, .1)

    # HotGym using spatial classification
    cls.benchmarkDB['hotgymsc' + ',' + 'v2NoTerm'] = (21.1, .1)
    cls.benchmarkDB['hotgymsc' + ',' + 'v2Term'] = (21.1, .1)
    cls.benchmarkDB['hotgymsc' + ',' + 'cluster_default'] = (21.1, .1)


  def generatePrependPath(self, prependDict):
    prep = ""
    if 'iteration' in prependDict:
      prep = os.path.join(prep, str(prependDict["iteration"]))
    if (self.BRANCHING_PROP in prependDict and
        len(self.maxBranchings.split(",")) > 1):
      prep = os.path.join(prep, "maxBranch_%s" %
                          prependDict[self.BRANCHING_PROP])
    if (self.PARTICLE_PROP in prependDict and
        len(self.maxParticles.split(",")) > 1):
      prep = os.path.join(prep, "maxParticles_%s" %
                          prependDict[self.PARTICLE_PROP])
    return prep


  @classmethod
  def setMaxNumWorkers(cls, n):
    # Safety check to make sure not too many workers run on a local machine
    if(n is None):
      if(not cls.onCluster()):
        cls.__maxNumWorkers = 2
      else:
        cls.__maxNumWorkers = 20
    else:
      cls.__maxNumWorkers = n


  @classmethod
  def setNumRecords(cls, n):
    cls.__recordsToProcess = n


  def waitForProductionWorkers(self):
    jobsDB = cjdao.ClientJobsDAO.get()
    done=False
    while(not done):
      done=True
      for jobID in self.swarmJobIDProductionJobIDMap.keys():
        if (jobsDB.jobGetFields(self.swarmJobIDProductionJobIDMap[jobID],
            ["status",])[0] != 'completed'):
          done=False
          time.sleep(10)

    #When the production workers are done, get and store their results
    for jobRes in self.__resultList:
      swarmjobID = jobRes['jobID']
      prodjobID = self.swarmJobIDProductionJobIDMap[swarmjobID]
      prodResults = json.loads(jobsDB.jobGetFields(prodjobID, ['results'])[0])
      jobRes['prodMetric'] = str(prodResults['bestValue'])


  def submitProductionJob(self, modelID, dataSet):
    jobsDB = cjdao.ClientJobsDAO.get()

    outputDir=self.descriptions[dataSet][0]
    streamDef = self.descriptions[dataSet][1]["streamDef"]
    #streamDef["streams"][0]["first_record"]=self.splits[dataSet]
    streamDef["streams"][0]["last_record"]=sys.maxint

    cmdLine = "$PRODUCTIONMODEL"

    productionJobParams = dict(
       inputStreamDef = streamDef,
       #outputDir=outputDir,
       modelSpec = dict(
            checkpointID=jobsDB.modelsGetFields(
                  modelID, ("modelCheckpointId",))[0]),
     )

    productionJobParams['persistentJobGUID'] = generatePersistentJobGUID()
    if (productionJobParams["modelSpec"]["checkpointID"] is None):
      return -1
    return jobsDB.jobInsert(
           client="TstPW-PM",
           cmdLine=cmdLine,
           params=json.dumps(productionJobParams),
           minimumWorkers=1,
           maximumWorkers=1,
           jobType = jobsDB.JOB_TYPE_PM)


  def runProductionWorkers(self):

    jobsDB = cjdao.ClientJobsDAO.get()
    print "Starting Production Worker Jobs"
    print "__expJobMap " + str(self.__expJobMap) + str(id(self.__expJobMap))
    while not self.__expJobMap.empty():
      (dataSet, jobID) = self.__expJobMap.get()
      modelCounterPairs = jobsDB.modelsGetUpdateCounters(jobID)
      modelIDs = tuple(x[0] for x in modelCounterPairs)
      for modelID in modelIDs:
        prodID=self.submitProductionJob(modelID, dataSet)
        if(prodID!=-1):
          self.swarmJobIDProductionJobIDMap[jobID] = prodID


  @classmethod
  def setTrainFraction(cls, x):
    if x == None:
      cls.__trainFraction==1.0
    elif x > 1.0 or x < 0.0:
      raise Exception("Invalid training fraction")
    else:
      cls.__trainFraction=x


  @classmethod
  def setDoEnsemble(cls):
    cls.__doEnsemble = True


  @classmethod
  def setTimeout(cls, n):
    cls.__timeout = n


  @classmethod
  def setMaxPermutations(cls, n):
    cls.__maxPermutations = n


  def setEnsemble(self, ensemble):
    if(ensemble):
      os.environ['NTA_CONF_PROP_nupic_hypersearch_ensemble'] = "True"


  @classmethod
  def setMetaOptimize(cls, paramString):
    print paramString
    if paramString is None:
      cls.__metaOptimize = False
    else:
      cls.__metaOptimize = True
      paramsDict=json.loads(paramString)
      if(paramsDict.has_key("inertia")):
        os.environ['NTA_CONF_PROP_nupic_hypersearch_inertia'] = \
                  str(paramsDict['inertia'])

      if(paramsDict.has_key('socRate')):
        os.environ['NTA_CONF_PROP_nupic_hypersearch_socRate'] = \
                  str(paramsDict['socRate'])

      if(paramsDict.has_key('cogRate')):
        os.environ['NTA_CONF_PROP_nupic_hypersearch_cogRate'] = \
                  str(paramsDict['cogRate'])

      if(paramsDict.has_key('minParticlesPerSwarm')):
        os.environ['NTA_CONF_PROP_nupic_hypersearch_minParticlesPerSwarm'] = \
                   str(paramsDict['minParticlesPerSwarm'])


  def setUpExportDicts(self):
    """
    Setup up a dict of branchings and particles
    """
    ret = []
    if self.maxBranchings is None:
      self.maxBranchings = [None]
    else:
      self.maxBranchings = self.maxBranchings.split(',')
    if self.maxParticles is None:
      self.maxParticles = [None]
    else:
      self.maxParticles = self.maxParticles.split(",")
    for branch in self.maxBranchings:
      for part in self.maxParticles:
        curdict = dict()
        if not branch is None:
          curdict[self.BRANCHING_PROP] = branch
        if not part is None:
          curdict[self.PARTICLE_PROP] = part
        ret+=[curdict]
    return ret


  def addExportsToResults(self, results, exports):
    if self.BRANCHING_PROP in exports:
      results['maxBranching'] = exports[self.BRANCHING_PROP]
    if self.PARTICLE_PROP in exports:
      results['maxParticles'] = exports[self.PARTICLE_PROP]


  def syncFiles(self):
    if(self.onCluster()):
      os.system("syncDataFiles %s" % self.outdir)
    return


  def removeTmpDirs(self):
    print "Removing temporary directory <%s>" % self.outdir
    if(self.onCluster()):
      os.system("onall rm -r %s" % self.outdir)
    else :
      os.system("rm -r %s" % self.outdir)


  @classmethod
  def onCluster(cls):
    return (Configuration.get('nupic.cluster.database.host') != 'localhost')


  def createResultList(self):
    try:
      while 1:
        self.__resultList.append(self.__resultQ.get(True, 5))
    except Empty:
      pass


  def printResults(self):
    jobsDB = cjdao.ClientJobsDAO.get()
    productionError=-1
    for key in sorted(self.resultDB.keys()):
      restup = self.resultDB[key]
      if(self.__trainFraction<1.0):
        productionError=json.loads(jobsDB.jobGetFields(
                        self.swarmJobIDProductionJobIDMap[restup["jobID"]],
                        ["results",])[0])['bestValue']

      print ("Test: %10s      Expected: %10.4f     Swarm Error: %10.4f     "
             "ProductionError: %10.4f   TotalModelWallTime: %8d    "
             "RecordsProcessed: %10d    Status: %10s") % \
            (key, self.benchmarkDB[key][0], restup['metric'],
             productionError, restup['totalModelWallTime'],
             restup["totalNumRecordsProcessed"], restup['status'])


      if self.__metaOptimize:
        lineResults=str(key)+", "+str(self.benchmarkDB[key][0])+", "+ \
          str(restup['metric'])+", "+str(restup['totalModelWallTime'])+", "+ \
          str(restup["totalNumRecordsProcessed"])+", "+str(restup['status'])
        lineMeta=Configuration.get("nupic.hypersearch.minParticlesPerSwarm")+\
          ", "+Configuration.get("nupic.hypersearch.inertia")+", "+\
          Configuration.get("nupic.hypersearch.cogRate")+", "+\
          Configuration.get("nupic.hypersearch.socRate")+", "+\
          str(productionError)+", "+str(self.__trainFraction)+"\n"
        print lineMeta
        with open("allResults.csv", "a") as results:
          results.write(lineResults+", "+lineMeta)


  def saveResults(self):
    outpath = os.path.join(self.outdir, "BenchmarkResults.csv")
    csv = open(outpath, 'w')
    optionalKeys = ['maxBranching', 'maxParticles']
    print >> csv , (
        "JobID, Output Directory, Benchmark, Search, Swarm Error Metric,"
        " Prod. Error Metric, encoders, TotalModelElapsedTime(s), "
        "TotalCpuTime(s), JobWallTime, RecordsProcessed, Completion Status"),
    addstr = ""
    for key in optionalKeys:
      addstr+= ",%s" % key
    print >> csv, addstr
    for result in self.__resultList:
      print >> csv, "%d,%s,%s,%s,%f,%s,%s,%d,%f,%s,%d,%s" % (result['jobID'],
            result['outDir'], result['expName'], result['searchType'], \
            result["metric"], result["prodMetric"], \
            result['encoders'], \
            result["totalModelWallTime"], \
            result['totalModelCpuTime'], str(result['jobTime']), \
            result["totalNumRecordsProcessed"], result['status']),
      addstr = ""
      for key in optionalKeys:
        if key in result:
          addstr+= ",%s" % str(result[key])
        else:
          addstr+= ",None"
      print >> csv, addstr

    csv.close()


  def readModelWallTime(self, modelInfo):
    startTime = modelInfo.startTime
    if(modelInfo.status == cjdao.ClientJobsDAO.STATUS_COMPLETED):
      endTime = modelInfo.endTime
      return (endTime - startTime).seconds
    return 0


  def readNumRecordsProcessed(self, modelInfo):
    return modelInfo.numRecords


  def readModelCpuTime(self, modelInfo):
    return modelInfo.cpuTime


  def getResultsFromJobDB(self, jobID, expname, searchtype, basedir):
    ret = {}
    jobsDB = cjdao.ClientJobsDAO.get()
    jobInfo = jobsDB.jobInfo(jobID)
    res = jobInfo.results
    results = json.loads(res)
    bestModel = results["bestModel"]
    modelIds = jobsDB.jobGetModelIDs(jobID)
    modelInfos = jobsDB.modelsInfo(modelIds)
    totalModelWallTime = 0
    totalNumRecordsProcessed = 0
    totalModelCpuTime = 0.0
    for modelInfo in modelInfos:
      if modelInfo.modelId == bestModel:
        metrics = json.loads(modelInfo.results)[0]
        bestmetric = json.loads(modelInfo.results)[1].keys()[0]
        for key in metrics.keys():
          if "nupicScore" in key and "moving" in key:
            ret["nupicScore"] = ret[key] = metrics[key]
          ret[key] = metrics[key]
        ret["encoders"] = (
            json.loads(modelInfo.params)["particleState"]["swarmId"])
      totalModelWallTime += self.readModelWallTime(modelInfo)
      totalNumRecordsProcessed += self.readNumRecordsProcessed(modelInfo)
      totalModelCpuTime += self.readModelCpuTime(modelInfo)

    ret['outDir'] = basedir
    ret['jobID'] = jobID
    ret['status'] = jobInfo.workerCompletionReason
    ret['metric'] = results['bestValue']
    #ret['jobTime'] = jobTime
    ret['totalModelCpuTime'] = totalModelCpuTime
    ret['totalModelWallTime'] = totalModelWallTime
    ret['totalNumRecordsProcessed'] = totalNumRecordsProcessed
    ret['expName'] = expname
    ret['searchType'] = searchtype
    ret['prodMetric'] = ""
    return ret


  def benchmarkHotGym(self):
    """Try running a basic experiment and permutations."""
    # Form the stream definition
    dataPath = os.path.join(self.datadir, "hotgym", "hotgym.csv")

    streamDef = dict(
      version=1,
      info="hotgym benchmark test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="hotgym.csv",
             # NOTE: Limiting number of records to work around a bug in the
             # Streams Mgr present as of Dec 7, 2011 that shows up if you have
             # more than 50K records.
             # last_record = 49000,
             columns=["gym", "timestamp", "consumption"],
             last_record=self.splits['hotgym'],)
        ],
        aggregation={
        'hours' : 1,
        'fields' : [
                ('consumption', 'sum'),
                ('gym', 'first'),
                ]
          },

    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "consumption"
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  1.1,
          "maxValue":  44.72,
        },
        { "fieldName": "gym",
          "fieldType": "string",
        },
      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "hotgym")
    self.generateModules(expDesc,  expdir)
    self.descriptions["hotgym"]=(expdir, expDesc)

    return expdir


  def benchmarkSine(self):
    """ Try running a basic experiment and permutations
    """


    # Form the stream definition
    dataPath = os.path.join(self.datadir, "sine", "sine.csv")

    streamDef = dict(
      version=1,
      info="hotgym benchmark test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="sine.csv",
             columns=["Sine","angle"],
             last_record=self.splits['sine']),
        ],


    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "Sine"
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "Sine",
          "fieldType": "float",
          "minValue":  -1.0,
          "maxValue":  1.0,
        },
        { "fieldName": "angle",
          "fieldType": "float",
          "minValue":  0.0,
          "maxValue":  25.0,

        },
      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "sine")
    self.generateModules(expDesc,  expdir)
    self.descriptions["sine"]=(expdir, expDesc)

    return expdir


  def benchmarkTwoVars(self):
    """ Try running a basic experiment and permutations
    """

    # Form the stream definition
    dataPath = os.path.join(self.datadir, "generated", "spatial",
                            "linear_two_fields", "sample2.csv")

    streamDef = dict(
      version=1,
      info="two fields test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="linear_two_fields",
             columns=["field1","field2"],
             last_record=self.splits['twovars'],),
        ],


    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "field1"
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "field1",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,
        },
        { "fieldName": "field2",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,

        },
      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "twovars")
    self.generateModules(expDesc,  expdir)
    self.descriptions["twovars"]=(expdir, expDesc)
    return expdir


  def benchmarkThreeVars(self):
    """ Try running a basic experiment and permutations
    """

    # Form the stream definition
    dataPath = os.path.join(self.datadir, "generated", "spatial",
                            "linear_two_plus_one_fields", "sample1.csv")

    streamDef = dict(
      version=1,
      info="three fields test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="linear_two_plus_one_fields",
             columns=["field1","field2","field3"],
             last_record=self.splits['threevars']),
        ],


    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "field1"
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "field1",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,
        },
        { "fieldName": "field2",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,

        },
        { "fieldName": "field3",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,

        }
      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "threevars")
    self.generateModules(expDesc,  expdir)
    self.descriptions["threevars"]=(expdir, expDesc)
    return expdir


  def benchmarkFourVars(self):
    """ Try running a basic experiment and permutations
    """

    # Form the stream definition
    dataPath = os.path.join(self.datadir, "generated", "spatial",
                            "sum_two_fields_plus_extra_field", "sample1.csv")

    streamDef = dict(
      version=1,
      info="four fields test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="linear_two_plus_one_fields",
             columns=["field1","field2","field3","field4"],
             last_record=self.splits['fourvars']),
        ],


    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "field1"
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "field1",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  210,
        },
        { "fieldName": "field2",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,
        },
        { "fieldName": "field3",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,
        },
        { "fieldName": "field4",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,
        }

      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "fourvars")
    self.generateModules(expDesc,  expdir)
    self.descriptions["fourvars"]=(expdir, expDesc)
    return expdir


  def benchmarkCategories(self):
    """ Try running a basic experiment and permutations
    """

    # Form the stream definition
    dataPath = os.path.join(self.datadir, "generated", "temporal",
                            "categories", "sample1.csv")

    streamDef = dict(
      version=1,
      info="categories test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="categories",
             columns=["field1","field2"],
             last_record=self.splits['categories']),
        ],


    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "field2"
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "field1",
          "fieldType": "string",
        },
        { "fieldName": "field2",
          "fieldType": "string",
        }
      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "categories")
    self.generateModules(expDesc,  expdir)
    self.descriptions["categories"]=(expdir, expDesc)
    return expdir


  def benchmarkTwoVarsSquare(self):
    """ Try running a basic experiment and permutations
    """

    # Form the stream definition
    dataPath = os.path.join(self.datadir, "generated", "spatial",
                            "linear_two_fields", "sample3.csv")

    streamDef = dict(
      version=1,
      info="three fields test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="linear_two_fields",
             columns=["field1","field2"],
             last_record=self.splits['twovars2']),
        ],


    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "field1"
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "field1",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  110,
        },
        { "fieldName": "field2",
          "fieldType": "int",
          "minValue":  -10,
          "maxValue":  10010,
        }
      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "twovars2")
    self.generateModules(expDesc,  expdir)
    self.descriptions["twovars2"]=(expdir, expDesc)
    return expdir


  def benchmarkSawtooth(self):
    """ Try running a basic experiment and permutations
    """

    # Form the stream definition
    dataPath = os.path.join(self.datadir, "sawtooth", "sawtooth.csv")

    streamDef = dict(
      version=1,
      info="sawtooth test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="sawtooth",
             columns=["value"],
             last_record=self.splits['sawtooth'],),
        ],


    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "value"
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "value",
          "fieldType": "int",
          "runDelta":True,
        },
      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "sawtooth")
    self.generateModules(expDesc,  expdir)
    self.descriptions["sawtooth"]=(expdir, expDesc)
    return expdir


  def benchmarkHotGymSC(self):
    """ The HotGym dataset, only the first gym, solved using spatial
    classification. This model learns the association between the date/time
    stamp and the consumption - the model does not get consumption fed in at
    the bottom.
    """


    # Form the stream definition
    dataPath = os.path.join(self.datadir, "hotgym", "hotgym.csv")

    streamDef = dict(
      version=1,
      info="hotgym spatial classification benchmark test",
      streams=[
        dict(source="file://%s" % (dataPath),
             info="hotgym.csv",
             # NOTE: Limiting number of records to work around a bug in the
             # Streams Mgr present as of Dec 7, 2011 that shows up if you have
             # more than 50K records.
             # last_record = 49000,
             columns=["gym", "timestamp", "consumption"],
             last_record=self.splits['hotgymsc'],)
        ],
        aggregation={
        'hours' : 1,
        'fields' : [
                ('consumption', 'sum'),
                ('gym', 'first'),
                ]
          },

    )

    # Generate the experiment description
    expDesc = OPFBenchmarkRunner.EXP_COMMON.copy()
    expDesc["inferenceArgs"]["predictedField"] = "consumption"
    expDesc["inferenceArgs"]["predictionSteps"] = [0]
    expDesc.update({
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  0,
          "maxValue":  100,
        },
        { "fieldName": "gym",
          "fieldType": "string",
        },
      ],
     "iterationCount": self.__recordsToProcess,
    })

    # set the experiment name to put the experiment files in different folders
    expdir = os.path.join(self.outdir,  "hotgymsc")
    self.generateModules(expDesc,  expdir)
    self.descriptions["hotgymsc"]=(expdir, expDesc)

    return expdir


  def generateModules(self, expDesc, outdir):
    """ This calls ExpGenerator to generate a base description file and
    permutations file from expDesc.

    Parameters:
    -------------------------------------------------------------------
    expDesc:       Experiment description dict
    outDir:        Which output directory to use
    """
    # Print out example JSON for documentation purposes
    # TODO: jobParams is unused
    jobParams = dict(
      desription=expDesc
      )

    # Call ExpGenerator to generate the base description and permutations
    # files.
    shutil.rmtree(outdir, ignore_errors=True)

    # TODO: outdirv2term is not used
    outdirv2term = os.path.join(outdir, "v2Term", "base")
    outdirv2noterm = os.path.join(outdir, "v2NoTerm", "base")
    outdirdef = os.path.join(outdir, "cluster_default", "base")

    if self.__doV2Term:
      # TODO BUG: args passed to expGenerator is not defined yet
      ExpGenerator.expGenerator(args)
    args = [
      "--description=%s" % (json.dumps(expDesc)),
      "--version=v2",
      "--outDir=%s" % (outdirv2noterm)
    ]
    if self.__doV2noTerm:
      ExpGenerator.expGenerator(args)
    args = [
      "--description=%s" % (json.dumps(expDesc)),
      "--version=v2",
      "--outDir=%s" % (outdirdef)
    ]
    if self.__doClusterDef:
      ExpGenerator.expGenerator(args)


  def runV2noTerm(self, basedir, expname, searchtype, exportdict):
    v2path = os.path.join(basedir, "v2NoTerm", "base", "permutations.py")
    maxWorkers = "--maxWorkers=%d" % self.__maxNumWorkers
    searchMethod = "--searchMethod=v2"
    useTerms = "--useTerminators"
    exports = "--exports=%s" % json.dumps(exportdict)
    runString = [v2path, maxWorkers, searchMethod, exports]
    if self.__maxPermutations > 0:
      maxPermutations = "--maxPermutations=%d" % self.__maxPermutations
      runString.append(maxPermutations)
    if self.__timeout != None:
      timeout = "--timeout=%d" % self.__timeout
      runString.append(timeout)
    if self.__doEnsemble:
      ensemble = "--ensemble"
      runString.append(ensemble)
    # Disabling maxPermutations
    # if(self.__maxPermutations > 0):
    #   maxPermutations = "--maxPermutations=%d" % self.__maxPermutations
    #   pr = permutations_runner.runPermutations([v2path, maxWorkers,
    #                        searchMethod, maxPermutations, exports, timeout])
    # else:
    #   pr = permutations_runner.runPermutations([v2path, maxWorkers,
    #                        searchMethod, exports, timeout])
    pr = permutations_runner.runPermutations(runString)
    #Store results
    resultdict = self.getResultsFromJobDB(pr, expname, searchtype, basedir)
    #Save the exported custom environment variables
    self.addExportsToResults(resultdict, exportdict)
     #Store the results in the asynchronous queue
    self.__resultQ.put(resultdict)
    self.__expJobMap.put((expname, pr))

    return resultdict


  def runDefault(self, basedir, expname, searchtype, exportdict):
    path = os.path.join(basedir, "cluster_default", "base", "permutations.py")
    maxWorkers = "--maxWorkers=%d" % self.__maxNumWorkers
    searchMethod = "--searchMethod=v2"
    clusterDefault = "--clusterDefault"
    exports = "--exports=%s" % json.dumps(exportdict)
    runString = [path, maxWorkers, clusterDefault, exports]
    if self.__maxPermutations > 0:
      maxPermutations = "--maxPermutations=%d" % self.__maxPermutations
      runString.append(maxPermutations)
    if self.__timeout != None:
      timeout = "--timeout=%d" % self.__timeout
      runString.append(timeout)
    if self.__doEnsemble:
      ensemble = "--ensemble"
      runString.append(ensemble)
    # Disabling maxPermutations
    # if(self.__maxPermutations > 0):
    #   maxPermutations = "--maxPermutations=%d" % self.__maxPermutations
    #   pr = permutations_runner.runPermutations([path, maxWorkers,
    #                clusterDefault, maxPermutations, exports, timeout])
    # else:
    #   pr = permutations_runner.runPermutations([path, maxWorkers,
    #                clusterDefault, exports, timeout])
    pr = permutations_runner.runPermutations(runString)
    resultdict = self.getResultsFromJobDB(pr, expname, searchtype, basedir)
    #Save the exported custom environment variables
    self.addExportsToResults(resultdict, exportdict)
     #Store the results in the asynchronous queue
    self.__resultQ.put(resultdict)
    self.__expJobMap.put((expname, pr))
    return resultdict


  def runV2Term(self, basedir, expname, searchtype, exportdict):
    v2path = os.path.join(basedir, "v2Term", "base", "permutations.py")
    maxWorkers = "--maxWorkers=%d" % self.__maxNumWorkers
    searchMethod = "--searchMethod=v2"
    useTerms = "--useTerminators"
    exports = "--exports=%s" % json.dumps(exportdict)
    runString = [v2path, maxWorkers, searchMethod, useTerms, exports]
    if self.__maxPermutations > 0:
      maxPermutations = "--maxPermutations=%d" % self.__maxPermutations
      runString.append(maxPermutations)
    if self.__timeout != None:
      timeout = "--timeout=%d" % self.__timeout
      runString.append(timeout)
    if self.__doEnsemble:
      ensemble = "--ensemble"
      runString.append(ensemble)
    # Disabling maxPermutations
    # if(self.__maxPermutations > 0):
    #   maxPermutations = "--maxPermutations=%d" % self.__maxPermutations
    #   pr = permutations_runner.runPermutations([v2path, maxWorkers,
    #                  searchMethod, maxPermutations, useTerms, exports])
    # else:
    #   pr = permutations_runner.runPermutations([v2path, maxWorkers,
    #                  searchMethod, useTerms, exports])
    pr = permutations_runner.runPermutations(runString)
    resultdict = self.getResultsFromJobDB(pr, expname, searchtype, basedir)
    #Save the exported custom environment variables
    self.addExportsToResults(resultdict, exportdict)
     #Store the results in the asynchronous queue
    self.__resultQ.put(resultdict)
    self.__expJobMap.put((expname, pr))
    return resultdict


  def runBenchmarksSerial(self, basedir, expname, exportdict):
    # Run the Benchmarks inProc and serially
    if(self.__doV2Term):
      self.runV2Term(basedir, expname, "v2Term", exportdict)
    if(self.__doV2noTerm):
      self.runV2noTerm(basedir, expname, "v2NoTerm", exportdict)
    if(self.__doClusterDef):
      self.runDefault(basedir, expname, "cluster_default", exportdict)
    return True


  def runBenchmarksParallel(self, basedir, expname, exportdict):
    # Place the tests in a job queue
    if(self.__doV2Term):
      v2termres = self.testQ.append((self.runV2Term, [basedir, expname,
                                                      "v2Term", exportdict]))
    if(self.__doV2noTerm):
      v2notermres = self.testQ.append((self.runV2noTerm,
                                       [basedir, expname, "v2NoTerm",
                                        exportdict]))
    if(self.__doClusterDef):
      v2cldef = self.testQ.append((self.runDefault,
                                   [basedir, expname, "cluster_default",
                                    exportdict]))
    return True


  def compareBenchmarks(self, expname, searchMethod, result):
    benchmark = self.benchmarkDB[str([expname, searchMethod])]
    self.resultDB[str([expname, searchMethod])] = results
    # Make sure results are within 2.2x of the desired result.
    # This is only temporary before
    # we establish the actual desired ranges
    # TODO resulttuple is NOT defined
    return (resulttuple.metric / benchmark) < 2.20


  def assertResults(self):
    self.assertEqual(self.__failures, 0,
                    "Some benchmarks failed to meet error criteria.")


  def assertBenchmarks(self, resultdict):
    expname = resultdict['expName']
    searchMethod = resultdict['searchType']
    benchmark = self.benchmarkDB[expname + "," + searchMethod]
    self.resultDB[expname + ',' + searchMethod] = resultdict
    self.__resultList.append(resultdict)
    if (resultdict['metric'] / benchmark[0]) > (1+benchmark[1]):
      print "HyperSearch %s on %s benchmark did not match " \
        "the expected value. (Expected: %f    Observed:  %f)" % \
        (searchMethod, expname, benchmark[0], resultdict['metric'])
      self.__failures+=1
    return


  def getJobParamsFromJobDB(self, jobID):
    jobInfo = cjdao.ClientJobsDAO.get().jobInfo(jobID)
    pars = jobInfo.params
    params = json.loads(pars)
    return params


  def checkPythonScript(self, scriptAbsPath):
    assert os.path.isabs(scriptAbsPath)

    assert os.path.isfile(scriptAbsPath) , (
        "Expected python script to be present here: <%s>" % scriptAbsPath)

    # Test viability of the file as a python script by loading it
    # An exception will be raised if this fails
    mod = imp.load_source('test', scriptAbsPath)
    return mod


  def testOPFBenchmarks(self):
    """Run the entire set of OPF benchmark experiments
    """
    # Check for benchmark misspellings
    for bm in self.listOfBenchmarks:
      if not bm in self.allBenchmarks:
        raise Exception("Unknown benchmark %s" % bm)

    # Set up FIFO queue for handling the different directories that are created
    # for the tests
    fifodirs = deque()
    baseoutdir = self.outdir
    iterations = self.iterations
    exportDicts = self.setUpExportDicts()
    for iter in range(iterations):
      for exports in exportDicts:
        if len(exportDicts)>1:
          prependDict = exports
        else:
          prependDict = dict()
        if self.iterations > 1:
          prependDict["iteration"] = iter
        prepend = self.generatePrependPath(prependDict)
        self.outdir = os.path.join(baseoutdir, prepend)
        if("sine" in self.listOfBenchmarks):
          tmpsine = self.benchmarkSine()
          fifodirs.append(tmpsine)
        if("hotgym" in self.listOfBenchmarks):
          tmphotgym = self.benchmarkHotGym()
          fifodirs.append(tmphotgym)
        if("twovars" in self.listOfBenchmarks):
          tmptwovars = self.benchmarkTwoVars()
          fifodirs.append(tmptwovars)
        if("twovars2" in self.listOfBenchmarks):
          tmptwovars2 = self.benchmarkTwoVarsSquare()
          fifodirs.append(tmptwovars2)
        if("threevars" in self.listOfBenchmarks):
          tmpthreevars = self.benchmarkThreeVars()
          fifodirs.append(tmpthreevars)
        if("fourvars" in self.listOfBenchmarks):
          tmpfourvars = self.benchmarkFourVars()
          fifodirs.append(tmpfourvars)
        if("categories" in self.listOfBenchmarks):
          tmpcategories = self.benchmarkCategories()
          fifodirs.append(tmpcategories)
        if("sawtooth" in self.listOfBenchmarks):
          tmpcategories = self.benchmarkSawtooth()
          fifodirs.append(tmpcategories)
        if("hotgymsc" in self.listOfBenchmarks):
          tmphotgymsc = self.benchmarkHotGymSC()
          fifodirs.append(tmphotgymsc)
    self.outdir = baseoutdir
    self.syncFiles()
    if self.filesOnly:
      return
    if(self.maxConcurrentJobs==1):
      self.runBenchmarks = self.runBenchmarksSerial
    else:
      self.runBenchmarks = self.runBenchmarksParallel
    for iter in range(iterations):
      for exports in exportDicts:
        if("sine" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "sine", exports))
        if("hotgym" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "hotgym", exports))
        if("twovars" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "twovars", exports))
        if("twovars2" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "twovars2", exports))
        if("threevars" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "threevars", exports))
        if("fourvars" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "fourvars", exports))
        if("categories" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "categories", exports))
        if("sawtooth" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "sawtooth", exports))
        if("hotgymsc" in self.listOfBenchmarks):
          assert(self.runBenchmarks(fifodirs.popleft(), "hotgymsc", exports))

    # Poll processes until they all finish.
    self.runJobs(self.maxConcurrentJobs)
    # Disabled removing the temporary directory
    if self.__trainFraction < 1.0:
      self.runProductionWorkers()
      self.waitForProductionWorkers()
    self.printResults()
    self.assertResults()

  def tearDown(self):
    if self.isSaveResults:
      self.saveResults()
    else:
      self.removeTmpDirs()
    print "Done with all tests"



if __name__ == "__main__":
  helpString = (
      "Usage: \n\n"
      "runOPFBenchmarks --outdir DIRNAME  "
      "// for simple v2 with Terminators benchmarks  \n"
      "runOPFBenchmarks --outdir DIRNAME --searches=v2noTerm, v2Term     "
      "//   to run all searches   \n"
      "Specify a DIRNAME if you want to keep the results, otherwise it will "
      "be done in a temp directory \n"
      )
  # ArgParser
  parser = OptionParser(usage=helpString)
  parser.add_option("--outdir", dest="outdir", default="artifacts",
                    type="string", help = "Specify a dirname if you want to"
                    "keep the results [default=%default].")
  parser.add_option( "--searches", dest="searches", default="v2NoTerm",
                     type="string",  help="Which searches to run,"
                     "specify as a list "
                     "can be composed of v2noTerm, v2Term, cluster_default"
                     "(ie. --searches=v2noTerm)"
                     "[default: %default].")
  parser.add_option("--maxPermutations", dest="maxPermutations", default= -1,
                    type="int", help="Maximum number of models to search."
                    "-1 for no limit to the number of models. "
                    "[default: %default].")
  parser.add_option("--recsToProcess", dest="recsToProcess", default= -1,
                    type="int", help="Maximum number of records to use as data"
                    " from each experiment. "
                    "-1 for the entire dateset [default: %default].")
  parser.add_option("--maxConcurrentJobs", dest="maxConcurrentJobs",
                    default= 4, type="int",
                    help="Maximum number of tests to run in parallel"
                    "each will be allocated maxWorkers number of workers. "
                    "[default: %default].")
  parser.add_option("--maxWorkers", dest="maxWorkers", default=None, type="int",
                    help="Maximum number of workers to use simultaneously"
                    "[default: %default].")
  parser.add_option("--benchmarks", dest="benchmarks",
                    default="hotgymsc",
                    type="string",
                    help="Which tests to run choose from "
                    "hotgym, sine, "
                    "hotgymsc [default: %default].")
  parser.add_option("--maxBranchings", dest="maxBranchings", default=None,
                    type="string", help="What is the maximum number of fields "
                    "to add per sprint. This dictates how many fields"
                    "are used at each sprint to generate the new swarms."
                    " Can be a comma separated list for the "
                    "different branching limits that you want to test. "
                    "All means no limit on branching, None is config default "
                    "[default: %default].")
  parser.add_option("--maxParticles", dest="maxParticles", default=None,
                    type="string", help="Maximum number of particles per "
                    "swarm to launch. None is config default"
                    "[default: %default].")
  parser.add_option("--iterations", dest="iterations", default=1, type="int",
                    help="Number of times to run each test"
                    "[default: %default].")
  parser.add_option("--generateFilesOnly", dest="filesOnly", default=False,
                    action="store_true", help="Setting this to true will only "
                    "generate the permutations and description files."
                    " No searches will be run. [default: %default].")
  parser.add_option("--useReconstruction", dest="useReconstruction",
                    action="store_true", help="Setting this to true will"
                    " use the old SP-reconstruction method to "
                    "make predictions. Used for side-by-side comparisons")
  parser.add_option("--timeout", dest="timeout", default=25, type="int",
                    help="The timeout for each individual search measured "
                    "in minutes. If a search reaches this timeout all searches"
                    " are cancelled")
  parser.add_option("--metaOptimize", dest="metaOptimize", default=None,
                    type="string", help="Dictionary of default swarm "
                    "parameters you want to modify. Options are inertia, "
                    "cogRate, socRate, minParticlesPerSwarm "
                    "[default: %default].")
  parser.add_option("--trainFraction", dest="trainFraction", default=1.0,
                    type="float", help="Setting this to true will swarm on"
                    " x*100% of the data and run a production worker on "
                    "(1-x)*100% of the data. This is to see if the swarm is "
                    "overfitting [default: %default].")
  parser.add_option("--ensemble", dest="ensemble", default=False,
                    action="store_true", help="Run an ensemble instead of HS"
                    " for this job [default: %default].")

  options, remainingArgs = parser.parse_args()

  # Set up module
  print "\nCURRENT DIRECTORY:", os.getcwd()
  if not os.path.isdir(options.outdir):
    options.outdir = tempfile.mkdtemp()
    print "Provided directory to store Benchmark files is invalid.",
    print "Now storing in <%s> and then deleting" % options.outdir
    OPFBenchmarkRunner.isSaveResults = False
  OPFBenchmarkRunner.outdir = os.path.abspath(os.path.join(options.outdir,
                                                           "BenchmarkFiles"))
  if os.path.isdir(OPFBenchmarkRunner.outdir):
    shutil.rmtree(OPFBenchmarkRunner.outdir)
  os.mkdir(OPFBenchmarkRunner.outdir)

  OPFBenchmarkRunner.setMetaOptimize(options.metaOptimize)
  OPFBenchmarkRunner.setMaxNumWorkers(options.maxWorkers)
  OPFBenchmarkRunner.setTrainFraction(options.trainFraction)
  OPFBenchmarkRunner.setNumRecords(options.recsToProcess)
  OPFBenchmarkRunner.setTimeout(options.timeout)
  OPFBenchmarkRunner.setMaxPermutations(options.maxPermutations)
  if options.ensemble:
    OPFBenchmarkRunner.setDoEnsemble()

  if options.useReconstruction:
    OPFBenchmarkRunner.EXP_COMMON["inferenceType"] = \
                       InferenceType.TemporalNextStep
  OPFBenchmarkRunner.setupTrainTestSplits()

  OPFBenchmarkRunner.datadir = os.path.join('extra')


  tests = options.searches
  if not OPFBenchmarkRunner.getTests(tests):
    raise Exception("Incorrect formatting of option \n %s" % helpString)

  OPFBenchmarkRunner.listOfBenchmarks = options.benchmarks.lower().split(',')
  OPFBenchmarkRunner.filesOnly = options.filesOnly
  OPFBenchmarkRunner.maxParticles = options.maxParticles
  OPFBenchmarkRunner.maxBranchings = options.maxBranchings
  OPFBenchmarkRunner.iterations = options.iterations
  OPFBenchmarkRunner.maxConcurrentJobs = options.maxConcurrentJobs

  unittest.main(argv=[sys.argv[0]] + remainingArgs)
