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

from random import *
import numpy
import cPickle
import pylab
import nupic.bindings.algorithms as algo
from nupic.bindings.math import GetNumpyDataType

type = GetNumpyDataType('NTA_Real')
type = 'float32'



def simple():
    
    print "Simple"
    numpy.random.seed(42)
    n_dims = 2
    n_class = 4
    size = 200
    labels = numpy.random.random_integers(0, n_class-1, size)
    samples = numpy.zeros((size, n_dims), dtype=type)
    do_plot = False

    print "Generating data"
    centers = numpy.array([[0,0],[0,1],[1,0],[1,1]])
    for i in range(0, size):
        t = 6.28 * numpy.random.random_sample()
        samples[i][0] = 2 * centers[labels[i]][0] + .5*numpy.random.random() * numpy.cos(t)
        samples[i][1] = 2 * centers[labels[i]][1] + .5*numpy.random.random() * numpy.sin(t)

    classifier = algo.svm_dense(0, n_dims, probability=True, seed=42)
    
    print "Adding sample vectors"
    for y, x_list in zip(labels, samples):
        x = numpy.array(x_list, dtype=type)
        classifier.add_sample(float(y), x)

    print "Displaying problem"
    problem = classifier.get_problem()
    print "Problem size:", problem.size()
    print "Problem dimensionality:", problem.n_dims()
    print "Problem samples:"
    s = numpy.zeros((problem.size(), problem.n_dims()+1), dtype=type)
    problem.get_samples(s)
    print s

    if do_plot:
        pylab.ion()
        pylab.plot(s[s[:,0]==0,1], s[s[:,0]==0,2], '.', color='r')
        pylab.plot(s[s[:,0]==1,1], s[s[:,0]==1,2], '+', color='b')
        pylab.plot(s[s[:,0]==2,1], s[s[:,0]==2,2], '^', color='g')
        pylab.plot(s[s[:,0]==3,1], s[s[:,0]==3,2], 'v', color='g')

    print "Training"
    classifier.train(gamma = 1./3., C = 100, eps=1e-1)

    print "Displaying model"
    model = classifier.get_model()
    print "Number of support vectors:", model.size()
    print "Number of classes:", model.n_class()
    print "Number of dimensions: ", model.n_dims()
    print "Support vectors:"
    sv = numpy.zeros((model.size(), model.n_dims()), dtype=type)
    model.get_support_vectors(sv)
    print sv
    
    if do_plot:
        pylab.plot(sv[:,0], sv[:,1], 'o', color='g')

    print "Support vector coefficients:"
    svc = numpy.zeros((model.n_class()-1, model.size()), dtype=type)
    model.get_support_vector_coefficients(svc)
    print svc

    print "Hyperplanes (for linear kernel only):"
    h = model.get_hyperplanes()
    print h

    if do_plot:
        xmin = numpy.min(samples[:,0])
        xmax = numpy.max(samples[:,0])
        xstep = (xmax - xmin) / 10
        X = numpy.arange(xmin, xmax, xstep)

        ymin = numpy.min(samples[:,1])
        ymax = numpy.max(samples[:,1])
        ystep = (ymax - ymin) / 10
        Y = numpy.arange(ymin, ymax, ystep)

        points = numpy.zeros((len(X), len(Y)))

        for i,x in enumerate(X):
            for j,y in enumerate(Y):
                proba = numpy.zeros(model.n_class(), dtype=type)
                classifier.predict_probability(numpy.array([x,y]), proba)
                points[i,j] = proba[0]
        pylab.contour(X,Y,points)

    print "Cross-validation"
    print classifier.cross_validate(2, gamma = .5, C = 10, eps = 1e-3)

    print "Predicting"
    for y, x_list in zip(labels, samples):
        x = numpy.array(x_list, dtype=type)
        proba = numpy.zeros(model.n_class(), dtype=type)
        print x, ': real=', y,
        print 'p1=', classifier.predict(x),
        print 'p2=', classifier.predict_probability(x, proba),
        print 'proba=', proba

    print "Discarding problem"
    classifier.discard_problem()

    print "Predicting after discarding the problem"
    for y, x_list in zip(labels, samples):
        x = numpy.array(x_list, dtype=type)
        proba = numpy.zeros(model.n_class(), dtype=type)
        print x, ': real=', y,
        print 'p1=', classifier.predict(x),
        print 'p2=', classifier.predict_probability(x, proba),
        print 'proba=', proba



def persistence():
    
    print "Persistence"
    numpy.random.seed(42)
    n_dims = 2
    n_class = 12
    size = 100
    labels = numpy.random.random_integers(0, 256, size)
    samples = numpy.zeros((size, n_dims), dtype=type)

    print "Generating data"
    for i in range(0, size):
        t = 6.28 * numpy.random.random_sample()
        samples[i][0] = 2 * labels[i] + 1.5 * numpy.cos(t)
        samples[i][1] = 2 * labels[i] + 1.5 * numpy.sin(t)

    print "Creating dense classifier"
    classifier = algo.svm_dense(0, n_dims = n_dims, seed=42)
    
    print "Adding sample vectors to dense classifier"
    for y, x_list in zip(labels, samples):
        x = numpy.array(x_list, dtype=type)
        classifier.add_sample(float(y), x)

    print "Pickling dense classifier"
    cPickle.dump(classifier, open('test', 'wb'))
    classifier = cPickle.load(open('test', 'rb'))

    print "Training dense classifier"
    classifier.train(gamma = 1, C = 10, eps=1e-1)

    print "Predicting with dense classifier"
    print classifier.predict(samples[0])

    print "Creating 0/1 classifier"
    classifier01 = algo.svm_01(n_dims = n_dims, seed=42)

    print "Adding sample vectors to 0/1 classifier"
    for y, x_list in zip(labels, samples):
        x = numpy.array(x_list, dtype=type)
        classifier01.add_sample(float(y), x)

    print "Training 0/1 classifier"
    classifier01.train(gamma = 1./3., C = 100, eps=1e-1)

    print "Pickling 0/1 classifier"
    cPickle.dump(classifier01, open('test', 'wb'))
    classifier01 = cPickle.load(open('test', 'rb'))

    print "Predicting with 0/1 classifier"
    print classifier01.predict(numpy.array(samples[0], dtype=type))



def cross_validation():
    return
    print "Cross validation"
    numpy.random.seed(42)
    labels = [0, 1, 1, 2, 1, 2]
    samples = [[0, 0, 0], [0, 1, 0], [1, 0, 1], [1, 1, 1], [1, 1, 0], [0, 1, 1]]
    classifier = algo.svm_dense(0, n_dims = 3, seed=42)
    
    print "Adding sample vectors"
    for y, x_list in zip(labels, samples):
        x = numpy.array(x_list, dtype=type)
        classifier.add_sample(float(y), x)

    cPickle.dump(classifier, open('test', 'wb'))
    classifier = cPickle.load(open('test', 'rb'))

    print "Training"
    classifier.train(gamma = 1./3., C = 100, eps=1e-1)

    print "Cross validation =", 
    print classifier.cross_validate(3, gamma = .5, C = 10, eps = 1e-3)

#--------------------------------------------------------------------------------
simple()
persistence()
cross_validation()


