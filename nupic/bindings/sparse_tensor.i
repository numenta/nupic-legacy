/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */


// This set of includes will be reproduced verbatim in the generated 
// C++ bindings code. That code is exposed to the target language 
// (i.e. Python) through a tiny C interface (equivalent to a single 
// entry point with C linkage, class init_math for the math module,
// which fills up an array of function pointers.
// The process of specifying bindings, below, does not inherently add any 
// include statements to the generated C++, so necessary includes must be 
// added here.
// The typical structure for an "easy-to-bind" class is as follows:
// 1) Add an include line inside the %{ %} block. For example:
//    %{
//    ... other includes ...
//    #include <nupic/tools/NetworkElement.hpp>
//    ... other includes ...
//    %}
// 2) Add a binding-generating include line outside any block. 
//    Binding-generating includes start with %. For example:
//    %include <nupic/tools/NetworkElement.hpp>
// That is it! If this fails to generate the desired bindings, consult
// the extensive SWIG documentation on customizing and extending the 
// existing bindings, available at:
// http://www.swig.org/doc.html
// http://www.swig.org/tutorial.html
//

%{
#include <py_support/NumpyVector.hpp>
#include <nupic/math/Index.hpp>
#include <nupic/math/Domain.hpp>
#include <nupic/math/SparseTensor.hpp>
#include <nupic/bindings/PySparseTensor.hpp>
%}

%ignore operator<<;
%ignore operator==;
%ignore operator!=;

%ignore PyTensorIndex::operator[];
%ignore PyTensorIndex::operator=;
%ignore PyTensorIndex::operator==;
%ignore PyTensorIndex::operator!=;

%ignore nupic::Domain::operator[];
%ignore nupic::Domain::operator=;
%ignore nupic::Domain::operator<<;
%ignore nupic::Domain::operator==;
%ignore nupic::Domain::operator!=;
%ignore nupic::DimRange::operator=;

%include <nupic/math/Domain.hpp>
 //%template(BaseDomain) nupic::Domain<nupic::UInt32>;

%include <nupic/bindings/PySparseTensor.hpp>

%extend PyTensorIndex {
%pythoncode %{
  def __setstate__(self, tup):
    self.this = _MATH.new_PyTensorIndex(tup)
    self.thisown = 1
%}
}

%extend PySparseTensor {
%pythoncode %{
    def _fixSlice(self, dim, ub):
        """Used internally to fill out blank fields in slicing records."""
        assert (dim.step == 1) or (dim.step is None)
        start = dim.start
        if start is None: start = 0
        elif start < 0: start += ub
        stop = dim.stop
        if stop is None: stop = ub
        elif stop < 0: stop += ub
        return slice(start, stop, 1)

    def _getDomain(self, key, bounds):
        """Used internally to convert a list of slices to a valid Domain."""
        slices = [None] * len(bounds)
        cur = 0
        hasEllipsis = False
        for dim in key:
            if dim is Ellipsis:
                assert not hasEllipsis
                hasEllipsis = True
                toFill = len(bounds) - len(key) + 1
                if toFill > 0:
                    for j in xrange(toFill-1):
                        slices[cur] = slice(0, bounds[cur], 1)
                        cur += 1
                    slices[cur] = slice(0, bounds[cur], 1)
            elif isinstance(dim, slice): 
                slices[cur] = self._fixSlice(dim, bounds[cur])
            else: slices[cur] = slice(dim, dim, 0)
            cur += 1
        return Domain([x.start for x in slices], [x.stop for x in slices])

    def getSliceWrap(self, key):
        return self.getSlice(self._getDomain(key, self.getBounds()))
          
    def setSliceWrap(self, key, value):
        self.setSlice(self._getDomain(key, self.getBounds()), value)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            hasSlices = False
            for dim in key:
                if (dim is Ellipsis) or isinstance(dim, slice):
                    hasSlices = True
                    break
            if hasSlices: return self.getSliceWrap(key)
            else: return _MATH.PySparseTensor_get(self, key)
        elif (key is Ellipsis) or isinstance(key, slice):
            return self.getSliceWrap((key,))
        else:
            return _MATH.PySparseTensor_get(self, (key,))
    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            hasSlices = False
            for dim in key:
                if isinstance(dim, slice): hasSlices = True
            if hasSlices: return self.setSliceWrap(key, value)
            else: return _MATH.PySparseTensor_set(self, key, value)
        elif (key is Ellipsis) or isinstance(key, slice):
            return self.setSliceWrap((key,), value)
        else:
            return _MATH.PySparseTensor_set(self, (key,), value)
    def __setstate__(self, s):
        self.this = _MATH.new_PySparseTensor(s)
        self.thisown = 1
%}
}

// Alias around the awkward name change.
%pythoncode %{
SparseTensor = PySparseTensor
TensorIndex = PyTensorIndex
Domain = PyDomain
%}




