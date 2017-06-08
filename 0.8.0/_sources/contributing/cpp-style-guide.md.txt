# C++ Style Guide

NuPIC programmers are expected to follow sound programming techniques. This document outlines specific software coding standards and guidelines to be used by developers. We focus on those aspects of code guidelines that are specific to NuPIC, not on all possible techniques (see references for books on general programming methodologies).

The primary reasons for the guidelines are reliability, readability, and efficiency. Reliability is a major problem in large-scale systems and software developed in teams. Decisions made early in the software design can affect you in surprising ways late in the development or test cycle. We need to minimize these surprises. In general this document emphasizes the following themes: use "defensive programming" techniques, keep your code simple and clean, avoid external dependencies where possible, and avoid redundancy.

This document is primarily for C++ code. See the [Python Style Guide](python-style-guide.html) for Python code.

## Consistency Within A File

Maintain consistency within a file. Where details are not specified here, developers have the freedom to use their own convention. In such cases modifications of a file by other developers should maintain the conventions and overall consistency within that file.

## References

1. Sutter and Alexandrescu, C++ Coding Standards
2. Scott Meyers, Effective C++
3. Scott Meyers, More Effective C++

## C++ Source Files

This section contains general guidelines applicable to all source files, including header and implementation files.

### Introductory Section And Copyright Notices

All source files, including header files, should start with the following introductory legal notice.

```cpp
/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU Affero Public License for more details.
 *
 * You should have received a copy of the GNU Affero Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ----------------------------------------------------------------------
 */
```

If the source code spans multiple years, the copyright notice should reflect this. For example:

```
Copyright (C) 2006-2007, Numenta, Inc.
```

### Filenames

Filenames should not contain characters that could cause problems on different platforms or in certain scripting situations. Filenames should contain only English alphanumeric characters, underscore, and period. No spaces or funny characters are allowed. Some operating systems (such as Windows) are not case sensitive so filenames that differ only in case are not allowed. This applies across the entire codebase.

C++ header files should have the suffix ".hpp". C header files should have the suffix ".h".

C/C++ (`.h`, `.c`, `.hpp` and `.cpp`) and related SWIG (`.i`) file names should be **UpperCamelCase**. Initials and two-letter acronyms should be capitalized (e.g. **RegionIO.cpp**, **OSUnix.cpp**), longer acronyms treated as words (e.g. **SdrClassifier.cpp**). A few non-code files (e.g. **README.md**, **cmake_install.cmake**) are uppercase or snake_case by standard convention.

### Naming Conventions

All identifier names should be descriptive and readable. All NuPIC class, type, constant, etc. definitions should be placed in the global namespace "nta" to avoid name collisions. Modules within Numenta can define namespaces within `nta`, such as `nta::math`. As much as possible, use verbs to start method names (e.g. getAttribute()).

We will use "CamelBack" capitalization for naming identifiers. This consists of a sequence of words where the first letter of each successive word is capitalized. No underscores are used to separate words. Generally identifiers that are global within a namespace capitalize the first letter, other identifiers start with a lower case letter. More specifically:

* Global class names will be named as in `ExampleClass`
* Methods will be 'setAttribute()'
* Class data members will be `exampleDataMember_` (with trailing underscore)
* Local variables within methods and functions will be "exampleLocalVariable" (no trailing underscore)
* `ExampleType` used for global typedefs, `exampleType` for typedefs within a class. (Exceptions are allowed where STL requires a specific name.)
* `ExampleType` used for global enum names, and `ValueExample` used for global enum values.
* `exampleType` used for enum names defined within a class and `valueExample` used for enum values within a class.

### Indentation

The indentation level should be 2 spaces. Editor settings should be set such that tabs are converted to spaces. Tab characters should not be used.

### The Header File

All header files should be bracketed by #define's to prevent multiple inclusion. For example, ExampleClass.hpp should be bracketed by NTA_EXAMPLE_CLASS_HPP, as in:

```c++
#ifndef NTA_EXAMPLE_CLASS_HPP
#define NTA_EXAMPLE_CLASS_HPP

#include <AHeader.hpp>
#include <AnotherHeader.hpp>

namespace nta
{

// Main content of ExampleClass.hpp header file

} // end namespace nta

#endif // NTA_EXAMPLE_CLASS_HPP
```

All header file inclusions should be inside the surrounding #define. This prevents infinite pre-processor loops (such as if AHeader.hpp were to include ExampleClass.hpp). In general only include what is strictly necessary to use this header file. Do not include common library header files such as stdio.h (or generally any header file), unless that functionality is required to compile that individual header file. Those header files are more appropriate for inclusion in the CPP file itself.

Use:

```c++
#include <algorithms/header.hpp>
```

rather than:

```c++
#include "header.hpp"
```

The former allows more flexibility in moving files around.

### Class Definitions

Class definitions should be preceded by precise comments explaining the following: purpose, responsibility, rationale, etc. of the class. This is also the place to put any "TODO" for work remaining to be done. The descriptions should be concise and meaningful. This is not the place to put random thoughts or philosophies about data structures, experiments, etc. That stuff can go on the forum or design documents.

### Method Definitions

Method names should be descriptive. Definitions should contain a precise description of the method plus descriptions of the parameters and error checking.

### Example Header File

```c++
/*
 * ----------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
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
 * ----------------------------------------------------------------
 */

/** @file
 * Description of class ClassName.
 */

#ifndef NTA_CLASS_NAME_HPP
#define NTA_CLASS_NAME_HPP

#include <iostream>
/* <-- Put other Numenta includes here, after standard includes */

namespace nta
{

  /** One line class description for Doxygen.
   *
   * @b Description
   * A detailed description follows the one line description.
   * Detailed description should include responsibility (what
   * does this class do?).
   *
   * @b Rationale
   * Why did we choose to have that class the way it is?)
   *
   * @b Resource @b Ownership
   * Resource ownerships (acquired/transfered...)
   *
   * @note
   * A useful note for users of this class
   *
   */
  class ClassName
  {
  public:
    /* Remove virtual if no other virtual members */
    virtual ~ClassName() {}

    /**
     * Brief description of method for Doxygen.
     *
     * More detailed description includes explanation of error checking.
     */
    virtual void anExampleMethod();

    /**
     * Brief description of method for Doxygen.
     *
     * More detailed description includes explanation of parameters
     * and error checking.
     *
     * @param foo Description of parameter foo including valid
     * range and (any) error checking.
     *
     * @retval Description of return value of this method.
     */
    virtual int anotherMethod(int foo);

  protected:

  private:
    /** An example private data member. */
    int anExampleDataMember_;

    /**
     * Default ctor, copy ctor and assignment operator
     * forbidden by default
     */
    ClassName();
    ClassName(const ClassName &);
    ClassName& operator=(const ClassName&);

  }; // end class ClassName

} // end namespace nta

#endif // NTA_CLASS_NAME_HPP
```

## The CPP file

In a .cpp file, all include statements should be placed right after the introductory comments. It is a bad idea to put includes in the middle of source files. In general the order of include files should be: standard C++ header files first, followed by header files of third party libraries, followed by NuPIC header files.

### Variable Declarations

It is good practice (though not required) to declare variables just before they are used. It is mandatory to initialize all variables. For example:

```c++
int i = 0;
char *s = NULL;
float f = 0;
```

### Comments in CPP files

__WRITE ME__

## Error Handling

### Logging

In general, printing using printf's, cout, and cerr should never be used directly in the main code branch. Errors, warnings, and messages should be logged using a general logging class (which in turn can use cout when appropriate).

### Use of assert

`NTA_ASSERT()` should be used in place of `assert()`. `NTA_ASSERT()` should be carefully used in the main code branch. It should be remembered at all times that the assert will not be present in production code. In non-performance-critical code, potential errors should be explicitly checked without assert and handled appropriately. No expressions with side effects should ever be used within an assert statement. For example:

```c++
NTA_ASSERT(list->insert(node));
```

The use of assert's is strongly encouraged in error checking within performance critical code. It is also strongly encouraged to use `NTA_ASSERT` ability to log additional information, as in:

```c++
NTA_ASSERT(check_preconditions()) << "Incorrect preconditions in node:" << node_number;
```

### Exceptions and Error Codes

Except in performance-critical sections, exceptions rather than error codes should be used to return errors. All non-performance critical methods should check their input parameters (and other external dependencies where appropriate), log errors, and throw appropriate exceptions. Don't use exception specifications in the signature of a method.

In performance-critical sections, error codes can be returned, asserts may be used, or eror checking may be skipped altogether. In such cases, the specifics of error checking should be explicitly noted in the method comments.

### Avoid static_cast

Use dynamic_cast rather than static_cast unless the code is performance critical. dynamic_cast is safer and recommended.

## Memory and Resource Management

### Memory Allocation

Use the C++ "new" and "delete" rather than malloc or calloc. In all cases the memory block returned should be checked. If NULL, there is a catastrophic problem with the system and this should be logged. The memory blocks should be initialized immediately to reasonable values (except in performance-intensive situations). Never allocate memory in core inner loops.

### Resource Management

Resources such as memory, network connections and owned objects should be cleaned up properly. The ownership of these resources can be limited to a local scope or to whole lifetime of the object (member variables). The only way to guarantee proper cleanup in C++ is to do it in the destructor. Local resources should be placed in local variables (on the stack) such that their destructor will be called automatically.

This is the famous RAII idiom (Resource Acquisition Is Initialization). See here: [http://en.wikipedia.org/wiki/Resource_Acquisition_Is_Initialization](http://en.wikipedia.org/wiki/Resource_Acquisition_Is_Initialization)

Sometimes however you get a pointer to a dynamic object you must free before exiting the scope. Explicitly calling delete on a raw pointer is a dubious practice. If there are multiple return statements from a method/function you must remember to free the pointer before each one. If an exception is thrown you are out of luck.

The solution is to place the pointer in a smart pointer that is actually a local object that is guaranteed to be destructed. It will delete the raw pointer when the control flow leaves the scope. The C++ standard library contains the auto_ptr smart pointer that can be used for this purpose, but it might subject the developer to multiple gotchas. Instead you should use `boost::scoped_ptr` for this purpose. The gory details are here:

[http://www.boost.org/libs/smart_ptr/scoped_ptr.htm](http://www.boost.org/libs/smart_ptr/scoped_ptr.htm)

## General principles

Creator of a resource is by default the owner and is responsible for its cleanup. Ownership transfer should be minimized to keep the code simple. There should be no need to hunt down ownership transfers in general. Note that resource handles in different forms (pointers, references, indexes into containers, opaque handles, persistent ids, etc) should be passed around, but there should be a single owner that will typically destroy the resource when it is safe.

### Factories

Factories are either objects, functions or methods whose job is to encapsulate complicated validation and initialization logic and create resources. The factory method signature typically look like:

```c++
X * createX(params);
```

In this case even though the factory technically created the X resource it is not the owner. The caller to create X is the owner. The factory method is a well-known design patterns that further elaborate on that: [http://en.wikipedia.org/wiki/Factory_method_pattern](http://en.wikipedia.org/wiki/Factory_method_pattern)

Typically when the caller gets the X raw pointer it should either store it in a member variable for later destruction or assign it to a boost::scoped_ptr if it is supposed to be used in this scope only.

### Passing resources around

The owner should pass around resources as references or const references.This communicates the fact that the resource is owned by someone else and prevents accidental destruction of the resource by a non-owner. Note that the non-owner can still destroy the resource by explicitly taking its address and deleting it. There are ways to prevent that too, but the complication is not worth the risk. If you are interested check out: [http://www.ddj.com/article/printableArticle.jhtml?articleID=184401977 &dept_url=/dept/cpp/](http://www.ddj.com/article/printableArticle.jhtml?articleID=184401977 &dept_url=/dept/cpp/)

### `boost::shared_ptr`

In some situations ownership may not be so clear. Suppose 3 objects use the same resource and they may or may not be destroyed at each point. Once all 3 of them were destroyed you need to destroy the shared resource. This situation may still be handled by having a separate owner that outlives all 3 objects. However, you don't want to keep the resource around once all 3 objects were destroyed. In this case boost::shared_ptr could be the ticket.We didn't identify use cases that require it in Anthill. In case you think you need boost::shared_ptr bring it up for discussion.

## Unit Tests

With few exceptions, the use of unit tests is required for all classes. The unit tests should exercise all API functions and stress test the class. The unit test routines should be self-contained and designed to return programmatically the success or failure of each of the tests. In this way, it would be easy to chain together all the unit tests and automate the basic testing of all classes. The base class "Tester" is used to define subclasses for performing unit tests.  Tests should go into a "unittests" directory that is in the same location as the code being tested and should automatically be included in the "testeverything" binary.

See [CPP Unit Tests](https://discourse.numenta.org/t/c-unit-tests/2144) for a more up-to-date guide.

## Documentation

The use of triple slashes insures that the Doxygen tool will pick up the comment block for automatic documentation generation.

### Classes

Class declarations in the header file should be documented with a comment block similar to this:

```c++
/////////////////////////////////////////////////////////////////////////
/// Short, one line description of class.
///
/// @b Responsibility
/// Overall responsibility
///
/// @b Description
/// Detailed and clear description
///
/// @b Resource @b Ownership
///
/// @note
/// Optional short notes.
///
/// @todo
/// Optional list of todo items.
///
////////////////////////////////////////////////////////////////////////
class ExampleClass : public BaseClass
```

### Functions

Functions and methods should be documented with a comment block similar to this:

```c++
 /////////////////////////////////////////////////////////////////////////
 /// Short, one line description of function
 ///
 /// Detailed description of function goes here.
 /// This description can be multiple lines
 ///
 /// @param paramName description of this parameter
 /// @param anotherParam description of this parameter
 /// @retval description of return value, if any
 ///
 /// @todo optional list of todo items can go here&hellip;.
 ///
 //////////////////////////////////////////////////////////////////////////
```

In general, these Doxygen style function comment blocks should only be placed in the class header file, not the source file, in order to avoid confusion as to which one doxygen will use when generating the documentation.

## Miscellaneous

### Macros

In general, macros should be avoided. Macros should not hide program control flow. List any good reasons for macros.

### Use of text

Use of string vs wstring? __WRITE ME__

## Use Of External Libraries

External libraries should be used with extreme caution in the main code branch. Although these libraries may seem enticing, they are often written with a different purpose, are written to be too general purpose, or have not been tested thoroughly. Sometimes these issues are subtle and you do not notice them until late in the cycle. For example, a library's memory allocation scheme may not be appropriate for our situation. Or, the library may be too general purpose, and thus may contain much inefficiency.

## Cross Platform Coding

This section covers some issues and Numenta policies around cross-platform coding.

## Operating System Dependencies

Make sure your code is not heavily operating system or platform dependent. Think of the operating system as an external library, and to isolate our code from OS dependencies. Any header files, function calls or definitions that are specific to an operating system should be isolated and accessed through an OS interface layer. The interface layer definition itself should be operating system independent. Different implementations of the interface layer can then be included during the build process to handle different operating systems.

With very few exceptions, the main code branch should not directly use operating system specific functionality. The code should not include OS specific header files, use OS specific #define's, or call OS specific functions. The code should instead include our OS interface header file (which will contain Numenta versions of this functionality) and access our OS layer directly.

Exceptions There are some exceptions to this rule. As an example, for certain performance-critical inner loops, we may find that MMX optimizations speed things up on Intel platforms. In these cases it is desirable to have an Intel specific implementation, but we also want an alternate, platform independent implementation. The alternate version is needed for cross-platform compatibility, but also to check the platform-specific implementation!

Exact implementation of platform specific code will vary depending on the situation. For example, for an optimized inner loop, you would bracket the Intel-specific code by a #define:

```c++
#ifdef NTA_USING_INTEL
<Intel specific code>
#else
<generic code>
#endif
```

## Specific Cross Platform Usage

Functionality that is not part of the C++ standard library is not cross platform. In these cases a cross-platform library (external or internal) should be used to isolate Numenta's code from OS and platform dependencies. APR (Apache Runtime library) has an excellent collection of such libraries and should be used wherever possible.

Listed below are specific functions that are not cross-platform. For these functions use APR (preferably) or another approved library.

* File path specifications, file manipulation, directory manipulation and traversals - use APR. Boost is very hard to use and "deprecated".
* Threading - we shouldn't have multi-threading in most parts of our system. If we do need it, we should use APR's thread library.
* Time/Date - APR
* Getting/setting environment variables - APR
* Program options - APR. Boost is ok but deprecated.
* Sockets and networking routines - APR
* Shared memory - APR
* Timing - use our internal timing library, which is designed to be cross platform and provide high accuracy.
* Dynamic Loading - use our internal library DynamicLibrary until an appropriate external library is found.

## Write Compiler-Agnostic Code

Avoid using compiler-specific extensions since our code should compile under multiple compiler. In particular avoid using #pragma once instead of include guards under Windows and dynamic arrays under gcc.

## API Guidelines

As an open source project, NuPIC is intended for use by a wide range of people. The API should be clean, professional, and easy to use. This section contains specific guidelines for implementing these API's.

### API Design = Marketing

Creating a great API is really a marketing task. You need to think about our users and try to put yourself in their mindset. The ease of learning an API is important, even for complex API's. This section discusses some general concepts related to these issues.

#### Missing step

Here is a crucial API design step that is often missed or skipped: before even implementing the API write out the common sequence of operations. Then ask yourself: is it simple enough? How can I make it simpler?

To do this, make your first set of unit tests reflect the common sequences. Write these tests as you implement the API. You should also write up some example code that illustrates the use of the API.

#### Layering

In thinking through the common sequences, make sure the API is "layered". A layered API makes easy tasks trivial, with very few function calls. At the same time it enables developers to do more complex tasks by providing additional methods and routines to control and change options/behavior.

#### Code Complexity

When in marketing, you have to be aware of your demographic. Do not assume that our customers are going to be Python or C++ coding gurus. Believe it or not, 75% of them are not going to be in the top 25%. They may still be very effective users (for example, they might be experts in statistics, or some other field). Many of them may be learning Python just to use our platform.

A related point to remember is that many C++ classes, functions, or method will likely be wrapped and made available to other languages such as Python.

Because of these two situations, stick to very basic constructs in the API. No enums. No templates. Should we allow const in APIs?

As much as possible, method signatures should not require fancy constructs (e.g. lambda functions in Python or streams in C/C++). Try to avoid passing in other fancy C++ or Python structures.

#### Market Research

In marketing it is often a good idea to do some market research. The nice thing is that in a development-oriented company there are no lack of developers.

## Naming conventions

This section supplements the general discussion on naming conventions. The naming conventions in that section apply to API's. Although the items discussed in this section can be applied to any source code, they are particularly relevant (and will be enforced) in our API.

Names should be meaningful and specific. "Constructors" is not a good name as it is too generic. "NodeConstructors" is a good name.

Use names and terminology consistently throughout the API. Use names and terms in a manner that is consistent with the rest of our usage. Before using a term, search our codebase and docs for how they are used. [Note: we should create an API glossary for the Reference Manual.]

See Cocoa API coding guidelines for more discussion on these topics:

[http://developer.apple.com/documentation/Cocoa/Conceptual/CodingGuidelines/CodingGuidelines.html](http://developer.apple.com/documentation/Cocoa/Conceptual/CodingGuidelines/CodingGuidelines.html)

### Abbreviations

In general don't abbreviate, even if you think the abbreviation is common. This is hard to do as good programmers are often lazy typists. Spell things out so they are clear. Longer names are better than abbreviated ones.

For example, 'maxCoinc' is not a good name. 'maxCoincidence' is a much clearer name. 'max_d' is not a good name. 'maxDistance' is much better.

#### Acceptable abbreviations

In general, the abbreviations listed on [http://developer.apple.com/documentation/Cocoa/Conceptual/CodingGuidelines/Articles/APIAbbreviations.html](http://developer.apple.com/documentation/Cocoa/Conceptual/CodingGuidelines/Articles/APIAbbreviations.html) are okay to use.

The following HTM specific abbreviations are ok to use:

* SDR - Sparse Distributed Representation
* SP - Spatial Pooler
* TM - Temporal Memory
* HTM - Hierarchical Temporal Memory
* Net - network
* TAM - Temporal Adjacency Matrix
* TBI - Time Based Inference

## API Documentation

Documentation is clearly important for an API. Our reference guides will draw heavily from the code documentation. Document everything from the point of view of a first-time developer. Don't assume they know about every other part of the system.

The documentation conventions for API header files are stricter than for other source code. API header files should follow the example in Section 2.5.3 strictly, including spacing, commenting standard, the use of "/**" vs "//" etc. Methods with parameters should contain appropriate @param lines. Return values should be marked with @retval.

## Error Handling

We should not throw exceptions across language boundaries.

The vast majority of developers will make errors in using an API. It is just a part of learning and development. Therefore, good error handling is crucial.

### What errors should you check for?

Any condition that can be caused by situations outside of the control of our software should be checked. This includes user errors such as illegal parameter values, buffer overflows, and using wrong sequence of API calls.

It includes environmental errors, such as failed connections, hard drive full, and data corruption.

It is also helpful to provide warnings for situations where the user could get into trouble. For example, suppose you have a node in a network that is not connected to any other nodes. This is not strictly an error but it would be nice if our tools gave a warning.

In general we don't need to check for out of memory conditions.

### Where should you check for errors?

As much as possible, the entry points into the API should check for any errors. Error results returned from deep within the system are usually incomprehensible to the user.

### How should you handle errors?

Our system must have clear error messages for everything. Error messages should be specific, such as "Parameter 'maxCoincidences' to node N is out of range" rather than "illegal parameter" or "stack overflow".

Be careful about throwing exceptions in the API layer, particularly if the layer is going to be wrapped into another language.

## Miscellaneous

Header files - for C or C++ API's, include a single header file that developers will include. It should be a container that includes other required header files. For example, "nta_plugin.hpp" should be sufficient for all C++ plugin developers.

In C++ classes users will care more about the public members than private members. Thus, for C++ header files always put public members first, then private members.

## Node API Guidelines

Nodes are implemented as plugins in NuPIC. These nodes have a NodeSpec, containing node documentation, input and output variable names, parameters, and execute commands. The NodeSpec in essence defines the API of the node. Over time some conventions have arisen regarding names and functionality of specific NodeSpec items. Internal and third party tools, as well as customer code, now rely on some of this and we expect this reliance to grow in the future.

It is therefore useful to codify some general and specific guidelines regarding NodeSpec items. This section covers these guidelines and is intended for nodes released to customers. Both PyNodes and C++ nodes have NodeSpec's and should adhere to these guidelines.

## General Guidelines

The node name should be camelBack notation with a leading upper case, such as "Zeta1TopNode". Inputs, outputs, parameter names, and execute commands should be camelBack notation with a leading lower case letter and no trailing underscore, such as "exampleParameter".

All nodes should fill in the general description field of NodeSpec to contain a general description of the node purpose and functionality. All inputs, outputs, parameters and execute commands should have the description field set to something useful. The type should be set to the most specific applicable type, and the constraints field should be set appropriately.

## Specific Guidelines

The following table lists specific conventions that all externally released nodes should follow. These names should also be considered "reserved" for the usage specified here (for example, if a node has a parameter categoryCount, it must have the meaning specified below).

<table>
<thead>
<tr>
  <th>nodeSpecItem name</th>
  <th>Type</th>
  <th>Node type</th>
  <th>Description</th>
</tr>
</thead>
<tbody><tr>
  <td>dataOut</td>
  <td>O</td>
  <td>NL</td>
  <td>The primary output of the node</td>
</tr>
<tr>
  <td>dataIn</td>
  <td>I</td>
  <td>NL</td>
  <td>The primary input to the node</td>
</tr>
<tr>
  <td>bottomUpOut</td>
  <td>O</td>
  <td>LUnsup</td>
  <td>Output from a learning node (intended for higher level nodes)</td>
</tr>
<tr>
  <td>bottomUpIn</td>
  <td>I</td>
  <td>L</td>
  <td>Input to a learning node (intended to be from lower level nodes)</td>
</tr>
<tr>
  <td>topDownIn</td>
  <td>I</td>
  <td>L</td>
  <td>(optional) Input to a learning node (intended for nodes that receive   input from higher level nodes)</td>
</tr>
<tr>
  <td>topDownOut</td>
  <td>O</td>
  <td>L</td>
  <td>(optional) Output from a learning node (intended for nodes that send   output to lower level nodes)</td>
</tr>
<tr>
  <td>maxOutputVectorCount</td>
  <td>P</td>
  <td>S</td>
  <td>An integer denoting the number of output vectors that can be   generated by this sensor under the current configuration. This should take   into account the loaded data as well as explorer configurations, repeat   counts, etc. The sensor should return -1 where meaningless or infinite (such   as for random sensors or when reading from live streams).</td>
</tr>
<tr>
  <td>position</td>
  <td>P</td>
  <td>S</td>
  <td>(optional) Refers to sensors that have a discrete number of data   items loaded. These items could be vectors, sequences, images, etc. When   implemented it should have the following meaning: if position is set to an   integer N, the next call to compute should output the first vector from the   N’th item. When retrieved, the sensor should return the item number. The   sensor should precisely define the data item that is returned.</td>
</tr>
<tr>
  <td>seek</td>
  <td>C</td>
  <td>S</td>
  <td>(optional) When implemented, it should have the   following meaning: “seek “; should set the sensor state to be equivalent to   re-starting the sensor in the current configuration and performing n-1   compute’s. In other words the next compute should cause it to output the n’th   output vector. When this concept is meaningless (such as for random   sensors or when reading from live streams), the command should return an   exception.</td>
</tr>
<tr>
  <td>activeOutputCount</td>
  <td></td>
  <td>All nodes with outputs</td>
  <td>An integer indicating the number of output elements that are actually   being used by the primary output (typically dataOut or bottomUpOut)</td>
</tr>
<tr>
  <td>inferenceMode</td>
  <td>P</td>
  <td>L</td>
  <td>A boolean. Return value indicates whether node is performing   inference. When the parameter is set, the node should begin inference under   the current inference configuration.</td>
</tr>
<tr>
  <td>learningMode</td>
  <td>P</td>
  <td>L</td>
  <td>A boolean. Return value indicates whether node is currently   performing learning. When the parameter is set, the node should begin   learning under the current learning configuration.</td>
</tr>
<tr>
  <td>categoryCount</td>
  <td>P</td>
  <td>LSup</td>
  <td>An integer indicating the number of categories that have been learned</td>
</tr>
<tr>
  <td>categoryIn</td>
  <td>I</td>
  <td>LSup</td>
  <td>An input denoting the true   category of the current input to the node. This could be a single number   denoting the category index or a   string label. Used only during training.</td>
</tr>
<tr>
  <td>categoriesOut</td>
  <td>O</td>
  <td>LSup</td>
  <td>A vector of reals representing, for each category index, the   likelihood that the input to the node belongs to that category. This output is meaningful only when   the node is in inference mode and should be set to all zeros otherwise</td>
</tr>
<tr>
  <td>coincidenceCount</td>
  <td>P</td>
  <td>LSpatial</td>
  <td>An integer representing the number of learned coincidences</td>
</tr>
<tr>
  <td>spatialPoolerOutput</td>
  <td>P</td>
  <td>LSpatial</td>
  <td>The output vector of the spatial pooler representing a distribution   over coincidences</td>
</tr>
<tr>
  <td>sparseCoincidenceMatrix</td>
  <td>P</td>
  <td>LSpatial</td>
  <td>A SparseMatrix representing all learned coincidences</td>
</tr>
<tr>
  <td>spatialPoolerAlgorithm</td>
  <td>P</td>
  <td>LSpatial</td>
  <td>An enum denoting the specific algorithm being used for spatial pooling</td>
</tr>
<tr>
  <td>coincidenceVectorCounts</td>
  <td>P</td>
  <td>LTAM</td>
  <td>An array of integers representing the frequency of each coincidence   encountered during learning</td>
</tr>
<tr>
  <td>symmetricTime</td>
  <td>P</td>
  <td>LTAM</td>
  <td>A boolean indicating whether the node assumes that time is symmetric</td>
</tr>
<tr>
  <td>temporalPoolerAlgorithm</td>
  <td>P</td>
  <td>LTAM</td>
  <td>An enum denoting the specific algorithm being used for temporal   pooling</td>
</tr>
<tr>
  <td>TAM</td>
  <td>P</td>
  <td>LTAM</td>
  <td>A SparseMatrix representing the full TAM</td>
</tr>
<tr>
  <td>overlappingGroups</td>
  <td>P</td>
  <td>LTAM</td>
  <td>Boolean indicating whether groups can be overlapped</td>
</tr>
<tr>
  <td>groupCount</td>
  <td>P</td>
  <td>LTAM</td>
  <td>Integer indicating the number of learned groups</td>
</tr>
<tr>
  <td>groups</td>
  <td>P</td>
  <td>LTAM</td>
  <td>The set of coincidences belonging to each group, returned as a list   of list of coincidence indices. The exact format should be the same as in   Zeta1Node.</td>
</tr>
</tbody></table>

Note: The items here represent a best guess as to what makes sense for the types of nodes specified. Given that the core algorithms in NuPIC are changing rapidly, as is our understanding of HTM applications, there is a good chance that changes will be made to the above list. However, where it makes sense, we should follow the above conventions.

"Type" and "Node type" Key:

- __I__ - Input
- __O__ - Output
- __P__ - Parameter
- __C__ - Execute command
- __S__ - sensors
- __NL__ - all non-learning nodes (sensors, effectors, pass through nodes, etc.)
- __L__ - all learning nodes
- __LSup__ - all supervised learning nodes
- __LUnsup__ - all unsupervised learning nodes
- __LSpatial__ - all learning nodes with a spatial pooler that learns coincidences
- __LTAM__ - all learning nodes using a transition matrix and computing groups from the transition matrix

## Example Code Guidelines

Example code has a tough job. It needs to educate and illuminate. It needs to work out of the box. It needs to be understandable to a developer who knows very little about our system and very little about Python or C++. Examples are the starting point for hands-on work with our system. They often serve as a framework for more complex applications.

General and specific guidelines for example code are below. The Bitworm and Waves examples can be used as Example code examples.

### General Guidelines

The following general guidelines should be followed when creating example code that is released as part of NuPIC:

* The target audience for simple examples: a programmer with some development experience and little or no prior exposure to Python. The developer may be coming from another discipline with little formal programming background.
* Keep coding style as simple and basic as possible. Avoid fancy language constructs. In Python, avoid list comprehensions, map, and other advanced constructs. Stick to simple loops, if statements, and function calls.
* Keep simple examples simple! Keep the number of lines of code down to less than a page. If you have non-trivial code in several lines, perhaps that should become part of the tool library itself? At the very least it can become a function in a separate utility file.
* Don't throw too many options into the example code. This becomes very confusing for developers. Split them out into separate example files that can be learned in sequence.
* Remember that developers often start by modifying sample code. As such, the longevity of the code is far longer than just running and understanding the example.

### Specific Guidelines

The following specific guidelines should be followed in examples:

* Examples should make an effort to use the best tools API for the job. No examples should use deprecated API calls.
* Complex examples should contain a README.md file.
* No auto-generated files should be included in the source tree or in the release. Exceptions are trained network files that take a long time to generate (e.g. distorted Pictures files).
* There should be a "cleanup.py" script that cleans up all auto-generated files, .pyc files, Visualizer files, and directories (including bundle directories).
* Source files should be well commented and include the appropriate copyright header.
* There should be a "run_once.py" in all folders that goes through the full sequence. See below for run_once.py guidelines
* There should be generate_data.py, create_network.py, etc. files for each step of the examples. The naming should be kept consistent across examples.
* generate_report should create a file report.txt. This file should contain an English report that is very readable and conversational in tone. Should compare both training and test results and reports accuracy on both. Should show overall learning      statistics such as number of coincidences and groups for each node.
* The more complex examples should contain some experiments that can be run. There should be a top level RunExperiment.py that can take command line option (e.g. experiment name) and run that experiment. There should be a subdirectory called "experiments" that contains each actual experiment.
* There should be nightly tests for each of the official examples that check the functionality and code. These tests should be in the qa directory, NOT in the examples directory!
