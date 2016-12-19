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

import sys
import csv
import numpy as np



def writeSimpleTest1(filePath, numRecords, testNumber):
  """ Generates requested number of records and saves in a csv file
  """
  with open(filePath+'.csv', 'wb') as f:
    writer = csv.writer(f)

    if testNumber == 1:
      writer.writerow(['field1', 'field2'])
      writer.writerow(['int', 'int'])
      writer.writerow(['', ''])
      for i in ranger(0, numRecords):  
        field1 = int(np.random.random_integers(0, 100, 1))
        field2 = field1 + int(0.025*np.random.normal(0, 100, 1))
        writer.writerow([field1, field2])
        
    elif testNumber == 2:
      writer.writerow(['field1', 'field2', 'field3'])
      writer.writerow(['int', 'int', 'int'])
      writer.writerow(['', '', ''])
      for i in range(0, numRecords):
        field1 = int(np.random.random_integers(0, 100, 1))
        field2 = field1 + int(0.025*np.random.normal(0, 100, 1))
        field3 = int(np.random.random_integers(0, 100, 1))
        writer.writerow([field1, field2, field3])
      pass
    
    elif testNumber == 3:
      writer.writerow(['field1', 'field2', 'field3', 'field4'])
      writer.writerow(['int', 'int', 'int', 'int'])
      writer.writerow(['', '', '', ''])
      for i in range(0, numRecords):
        field2 = int(np.random.random_integers(0, 100, 1))
        field3 = int(np.random.random_integers(0, 100, 1))
        field1 = field2 + field3
        field4 = int(np.random.random_integers(0, 100, 1))
        writer.writerow([field1, field2, field3, field4])

    elif testNumber == 4 or testNumber == 5:
      writer.writerow(['field1', 'field2'])
      writer.writerow(['string', 'string'])
      writer.writerow(['', ''])

      if testNumber == 5:
        categories = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 
                      'k', 'l', 'm', 'n', 'o', 'p']
      else:
        categories = ['a', 'b', 'c', 'd'] 
      numRecsSaved = 0 
      firstFieldInd = 0
      done = False
      while not done:
        while not done:
          field1 = categories[firstFieldInd]
          for category in categories:
            field2 = category
            writer.writerow([field1, field2])
            numRecsSaved += 1
            if numRecsSaved == numRecords:
              done = True
              break
          firstFieldInd += 1
          if firstFieldInd == len(categories):
            firstFieldInd = 0
    
    elif testNumber == 6:
      writer.writerow(['field1', 'field2'])
      writer.writerow(['string', 'string'])
      writer.writerow(['', ''])
      
      choises = [
                 ['a', [0.9, 0.05, 0.05]],
                 ['b', [0.05, 0.9, 0.05]],
                 ['c', [0.05, 0.05, 0.9]]
                ]
      cat2 = ['d', 'e', 'f']
      for i in range(0, numRecords):
        ind1 = int(np.random.random_integers(0, 2, 1))
        field1 = choises[ind1][0]
        ind2 = np.searchsorted(np.cumsum(choises[ind1][1]), np.random.random())
        field2 = cat2[ind2]
        writer.writerow([field1, field2])
      pass
    
    elif testNumber == 7:
      writer.writerow(['field1', 'field2', 'field3'])
      writer.writerow(['string', 'string', 'string'])
      writer.writerow(['', '', ''])      

      choises = [
                 ['a', [0.9, 0.05, 0.05]],
                 ['b', [0.05, 0.9, 0.05]],
                 ['c', [0.05, 0.05, 0.9]]
                ]
      cat2 = ['d', 'e', 'f']
      cat3 = ['g', 'h', 'i']
      for i in range(0, numRecords):
        ind1 = int(np.random.random_integers(0, 2, 1))
        field1 = choises[ind1][0]
        ind2 = np.searchsorted(np.cumsum(choises[ind1][1]), np.random.random())
        field2 = cat2[ind2]
        ind3 = int(np.random.random_integers(0, 2, 1))
        field3 = cat3[ind3]
        writer.writerow([field1, field2, field3])
      pass

    elif testNumber == 8:
      writer.writerow(['field1', 'field2', 'field3'])
      writer.writerow(['string', 'string', 'string'])
      writer.writerow(['', '', ''])      

      choises = [
                 ['a', 'd', [0.9, 0.05, 0.05]],
                 ['a', 'e', [0.05, 0.9, 0.05]],
                 ['a', 'f', [0.05, 0.05, 0.9]],
                 ['b', 'd', [0.9, 0.05, 0.05]],
                 ['b', 'e', [0.05, 0.9, 0.05]],
                 ['b', 'f', [0.05, 0.05, 0.9]],
                 ['c', 'd', [0.9, 0.05, 0.05]],
                 ['c', 'e', [0.05, 0.9, 0.05]],
                 ['c', 'f', [0.05, 0.05, 0.9]]
                ]
      cat3 = ['g', 'h', 'i']
      for i in range(0, numRecords):
        ind1 = int(np.random.random_integers(0, 8, 1))
        field1 = choises[ind1][0]
        field2 = choises[ind1][1]
        ind2 = np.searchsorted(np.cumsum(choises[ind1][2]), np.random.random())
        field3 = cat3[ind2]
        writer.writerow([field1, field2, field3])
      pass
    
  return



if __name__ == '__main__':
  
  np.random.seed(83)
  
  # Test 1
  # 2 fields. field2 = field1 + noise (5%). Values are 0-100 (plus noise)
  
  # Test 2
  # 3 fields, field 1 and 2 are the same as in #1, but 3rd field is random. 
  # Values are 0-100.
  
  # Test 3
  # 4 fields, field1 = field2 + field3 (no noise), field4 is random. 
  # Values are 0-100.
  
  # Test 4 
  # 2 fields, categories. Each category can have 4 values (a, b, c, d). 
  # Data in the following structure 
  # (a,a)->(a,b)->(a, c)->(a,d)->(b,a)->(b,b) and so on
  
  # Test 5 
  # 2 fields, categories. The data is the same as in #4, 
  # but each category can have 16 values (a,b, ...p)

  # Test 6
  # 2 fields, categories. First field is one of (a, b, c). 
  # Second field is (a->d, b->e, c->f) with probabilities (0.9 and 0.05, 0.05)
  
  # Test 7
  # 3 fields. 2 fields are the same as in #6, 3rd field is random (g, h, i)
  
  # Test 8
  # 3 fields. 1st field is (a, b, c), 2nd is (d, e, f). 3rd field is
  # (a,d -> g), (a, e -> h), (a, f -> i) and so on, with probabilities
  # (0.9, 0.05, 0.05)
  
  print 'Generating %s with %s records, test #%s' % \
        (sys.argv[1], sys.argv[2], sys.argv[3])
        
  writeSimpleTest1(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
