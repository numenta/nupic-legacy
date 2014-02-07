# Test for get/setParameter in python -- these methods are syntactic sugar that allow
# you to access parameters without knowing their types, at a moderate performance
# penalty.


from nupic.engine import Network
# import for type comparison with Array. Seems we should be able to use nupic.engine.Array directly.
import nupic.bindings.engine_internal

scalars = [
  ("int32Param", 32, int, 35),
  ("uint32Param", 33, int, 36),
  ("int64Param", 64, int, 74),
  ("uint64Param", 65, int, 75),
  ("real32Param", 32.1, float, 33.1),
  ("real64Param", 64.1, float, 65.1),
  ("stringParam", "nodespec value", str, "new value")]





n = Network()
l1= n.addRegion("l1", "TestNode", "")
x = l1.getParameter("uint32Param")

for paramName, initval, paramtype, newval in scalars:
  # Check the initial value for each parameter.
  print "Parameter = %s" % paramName
  x = l1.getParameter(paramName)
  assert type(x) == paramtype
  if initval is None:
    continue
  if type(x) == float:
    assert abs(x  - initval) < 0.00001
  else:
    assert x == initval

  # Now set the value, and check to make sure the value is updated
  l1.setParameter(paramName, newval)
  x = l1.getParameter(paramName)
  assert type(x) == paramtype
  if type(x) == float:
    assert abs(x  - newval) < 0.00001
  else:
    assert x == newval

  print "Param ok"


arrays = [
  ("real32ArrayParam", [0*32, 1*32, 2*32, 3*32, 4*32, 5*32, 6*32, 7*32], "Real32"),
  ("int64ArrayParam", [0*64, 1*64, 2*64, 3*64], "Int64")
]



for paramName, initval, paramtype in arrays:
  print "Parameter = %s" % paramName
  x = l1.getParameter(paramName)
  assert isinstance(x, nupic.bindings.engine_internal.Array)
  assert x.getType() == paramtype
  assert len(x) == len(initval)
  for i in xrange(len(x)):
    assert x[i] == initval[i]

  for i in xrange(len(x)):
    x[i] = x[i] * 2
  l1.setParameter(paramName, x)

  x = l1.getParameter(paramName)
  assert isinstance(x, nupic.bindings.engine_internal.Array)
  assert x.getType() == paramtype
  assert len(x) == len(initval)
  for i in xrange(len(x)):
    assert x[i] == 2 * initval[i]



  print "Param ok"


print "All tests passed"