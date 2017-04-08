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

nPointsToPlot = min(len(opfResults), len(netResults), len(algResults))

plt.figure(figsize=(12,7))
ax11 = plt.subplot(3, 2, 1)
ax11.plot(opfResults.input, label='input')
ax11.plot(opfResults.prediction, label='predictions')
ax11.legend()
ax11.set_title('OPF Predictions')

ax21 = plt.subplot(3, 2, 3, sharex=ax11, sharey=ax11)
ax21.plot(netResults.input, label='input')
ax21.plot(netResults.prediction, label='predictions')
ax21.legend()
ax21.set_title('Network API Predictions')

ax31 = plt.subplot(3, 2, 5, sharex=ax11, sharey=ax11)
ax31.plot(algResults.input, label='input')
ax31.plot(algResults.prediction, label='predictions')
ax31.legend()
ax31.set_title('Algorithms Predictions')

opfRMSE = opfResults.error.mean()
netRMSE = netResults.error.mean()
algRMSE = algResults.error.mean()

ax12 = plt.subplot(3, 2, 2, sharex=ax11, sharey=ax11)
ax12.plot(opfResults.error)
ax12.set_title('OPF Prediction Error (RMSE: %.2f)' % opfRMSE)

ax22 = plt.subplot(3, 2, 4, sharex=ax11, sharey=ax11)
ax22.plot(netResults.error)
ax22.set_title('Network API Prediction Error (RMSE: %.2f)' % netRMSE)

ax32 = plt.subplot(3, 2, 6, sharex=ax11, sharey=ax11)
ax32.plot(algResults.error)
ax32.set_title('Algorithms Prediction Error (RMSE: %.2f)' % algRMSE)

plt.xlim(0, nPointsToPlot)
plt.tight_layout()

plt.savefig('predictions.png')
print '\nFigure saved: %s\n' % outFile

print 'OPF RMSE:', opfRMSE
print 'Network API RMSE:', netRMSE
print 'Algorithms RMSE:',  algRMSE

if opfResults.error.mean() != netResults.error.mean():
  warnings.warn('OPF and Network API predictions are different.')
if opfResults.error.mean() != algResults.error.mean():
  warnings.warn('OPF and Algorithms predictions are different.')
if netResults.error.mean() != algResults.error.mean():
  warnings.warn('Algorithms and Network API predictions are different.')

plt.show()