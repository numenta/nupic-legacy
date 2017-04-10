# Python Style Guide

This document is a _diff_ - it describes how Numenta's Python guidelines differ from or are unspecified by [PEP-8](http://www.python.org/dev/peps/pep-0008/) and [PEP-257](http://www.python.org/dev/peps/pep-0257/).

It's meant to be succinct.  Generally, we wish to remain close to the best practices of the Python community.

## Python Version

Numenta software requires Python 2.7.

## Pylint

The NuPIC installation should put `pylint` on your path and you should create a symbolic link at `~/.pylintrc` that points to `$NUPIC/py/pylintrc`.  The pylint command enforces many of the style guidelines from this document and PEP8.

## File Layout

### Executables

Executables should be specified in the `setup.py` as described [here](http://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation).

### Legal Notice

At the top of each source file (after the shebang, if any), include the following legal notice:

```python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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
```

In the date, include any years in which the code was modified as either one year or a range, e.g. "2006-2009", "2010".

### Module Docstring

After the legal notice, include a docstring to describe the contents of the file.  If the file comprises a single class definition, then make it minimalist -- put your more-detailed documentation in the _class's_ docstring.

### Tests

Do not include tests in source files. All tests are in the [`/tests`](https://github.com/numenta/nupic/tree/master/tests) directory.

## Coding Style

### Indentation

Use two (2) spaces per indentation level.

### Blank Lines

Separate top level functions and classes by **three** blank lines. Separate methods inside classes by **two** blank lines. Do not use more than one consecutive blank line in a code block. Files should end with a single newline character (most editors will show this as a blank line but some, such as Vim, will not display it).

### Imports

#### try/except

For Numenta-internal code, do not wrap import statements in try-except blocks and attempt to recover dynamically.  (If there's an exception, consider that a configuration bug.)

No:

```python
try:
  import thirdpartymodule
except ImportError:
  # Attempt brave recovery
```

Yes:

```python
import thirdpartymodule
```

For code meant to be used externally, brave recoveries are acceptable.

#### from statements

Multiple imports are okay in a from statement.

Yes:

```python
from subprocess import Popen, PIPE
```

If there are many, enclose them in parentheses to allow multiple lines.

Yes:

```python
from my_fancy_module import (myFunc1,
                             myFunc2,
                             myVeryLongFunc3)
```

#### Wildcard imports

Do not use `import *`.  It pollutes the global namespace and makes it difficult to determine where symbols are defined.

No:

```python
from subprocess import *
```

#### Import Grouping

Imports should be grouped in the following order:

1. Standard library imports, e.g., libraries that come with Python such as `collections`
2. Related third party imports, i.e., anything non-nupic that we would have to add to `external/common/requirements.txt`
3. NuPIC imports (only if in a non-nupic repository)
4. Local imports (other packages from current repository)

Within each group the imports should be ordered alphabetically. There should be a blank line between each group of imports.

### Quotes

By default, double quotes should be used for all strings.

### Spaces

Do not leave trailing whitespace on non-blank lines.

For loosely-binding arithmetic operators (+, -), use surrounding spaces.

For tightly-binding ones (*, /, and **), you may omit the spaces.

No:

```python
i=i+1
submitted +=1
c = (a+b) * (a-b)
```

Yes:

```python
i = i + 1
submitted += 1
x = x*2 - 1
hypot2 = x*x + y*y
c = (a + b) * (a - b)
```

### Compound Statements

Do not use compound statements.

No:

```python
if foo: print foo
```

Yes:

```python
if foo:
  print foo
```

No:

```python
x = foo; print x
```

Yes:

```python
x = foo
print x
```

## Docstrings

Numenta's guidelines for _where_ to use docstrings are the same as in PEP-257.

Numenta's guidelines for _content and format_ of docstrings is defined in
[`docs`](https://github.com/numenta/nupic/tree/master/docs).

## Comments

### Purpose of Comments

Comments are for describing **why**, not what.  Favor **structure** over commentary.

If your comment says "the next n lines do y," then remove it and make those next n lines a new (unit-testable) function.

No:

```python
#-------------------------------
# first, flurblize the glambuz
... code ...

#-------------------------------
# then, deblurflize the buzglam
... even more code ...
```

Yes:

```python
def flurblize(glambuz):
   ... code ...

def deblurflize(buzglam):
   ... code ...

flurblize(glambuz)
deblurflize(buzglam)
```

### Commented Sections

Separate commented sections with a blank line.

No:

```python
# This comment applies to the next two lines.
foo()
bar()
# This is another comment.
baz()
```

Yes:

```python
# This comment applies to the next two lines.
foo()
bar()

# This is another comment.
baz()
```

### Inline Comments

Do not use a comments on the same line as a statement/expession.  It's hard to read.

No:

```python
x = x + 1  # Compensate for border
```

Yes:

```python
# Compensate for border.
x = x + 1
```

### Comments in if/else blocks

Put comments which describe the predicate _inside_ the block itself.

No:

```python
# User selected "Other"
if radioIndex == len(self.intervals):
  self.intervalOther.SetFocus()
# User selected one of the pre-defined intervals
else:
  self.interval = int(self.intervals[radioIndex])
```

Yes:

```python
if radioIndex == len(self.intervals):
  # User selected "Other"
  self.intervalOther.SetFocus()
else:
  # User selected one of the pre-defined intervals
  self.interval = int(self.intervals[radioIndex])
```

In contrast, put comments which describe the context for the entire if/else section before the if.

## Naming Conventions

### Directory and File Names

Make directories (packages) and files (modules) snake_cased -- i.e. lowercase letters with an underscore for separating words.  ASCII only.  Shorter is better.

No:

```python
# directory layout
production/
  ProductionWorker.py
  productionJobParamsSchema.json
# code
from nupic.cluster.production.ProductionWorker import ProductionWorker
```

Yes:

```python
# directory layout
production/
  production_worker.py
  production_job_params_schema.json
# code
from nupic.cluster.production.production_worker import ProductionWorker
```

Include the suffix ".py" on all Python modules.  Exception: ".pyw" for modules to be launched from a graphical shell.

### Function, Method, and Instance Variable Names

Give functions, methods, and instance variables names in camelCase.

For non-public attributes, add a leading underscore.  Whether just one (`_`) or two (`__`) is an interesting question.

Using just one (`_`) has two benefits:

* it's the most wide-spread convention
* unit tests can easily access those methods

On the other hand, using two (`__`) is useful for inheritance.  Names with this prefix (but _without_ that suffix) evoke name mangling, making them appropriately difficult to access from outside the class.  So attributes meant to be truly private (and not merely protected) will be immune to accidental overwriting by subclasses.

**You should not access mangled attribute names outside the class.**

### Module-global Variables

Give module-level "constants" SHOUT_CASE names.  If non-public, include a leading underscore.

Give module-level (actual) variables the prefix "g_", to indicate "global".  (These should never be public, so there's no need to include a leading underscore to distinguish public from non-public.)

### Dummy Names

"Dummy" variables are ones required but unused.  For example, you may need to supply a callback not all of whose arguments you need.  Or you call a function that returns multiple values, but you don't use them all.

Give dummy variables a leading underscore.

Yes:

```python
(hostname, _port) = getHostnameAndPort()
# _port is unused
print hostname
```

Or, use just an underscore.

Yes:

```python
(hostname, _) = getHostnameAndPort()
# _ is unused
print hostname
```

## Interfacing with third party code

Sometimes we use code with naming conventions that differ from Numenta's.  For example, wxPython requires one to use its naming conventions (to subclass its classes and provide event handlers).

In this case, hide these convention conflicts in a helper class.  The helper should encapsulate the use of the third-party code, do the heavy lifting, and expose only Numenta-style names.

## Programming Guidelines

### Testable Code

Make your units small.  Design for testability.

### Stay DRY

DRY stands for "don't repeat yourself".  Do not copy-and-paste.

Rather than copy-and-paste, make a new, parametrized function.

### Classes

Use only new-style classes -- those which subclass object, directly or indirectly.

No:

```python
class Foo:
  ...
```

Yes:

```python
class Foo(object):
  ...
```

### Data Member Initialization

Initialize all members in `__init__`, even if simply to None.  This serves to declare what all instance variables are in use.  Do not create attributes outside of `__init__`.

No:

```python
def __init__(self):
  pass


def bar(self, foo):
  self._foo = foo
```

Yes:

```python
def __init__(self):
  self._foo = None


def bar(self, foo):
  self._foo = foo
```

### Properties

Do not use properties unless necessary.  If you must:

* Declare them immediately after `__init__`.
* Document why, right before the definition.

Yes:

```python
# coincidenceCount is a property because it's:
#   - computed and
#   - read-only
@property
coincidenceCount(_getCoincidenceCount, None,
                 None, "Number of coincidences")


def _getCoincidenceCount(self):
  return len(self.coincidences)
```

### List Comprehensions

Use list comprehensions instead of map, filter, and reduce.  In Python, list comprehensions are highly optimized.  HOFs are deprecated.

### String Formatting

Use the `str.format` method.

Good:

```python
"Category = {cat}".format(cat=categoryOut)
```

Bad:

```python
"Category = %s" % categoryOut
```

### Enums

Use the `enum.Enum` class provided by the [enum34](https://pypi.python.org/pypi/enum34) package.
