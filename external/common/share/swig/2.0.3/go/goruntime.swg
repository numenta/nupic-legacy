/* ------------------------------------------------------------
 * goruntime.swg
 *
 * Go runtime code for the various generated files.
 * ------------------------------------------------------------ */

%insert(runtime) %{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char *p; int n; } _gostring_;
typedef struct { void* array; unsigned int len; unsigned int cap; } _goslice_;

%}

#ifndef SWIGGO_GCCGO
/* Boilerplate for C/C++ code when using 6g/8g.  This code is compiled
   with gcc.  */
%insert(runtime) %{

#define swiggo_size_assert_eq(x, y, name) typedef char name[(x-y)*(x-y)*-2+1];
#define swiggo_size_assert(t, n) swiggo_size_assert_eq(sizeof(t), n, swiggo_sizeof_##t##_is_not_##n)

swiggo_size_assert(char, 1)
swiggo_size_assert(short, 2)
swiggo_size_assert(int, 4)
typedef long long swiggo_long_long;
swiggo_size_assert(swiggo_long_long, 8)
swiggo_size_assert(float, 4)
swiggo_size_assert(double, 8)

#ifdef __cplusplus
extern "C" {
#endif
extern void crosscall2(void (*fn)(void *, int), void *, int);
extern void _cgo_allocate(void *, int);
extern void _cgo_panic(void *, int);
#ifdef __cplusplus
}
#endif

static void *_swig_goallocate(size_t len) {
  struct {
    size_t len;
    void *ret;
  } a;
  a.len = len;
  crosscall2(_cgo_allocate, &a, (int) sizeof a);
  return a.ret;
}

static void _swig_gopanic(const char *p) {
  struct {
    const char *p;
  } a;
  a.p = p;
  crosscall2(_cgo_panic, &a, (int) sizeof a);
}

%}

/* Boilerplate for C code when using 6g/8g.  This code is compiled
   with 6c/8c.  */
%insert(gc_header) %{
#include "runtime.h"
#include "cgocall.h"

#ifdef _64BIT
#define SWIG_PARM_SIZE 8
#else
#define SWIG_PARM_SIZE 4
#endif
%}

#else

/* Boilerplate for C/C++ code when using gccgo.  */
%insert(runtime) %{
#define SWIGGO_GCCGO

#ifdef __cplusplus
extern "C" {
#endif
extern void *_cgo_allocate(size_t);
extern void _cgo_panic(const char *);
#ifdef __cplusplus
}
#endif

#define _swig_goallocate _cgo_allocate
#define _swig_gopanic _cgo_panic

%}

#endif

%insert(runtime) %{

static _gostring_ _swig_makegostring(const char *p, size_t l) {
  _gostring_ ret;
  ret.p = (char*)_swig_goallocate(l + 1);
  memcpy(ret.p, p, l);
  ret.n = l;
  return ret;
}

#define SWIG_contract_assert(expr, msg) \
  if (!(expr)) { _swig_gopanic(msg); } else
%}

#ifndef SWIGGO_GCCGO

%insert(go_header) %{

import _ "runtime/cgo"

%}

#endif

/* Function pointers are translated by the code in go.cxx into
   _swig_fnptr.  Member pointers are translated to _swig_memberptr.  */

%insert(go_header) %{
type _swig_fnptr *byte
type _swig_memberptr *byte
%}
