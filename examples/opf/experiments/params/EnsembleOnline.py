import random
import multiprocessing
import numpy as np
from nupic.frameworks.opf import opfhelpers
from nupic.frameworks.opf.client import Client
from random import shuffle
from random import randrange, uniform
import copy

windowSize=36
r=30
predictedField='pounds' 
inertia=0.25
socRate=1.0
class Worker(multiprocessing.Process):

  def __init__(self, work_queue, result_queue, stableSize, windowSize, predictedField, modeldata, iden):
    multiprocessing.Process.__init__(self)
    # job management 
    self.work_queue = work_queue
    self.result_queue = result_queue
    self.kill_received = False
    #Model State
    self.stableSize=stableSize
    self.windowSize=windowSize
    self.stableUpdateStepSize=1
    self.iden=iden
    self.truth=[]
    self.predictedField=predictedField
    self.modeldata=modeldata
    self.numModels=len(modeldata)
    self.M={}
    self.Scores={}
    self.predictionStreams={}
    self.median=True
    self.index=-1
    self.modelCapacity=len(modelData)
      
 
  def run(self):
      self.initM(modelData)
      while not self.kill_received:
        jobaux = self.work_queue.get()
        command=jobaux[0]
        if command=='predict':
          self.index=self.index+1
          self.updateModelStats()
          self.result_queue.put([(self.Scores[m], self.predictionStreams[m][-1], self.truth[self.index], m) for m in self.M.keys()])
        if command=='getPredictionStreams':
          self.result_queue.put(dict([(m, self.predictionStreams[m][:-windowSize]) for m in self.predictionStreams.keys()]))
        if command=='delete':
          delList=jobaux[1]
          for d in delList:
            if(d in self.M):
              del self.M[d]
              del self.Scores[d]
              del self.predictionStreams[d]
              print 'deleted Model'+str(d)+" in process "+str(self.iden)
          print "number of models remaining in "+str(self.iden)+": "+str(len(self.M))
          self.result_queue.put(self.iden)
        if command=='getAAEs':
          self.result_queue.put([(m, computeAAE(self.truth, self.predictionStreams[m],r ), self.getModelState(self.M[m]), self.M[m]['modelDescription']) for m in self.M.keys()])
        if command=='addPSOVariants':
          for t in jobaux[1]:
            if(t[0]==self.iden):
              name=t[2]
              modelDescription=t[1][0]
              x=t[1][1]
              v=t[1][2]
              self.M[name]={}
              self.M[name]['modelDescription']=modelDescription
              self.M[name]['client']=Client(**modelDescription)
              self.M[name]['alive']=True
              self.M[name]['start']=0
              self.M[name]['end']=None
              self.M[name]['x']=x
              self.M[name]['v']=v
              self.Scores[name]=10000
              self.predictionStreams[name]=[0,]
              print "added new model "+str(name)+" to process"+str(self.iden)
            
       
 
        # store the result
        
  def getModelState(self, d):
    return d['x'], d['v']
          
  def initM(self, modelDatList):
    for modelData in modelDatList:
        name=modelData[0]
        self.M[name]={}
        self.M[name]['modelDescription']=modelData[1]
        self.M[name]['client']=Client(**modelData[1])
        alpha=modelData[1]['modelConfig']['modelParams']['clParams']['alpha']
        n=0
        for encoder in modelData[1]['modelConfig']['modelParams']['sensorParams']['encoders']:
          if encoder['name']==predictedField:
            n=encoder['n']
        synPermInactiveDec=modelData[1]['modelConfig']['modelParams']['spParams']['synPermInactiveDec']
        activationThreshold=modelData[1]['modelConfig']['modelParams']['tpParams']['activationThreshold']
        pamLength=modelData[1]['modelConfig']['modelParams']['tpParams']['pamLength']
        self.M[name]['x']=np.array([alpha, n,synPermInactiveDec,activationThreshold,  pamLength ])

        vAlpha=uniform(0.01, 0.15)
        vN=randrange(30, 200, 5)
        vSynPermInactiveDec=uniform(0.01, 0.15)
        vActivationThreshold=randrange(12, 17, 1)
        vPamLength=randrange(1, 6, 1)
        self.M[name]['v']=np.array([vAlpha, vN,vSynPermInactiveDec,vActivationThreshold,vPamLength])
        self.M[name]['alive']=True
        self.M[name]['start']=0
        self.M[name]['end']=None
        self.Scores[name]=10000
        self.predictionStreams[name]=[0,]

        
      
  def updateModelStats(self):
    updatedTruth=False
    for m in self.M.keys():
      truth, prediction=self.M[m]['client'].nextTruthPrediction(self.predictedField)
      if(not updatedTruth):
        self.truth.append(truth)
        updatedTruth=True      
      self.predictionStreams[m].append(prediction)
      self.Scores[m]=computeAAE(self.truth, self.predictionStreams[m],windowSize)
      




     
def getStableVote(scores, stableSize, votes, currModel):
  scores = sorted(scores, key=lambda t: t[0])[:stableSize]
  median=True
  if not median:
    for s in scores:
      if s[3]==currModel:
        print [(score[0], score[3]) for score in scores]
      
        return s[1], currModel
    print [(s[0], s[3]) for s in scores], "switching voting Model!"
    return scores[0][1], scores[0][3]
  else:
    print [(s[0], s[3]) for s in scores]
    voters = sorted(scores, key=lambda t: t[1])
    for voter in voters:
      votes[voter[3]]=votes[voter[3]]+1
    vote=voters[int(stableSize/2)][1]
    return vote, currModel
  
        
def getFieldPermutations(config, predictedField):
  encoders=config['modelParams']['sensorParams']['encoders']
  encoderList=[]
  for encoder in encoders:
    if encoder==None:
      continue
    if encoder['name']==predictedField:
      encoderList.append([encoder])
      for e in encoders:
        if e==None:
          continue
        if e['name'] != predictedField:
          encoderList.append([encoder, e])
  return encoderList
              
        
def getModelDescriptionLists(numProcesses, experiment):
    config, control = opfhelpers.loadExperiment(experiment)
    encodersList=getFieldPermutations(config, 'pounds')
    ns=range(50, 140, 120)
    clAlphas=np.arange(0.01, 0.16, 0.104)
    synPermInactives=np.arange(0.01, 0.16, 0.105)
    tpPamLengths=range(5, 8, 2)
    tpSegmentActivations=range(13, 17, 12)
    
    if control['environment'] == 'opfExperiment':
      experimentTasks = control['tasks']
      task = experimentTasks[0]
      datasetURI = task['dataset']['streams'][0]['source']

    elif control['environment'] == 'nupic':
      datasetURI = control['dataset']['streams'][0]['source']

    metricSpecs = control['metrics']

    datasetPath = datasetURI[len("file://"):]
    ModelSetUpData=[]
    name=0
    
    for n in ns:
      for clAlpha in clAlphas:
        for synPermInactive in synPermInactives:
          for tpPamLength in tpPamLengths:
            for tpSegmentActivation in tpSegmentActivations:
              for encoders in encodersList:
                encodersmod=copy.deepcopy(encoders)
                configmod=copy.deepcopy(config)
                configmod['modelParams']['sensorParams']['encoders']=encodersmod
                configmod['modelParams']['clParams']['alpha']=clAlpha
                configmod['modelParams']['spParams']['synPermInactiveDec']=synPermInactive
                configmod['modelParams']['tpParams']['pamLength']=tpPamLength
                configmod['modelParams']['tpParams']['activationThreshold']=tpSegmentActivation
                for encoder in encodersmod:
                  if encoder['name']==predictedField:
                    encoder['n']=n
                
                ModelSetUpData.append((name,{'modelConfig':configmod, 'inferenceArgs':control['inferenceArgs'], 'metricSpecs':metricSpecs, 'sourceSpec':datasetPath,'sinkSpec':None,}))
                name=name+1
              #print modelInfo['modelConfig']['modelParams']['tpParams']
              #print modelInfo['modelConfig']['modelParams']['sensorParams']['encoders'][4]['n']
    print "num Models"+str( len(ModelSetUpData))
    
    shuffle(ModelSetUpData)
    #print [ (m[1]['modelConfig']['modelParams']['tpParams']['pamLength'], m[1]['modelConfig']['modelParams']['sensorParams']['encoders']) for m in ModelSetUpData]       
    return list(chunk(ModelSetUpData,numProcesses))

    
def chunk(l, n):
    """ Yield n successive chunks from l.
    """
    newn = int(1.0 * len(l) / n + 0.5)
    for i in xrange(0, n-1):
        yield l[i*newn:i*newn+newn]
    yield l[n*newn-newn:]

def command(command, work_queues, aux):
  for queue in work_queues:
    queue.put((command, aux))


def getDuplicateList(streams, delta):
  delList=[]
  keys=streams.keys()
  for key1 in keys:
    if key1 in streams:
      for key2 in streams.keys():
        if(key1 !=key2):
          print 'comparing model'+str(key1)+" to "+str(key2)
          dist=sum([(a-b)**2 for a, b in zip(streams[key1], streams[key2])])
          print dist
          if(dist<delta):
            delList.append(key2)
            del streams[key2]
  return delList
    
def slice_sampler(px, N = 1, x = None):
    """
    Provides samples from a user-defined distribution.
    
    slice_sampler(px, N = 1, x = None)
    
    Inputs:
    px = A discrete probability distribution.
    N  = Number of samples to return, default is 1
    x  = Optional list/array of observation values to return, where prob(x) = px.

    Outputs:
    If x=None (default) or if len(x) != len(px), it will return an array of integers
    between 0 and len(px)-1. If x is supplied, it will return the
    samples from x according to the distribution px.    
    """
    values = np.zeros(N, dtype=np.int)
    samples = np.arange(len(px))
    px = np.array(px) / (1.*sum(px))
    u = uniform(0, max(px))
    for n in xrange(N):
        included = px>=u
        choice = random.sample(range(np.sum(included)), 1)[0]
        values[n] = samples[included][choice]
        u = uniform(0, px[included][choice])
    if x:
        if len(x) == len(px):
            x=np.array(x)
            values = x[values]
        else:
            print "px and x are different lengths. Returning index locations for px."
    
    return values
    
    
def getPSOVariants(modelInfos, votes, n):
  # get x, px lists for sampling 
  norm=sum(votes.values())
  xpx =[(m, float(votes[m])/norm) for m in votes.keys()] 
  x,px = [[z[i] for z in xpx] for i in (0,1)]
  #sample form set of models
  variantIDs=slice_sampler(px, n, x)
  print "variant IDS"
  print variantIDs
  #best X
  x_best=modelInfos[0][2][0]
  # create PSO variates of models
  modelDescriptions=[]
  for variantID in variantIDs:
    t=modelInfos[[i for i, v in enumerate(modelInfos) if v[0] == variantID][0]]
    x=t[2][0]
    v=t[2][1]
    print "old x"
    print x
    modelDescriptionMod=copy.deepcopy(t[3])
    configmod=modelDescriptionMod['modelConfig']
    v=inertia*v+socRate*np.random.random_sample(len(v))*(x_best-x)
    x=x+v
    print "new x"
    print x    
    configmod['modelParams']['clParams']['alpha']=max(0.01, x[0])
    configmod['modelParams']['spParams']['synPermInactiveDec']=max(0.01, x[2])
    configmod['modelParams']['tpParams']['pamLength']=int(round(max(1, x[4])))
    configmod['modelParams']['tpParams']['activationThreshold']=int(round(max(1, x[3])))
    for encoder in configmod['modelParams']['sensorParams']['encoders']:
      if encoder['name']==predictedField:
        encoder['n']=int(round(max(encoder['w']+1, x[1]) ))
    modelDescriptions.append((modelDescriptionMod, x, v))
  return modelDescriptions 
            
    
def computeAAE(truth, predictions, windowSize):
  windowSize=min(windowSize, len(truth))
  zipped=zip(truth[-windowSize:], predictions[-windowSize-1:])
  AAE=sum([abs(a - b) for a, b in zipped])/windowSize
  return AAE
 
    
              
if __name__ == "__main__":
    cutPercentage=0.1
    currModel=0
    stableSize=3
    delta=1
    predictedField='pounds'
    truth=[]
    ensemblePredictions=[0,]
    divisor=4
    ModelSetUpData=getModelDescriptionLists(divisor, './')
    num_processes=len(ModelSetUpData)
    print num_processes 
    work_queues=[]
    votes={}
    votingParameterStats={"tpSegmentActivationThreshold":[], "tpPamLength":[], "synPermInactiveDec":[], "clAlpha":[], "numBuckets":[]}  
    # create a queue to pass to workers to store the results
    result_queue = multiprocessing.Queue(len(ModelSetUpData))
 
    # spawn workers
    workerName=0
    modelNameCount=0
    for modelData in ModelSetUpData:
        print len(modelData)
        modelNameCount+=len(modelData)
        work_queue= multiprocessing.Queue()
        work_queues.append(work_queue)
        worker = Worker(work_queue, result_queue, stableSize, windowSize, predictedField, modelData, workerName)
        worker.start()
        workerName=workerName+1
        
    #init votes dict
    for dataList in ModelSetUpData:
      for data in dataList:
        votes[data[0]]=0
      
    
    for i in range(2120):
      
      command('predict', work_queues, i)
      scores=[]
      for j in range(num_processes):
        subscore=result_queue.get()
        scores.extend(subscore)
      print ""
      print i
      ensemblePrediction, currModel=getStableVote(scores, stableSize, votes, currModel)
      ensemblePredictions.append(ensemblePrediction)
      truth.append(scores[0][2])
      print  computeAAE(truth,ensemblePredictions, windowSize), int(currModel)
      assert(result_queue.empty())
      if i%r==0 and i!=0: #refresh ensemble
        assert(result_queue.empty())
        #get AAES of models over last i records
        command('getAAEs', work_queues, None)
        AAEs=[]
        for j in range(num_processes):
          subAAEs=result_queue.get()
          AAEs.extend(subAAEs)
        AAEs=sorted(AAEs, key=lambda t: t[1])
        numToDelete=int(round(cutPercentage*len(AAEs)))
        print "Single Model AAES"
        print [(aae[0], aae[1]) for aae in AAEs]
        print "Ensemble AAE"
        print computeAAE(truth, ensemblePredictions, r)
        #add bottom models to delList
        print "Vote counts"
        print votes
        delList=[t[0] for t in AAEs[-numToDelete:]]   
        print "delList"     
        print delList
        #find duplicate models(now unnecessary)
        #command('getPredictionStreams', work_queues, None)
        #streams={}
        #for j in range(num_processes):
        #  subList=result_queue.get()
        #  streams.update(subList)
        #delList.extend(getDuplicateList(streams, delta))
        #print delList
        command('delete', work_queues, delList)
        for iden in delList:
          del votes[iden]
        print votes  
        #wait for deletion to finish and collect processIndices for addition
        processIndices=[]
        for j in range(num_processes):
          processIndices.append( result_queue.get())
        # pick new set of models for PSO variants
        newModelDescriptions=getPSOVariants(AAEs, votes, len(delList))
        assert(result_queue.empty())
        #send new model dscriptions to queue and have processess pick them up
        aux=[]
        for i in range(len(newModelDescriptions)):
          votes[modelNameCount]=0
          aux.append((processIndices[i],newModelDescriptions[i],modelNameCount) )
          modelNameCount=modelNameCount+1
        
        command('addPSOVariants', work_queues, aux)
        #set votes to 0
        for key in votes.keys():
          votes[key]=0
                
        
      
 
    print "AAE over full stream"
    print computeAAE(truth, ensemblePredictions, len(truth))
    print "AAE1000"
    print computeAAE(truth, ensemblePredictions, 1000)
 
    
