import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy.linalg as la
import warnings

outFile = 'predictions.png'
opfFile = '../opf/predictions.csv'
netFile = '../networkapi/predictions.csv'
algFile = '../algo/predictions.csv'


if not os.path.exists(opfFile):
  raise RuntimeError('You must run "opf/complete-example.py" first.')
if not os.path.exists(netFile):
  raise RuntimeError('You must run "networkapi/complete-example.py" first.')
if not os.path.exists(algFile):
  raise RuntimeError('You must run "algo/complete-example.py" first.')


opfResults = pd.read_csv(opfFile)
opfResults['error'] = opfResults.input.sub(opfResults.prediction).apply(la.norm)

netResults = pd.read_csv(netFile)
netResults['error'] = netResults.input.sub(netResults.prediction).apply(la.norm)

algResults = pd.read_csv(algFile)
algResults['error'] = algResults.input.sub(algResults.prediction).apply(la.norm)


f, ax = plt.subplots(nrows=3, ncols=2, figsize=(12,7))
ax[0][0].plot(opfResults.input, label='input')
ax[0][0].plot(opfResults.prediction, label='predictions')
ax[0][0].legend()
ax[0][0].set_title('Predictions for OPF Example')

ax[1][0].plot(netResults.input, label='input')
ax[1][0].plot(netResults.prediction, label='predictions')
ax[1][0].legend()
ax[1][0].set_title('Predictions for Network API Example')

ax[2][0].plot(algResults.input, label='input')
ax[2][0].plot(algResults.prediction, label='predictions')
ax[2][0].legend()
ax[2][0].set_title('Predictions for Algorithms Example')

ax[0][1].plot(opfResults.error)
ax[0][1].set_title('OPF Prediction Error')
ax[0][1].set_ylim(0,100)

ax[1][1].plot(netResults.error)
ax[1][1].set_title('Network API Prediction Error')
ax[1][1].set_ylim(0,100)

ax[2][1].plot(algResults.error)
ax[2][1].set_title('Algorithms Prediction Error')
ax[2][1].set_ylim(0,100)
plt.tight_layout()

plt.savefig('predictions.png')
print '\nFigure saved: %s\n' % outFile

print 'OPF RMSE:',  opfResults.error.mean()
print 'Network API RMSE:',  netResults.error.mean()
print 'Algorithms RMSE:',  algResults.error.mean()

if opfResults.error.mean() != netResults.error.mean():
  warnings.warn('OPF and Network API predictions are different.')
if opfResults.error.mean() != algResults.error.mean():
  warnings.warn('OPF and Algorithms predictions are different.')
if netResults.error.mean() != algResults.error.mean():
  warnings.warn('Algorithms and Network API predictions are different.')
