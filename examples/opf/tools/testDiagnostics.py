import numpy as np



def printMatrix(inputs, spOutput):
  ''' (i,j)th cell of the diff matrix will have the number of inputs for which the input and output
  pattern differ by i bits and the cells activated differ at j places.
  Parameters:
  --------------------------------------------------------------------
  inputs:                the input encodings
  spOutput:              the coincidences activated in response to each input
  '''
  from pylab import matplotlib as mat

  w=len(np.nonzero(inputs[0])[0])
  numActive=len(np.nonzero(spOutput[0])[0])
  matrix = np.zeros([2*w+1,2*numActive+1])
    
  for x in xrange(len(inputs)):
    i = [_hammingDistance(inputs[x], z) for z in inputs[x:]]
    j = [_hammingDistance(spOutput[x], a) for a in spOutput[x:]]
    for p, q in zip(i,j):
      matrix[p,q]+=1
    for y in xrange(len(matrix))  :
      matrix[y]=[max(10*x, 100) if (x<100 and x>0) else x for x in matrix[y]]
  
  cdict = {'red':((0.0,0.0,0.0),(0.01,0.7,0.5),(0.3,1.0,0.7),(1.0,1.0,1.0)),\
          'green': ((0.0,0.0,0.0),(0.01,0.7,0.5),(0.3,1.0,0.0),(1.0,1.0,1.0)),\
          'blue': ((0.0,0.0,0.0),(0.01,0.7,0.5),(0.3,1.0,0.0),(1.0,0.5,1.0))}
  
  my_cmap = mat.colors.LinearSegmentedColormap('my_colormap',cdict,256)
  pyl=mat.pyplot
  pyl.matshow(matrix, cmap = my_cmap)
  pyl.colorbar()
  pyl.ylabel('Number of bits by which the inputs differ') 
  pyl.xlabel('Number of cells by which input and output differ')
  pyl.title('The difference matrix')
  pyl.show()



def _hammingDistance(s1, s2):
  """Hamming distance between two numpy arrays s1 and s2"""
  return sum(abs(s1-s2))
  