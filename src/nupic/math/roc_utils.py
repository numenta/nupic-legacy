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
"""
Utility functions to compute ROC (Receiver Operator Characteristic) curves
and AUC (Area Under the Curve).

The ROCCurve() and AreaUnderCurve() functions are based on the roc_curve()
and auc() functions found in metrics.py module of scikit-learn
(http://scikit-learn.org/stable/). Scikit-learn has a BSD license (3 clause).

Following is the original license/credits statement from the top of the
metrics.py file:

# Authors: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#          Mathieu Blondel <mathieu@mblondel.org>
#          Olivier Grisel <olivier.grisel@ensta.org>
# License: BSD Style.

"""

import numpy as np



def ROCCurve(y_true, y_score):
    """compute Receiver operating characteristic (ROC)

    Note: this implementation is restricted to the binary classification task.

    Parameters
    ----------

    y_true : array, shape = [n_samples]
        true binary labels

    y_score : array, shape = [n_samples]
        target scores, can either be probability estimates of
        the positive class, confidence values, or binary decisions.

    Returns
    -------
    fpr : array, shape = [>2]
        False Positive Rates

    tpr : array, shape = [>2]
        True Positive Rates

    thresholds : array, shape = [>2]
        Thresholds on y_score used to compute fpr and tpr

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn import metrics
    >>> y = np.array([1, 1, 2, 2])
    >>> scores = np.array([0.1, 0.4, 0.35, 0.8])
    >>> fpr, tpr, thresholds = metrics.roc_curve(y, scores)
    >>> fpr
    array([ 0. ,  0.5,  0.5,  1. ])

    References
    ----------
    http://en.wikipedia.org/wiki/Receiver_operating_characteristic

    """
    y_true = np.ravel(y_true)
    classes = np.unique(y_true)

    # ROC only for binary classification
    if classes.shape[0] != 2:
        raise ValueError("ROC is defined for binary classification only")

    y_score = np.ravel(y_score)

    n_pos = float(np.sum(y_true == classes[1]))  # nb of true positive
    n_neg = float(np.sum(y_true == classes[0]))  # nb of true negative

    thresholds = np.unique(y_score)
    neg_value, pos_value = classes[0], classes[1]

    tpr = np.empty(thresholds.size, dtype=np.float)  # True positive rate
    fpr = np.empty(thresholds.size, dtype=np.float)  # False positive rate

    # Build tpr/fpr vector
    current_pos_count = current_neg_count = sum_pos = sum_neg = idx = 0

    signal = np.c_[y_score, y_true]
    sorted_signal = signal[signal[:, 0].argsort(), :][::-1]
    last_score = sorted_signal[0][0]
    for score, value in sorted_signal:
        if score == last_score:
            if value == pos_value:
                current_pos_count += 1
            else:
                current_neg_count += 1
        else:
            tpr[idx] = (sum_pos + current_pos_count) / n_pos
            fpr[idx] = (sum_neg + current_neg_count) / n_neg
            sum_pos += current_pos_count
            sum_neg += current_neg_count
            current_pos_count = 1 if value == pos_value else 0
            current_neg_count = 1 if value == neg_value else 0
            idx += 1
            last_score = score
    else:
        tpr[-1] = (sum_pos + current_pos_count) / n_pos
        fpr[-1] = (sum_neg + current_neg_count) / n_neg

    # hard decisions, add (0,0)
    if fpr.shape[0] == 2:
        fpr = np.array([0.0, fpr[0], fpr[1]])
        tpr = np.array([0.0, tpr[0], tpr[1]])
    # trivial decisions, add (0,0) and (1,1)
    elif fpr.shape[0] == 1:
        fpr = np.array([0.0, fpr[0], 1.0])
        tpr = np.array([0.0, tpr[0], 1.0])

    return fpr, tpr, thresholds



def AreaUnderCurve(x, y):
    """Compute Area Under the Curve (AUC) using the trapezoidal rule

    Parameters
    ----------
    x : array, shape = [n]
        x coordinates

    y : array, shape = [n]
        y coordinates

    Returns
    -------
    auc : float

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn import metrics
    >>> y = np.array([1, 1, 2, 2])
    >>> pred = np.array([0.1, 0.4, 0.35, 0.8])
    >>> fpr, tpr, thresholds = metrics.roc_curve(y, pred)
    >>> metrics.auc(fpr, tpr)
    0.75

    """
    #x, y = check_arrays(x, y)
    if x.shape[0] != y.shape[0]:
        raise ValueError('x and y should have the same shape'
                         ' to compute area under curve,'
                         ' but x.shape = %s and y.shape = %s.'
                         % (x.shape, y.shape))
    if x.shape[0] < 2:
        raise ValueError('At least 2 points are needed to compute'
                         ' area under curve, but x.shape = %s' % x.shape)

    # reorder the data points according to the x axis
    order = np.argsort(x)
    x = x[order]
    y = y[order]

    h = np.diff(x)
    area = np.sum(h * (y[1:] + y[:-1])) / 2.0
    return area



def _printNPArray(x, precision=2):
  format = "%%.%df" % (precision)
  for elem in x:
    print format % (elem),
  print



def _test():
  """
  This is a toy example, to show the basic functionality:

  The dataset is:

  actual    prediction
  -------------------------
  0          0.1
  0          0.4
  1          0.5
  1          0.3
  1          0.45

  Some ROC terminology:
  A True Positive (TP) is when we predict TRUE and the actual value is 1.

  A False Positive (FP) is when we predict TRUE, but the actual value is 0.

  The True Positive Rate (TPR) is TP/P, where P is the total number of actual
  positives (3 in this example, the last 3 samples).

  The False Positive Rate (FPR) is FP/N, where N is the total number of actual
  negatives (2 in this example, the first 2 samples)


  Here are the classifications at various choices for the threshold. The
  prediction is TRUE if the predicted value is >= threshold and FALSE otherwise.

  actual    pred      0.50    0.45    0.40    0.30    0.10
  ---------------------------------------------------------
  0          0.1      0        0      0        0      1
  0          0.4      0        0      1        1      1
  1          0.5      1        1      1        1      1
  1          0.3      0        0      0        1      1
  1          0.45     0        1      1        1      1

  TruePos(TP)         1        2      2        3      3
  FalsePos(FP)        0        0      1        1      2
  TruePosRate(TPR)    1/3      2/3    2/3      3/3    3/3
  FalsePosRate(FPR)   0/2      0/2    1/2      1/2    2/2


  The ROC curve is a plot of FPR on the x-axis and TPR on the y-axis. Basically,
  one can pick any operating point along this curve to run, the operating point
  determined by which threshold you want to use. By changing the threshold, you
  tradeoff TP's for FPs.

  The more area under this curve, the better the classification algorithm is.
  The AreaUnderCurve() function can be used to compute the area under this
  curve.

  """

  yTrue = np.array([0, 0, 1, 1, 1])
  yScore = np.array([0.1, 0.4, 0.5, 0.3, 0.45])
  (fpr, tpr, thresholds) = ROCCurve(yTrue, yScore)

  print "Actual:    ",
  _printNPArray(yTrue)

  print "Predicted: ",
  _printNPArray(yScore)
  print

  print "Thresholds:",
  _printNPArray(thresholds[::-1])

  print "FPR(x):    ",
  _printNPArray(fpr)

  print "TPR(y):    ",
  _printNPArray(tpr)


  print
  area = AreaUnderCurve(fpr, tpr)
  print "AUC: ", area



if __name__=='__main__':
  _test()
