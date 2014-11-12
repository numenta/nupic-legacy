/* -----------------------------------------------------------------------------
 * javascriptruntime.swg
 *
 * ----------------------------------------------------------------------------- */

// V8 Version Macro
// ----------------
// v8 does not (until now) provide a version macro - which is still discussed and may come soon.
// Until then, we set a default version which can be overridden via command line using V8_VERSION:
//   swig -javascript -v8 -DV8_VERSION=0x031110
// Or code in the interface file using SWIG_V8_VERSION:
//   %begin %{#define SWIG_V8_VERSION 0x031110%}

%define %swig_v8_define_version(version)
%insert("runtime") %{
#ifndef SWIG_V8_VERSION
#define SWIG_V8_VERSION version
#endif
%}
%enddef

#ifdef V8_VERSION
%swig_v8_define_version(V8_VERSION)
#else
// HACK: defining a default version
%swig_v8_define_version(0x031110)
#endif


// Node support
// ------------

#ifdef BUILDING_NODE_EXTENSION
%insert("runtime") %{
#include <node.h>
%}
#endif


// V8 runtime
// ----------

%insert(runtime) %{
#include <v8.h>

#include <errno.h>
#include <limits.h>
#include <stdlib.h>
%}

%insert(runtime) "swigrun.swg";         /* SWIG API */
%insert(runtime) "swigerrors.swg";      /* SWIG errors */

%insert(runtime) "javascriptrun.swg"

