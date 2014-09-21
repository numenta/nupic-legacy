/* -----------------------------------------------------------------------------
 * guile_gh_run.swg
 *
 * Guile GH runtime file
 * ----------------------------------------------------------------------------- */

#define SWIGGUILE
#include "guile/gh.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef SCM (*swig_guile_proc)();

#define SWIG_malloc(size) \
  SCM_MUST_MALLOC(size)
#define SWIG_free(mem) \
  scm_must_free(mem)
#define SWIG_ConvertPtr(s, result, type, flags) \
  SWIG_Guile_ConvertPtr(&swig_module, s, result, type, flags)
#define SWIG_MustGetPtr(s, type, argnum, flags) \
  SWIG_Guile_MustGetPtr(&swig_module, s, type, argnum, flags, FUNC_NAME)
#define SWIG_NewPointerObj(ptr, type, owner) \
  SWIG_Guile_NewPointerObj(&swig_module, (void*)ptr, type, owner)
#define SWIG_GetModule(clientdata) SWIG_Guile_GetModule()
#define SWIG_SetModule(clientdata, pointer) SWIG_Guile_SetModule(pointer)

/* Ignore object-ownership changes in gh mode */
#define SWIG_Guile_MarkPointerNoncollectable(s) (s)
#define SWIG_Guile_MarkPointerDestroyed(s) (s)
  
#define SWIG_contract_assert(expr, msg)				\
  if (!(expr))							\
    scm_error(gh_symbol2scm("swig-contract-assertion-failed"),	\
	      (char *) FUNC_NAME, (char *) msg,			\
	      SCM_EOL, SCM_BOOL_F); else

/* SCM_CHAR and SCM_CHARP were introduced in Guile 1.4; the following is for
   1.3.4 compatibility. */
#ifndef SCM_CHAR
#  define SCM_CHAR SCM_ICHR
#endif
#ifndef SCM_CHARP
#  define SCM_CHARP SCM_ICHRP
#endif

/* This function replaces gh_scm2char, which is broken in Guile 1.4 */
SWIGINTERN char
GSWIG_scm2char (SCM s)
{
  if (SCM_CHARP(s)) return SCM_CHAR(s);
  scm_wrong_type_arg(NULL, 0, s);
}
#define gh_scm2char GSWIG_scm2char

/* Interface function */
#define SWIG_scm2str(x) gh_scm2newstr(x, NULL)

/* More 1.3.4 compatibility */
#ifndef SCM_INPUT_PORT_P
#  define SCM_INPUT_PORT_P SCM_INPORTP
#  define SCM_OUTPUT_PORT_P SCM_OUTPORTP
#endif

SWIGINTERN long
SWIG_convert_integer(SCM o,
		     long lower_bound, long upper_bound, 
		     const char *func_name, int argnum)
{
  long value = gh_scm2long(o);
  if (value < lower_bound || value > upper_bound)
    scm_wrong_type_arg((char *) func_name, argnum, o);
  return value;
}
  
SWIGINTERN unsigned long
SWIG_convert_unsigned_integer(SCM o,
			      unsigned long lower_bound,
			      unsigned long upper_bound, 
			      const char *func_name, int argnum)
{
  unsigned long value = gh_scm2ulong(o);
  if (value < lower_bound || value > upper_bound)
    scm_wrong_type_arg((char *) func_name, argnum, o);
  return value;
}

SWIGINTERN swig_type_info *
SWIG_Guile_LookupType(swig_module_info *module, SCM s, int normal) 
{
  swig_module_info *iter;
  if (!module) return 0;
  iter = module;
  do {
    if ((normal && (unsigned long) SCM_TYP16(s) == *((int *)iter->clientdata))) {
        
      return iter->types[(long) SCM_CAR(s) >> 16];
    }
    iter = iter->next;
  } while (iter != module);
  return 0;
}

#ifdef SWIG_GLOBAL
#define SWIG_GUILE_MODULE_STATIC
#elif !defined(SWIG_NOINCLUDE)
#define SWIG_GUILE_MODULE_STATIC static
#endif

#ifdef SWIG_GUILE_MODULE_STATIC
static swig_module_info *swig_guile_module = 0;
SWIG_GUILE_MODULE_STATIC swig_module_info *SWIG_Guile_GetModule(void) {
  return swig_guile_module;
}
SWIG_GUILE_MODULE_STATIC void SWIG_Guile_SetModule(swig_module_info *pointer) {
  swig_guile_module = pointer;
}
#else
SWIGEXPORT swig_module_info * SWIG_Guile_GetModule(void);
SWIGEXPORT void SWIG_Guile_SetModule(swig_module_info *pointer);
#endif

SWIGINTERN SCM
SWIG_Guile_NewPointerObj(swig_module_info *module, void *ptr, 
			 swig_type_info *type, int owner)
{
  unsigned long tag;
  if (ptr==NULL) return SCM_EOL;
  if (!module) return SCM_EOL;
  for (tag = 0; tag < module->size; ++tag) {
    if (module->types[tag] == type)
      break;
  }
  if (tag >= module->size)
    return SCM_EOL;
    

  SCM_RETURN_NEWSMOB( ((tag << 16) | *((int *)module->clientdata)), ptr);
}

/* Return 0 if successful. */
SWIGINTERN int
SWIG_Guile_ConvertPtr(swig_module_info *module, SCM s, void **result, 
		      swig_type_info *type, int flags)
{
  swig_cast_info *cast;
  swig_type_info *from;
  if (SCM_NULLP(s)) {
    *result = NULL;
    return SWIG_OK;
  } else if (SCM_NIMP(s)) {
    from = SWIG_Guile_LookupType(module, s, 1);
    if (!from) return SWIG_ERROR;
    if (type) {
      cast = SWIG_TypeCheckStruct(from, type);
      if (cast) {
        int newmemory = 0;
        *result = SWIG_TypeCast(cast, (void *) SCM_CDR(s), &newmemory);
        assert(!newmemory); /* newmemory handling not yet implemented */
        return SWIG_OK;
      } else {
        return SWIG_ERROR;
      }
    } else {
      *result = (void *) SCM_CDR(s);
      return SWIG_OK;
    }
  }
  return SWIG_ERROR;
}

SWIGINTERN void *
SWIG_Guile_MustGetPtr (swig_module_info *module, SCM s, swig_type_info *type,
                       int argnum, int flags, const char *func_name)
{
  void *result;
  int res = SWIG_Guile_ConvertPtr(module, s, &result, type, flags);
  if (!SWIG_IsOK(res)) {
    /* type mismatch */
    scm_wrong_type_arg((char *) func_name, argnum, s);
  }
  return result;
}

/* Init */

SWIGINTERN int
print_swig (SCM swig_smob, SCM port, scm_print_state *pstate)
{
  swig_type_info *type = SWIG_Guile_LookupType(0, swig_smob, 1);
  if (type) {
    scm_puts((char *) "#<swig ", port);
    if (type->str != NULL)
      scm_puts((char *) type->str, port);
    else 
      scm_puts((char *) type->name, port);
    scm_puts((char *) " ", port);
    scm_intprint((long) SCM_CDR(swig_smob), 16, port);
    scm_puts((char *) ">", port);
    /* non-zero means success */
    return 1;
  } else {
    return 0;
  }
}

SWIGINTERN SCM
equalp_swig (SCM A, SCM B)
{
  if (SCM_CAR(A) == SCM_CAR(B)
      && SCM_CDR(A) == SCM_CDR(B))
    return SCM_BOOL_T;
  else return SCM_BOOL_F;
}

SWIGINTERN void
SWIG_Guile_Init (swig_module_info *module)
{
    *((int *)module->clientdata) = 
         scm_make_smob_type_mfpe((char *) "swig", 0, NULL, NULL, print_swig, equalp_swig);
}

SWIGINTERN int
SWIG_Guile_GetArgs (SCM *dest, SCM rest,
		    int reqargs, int optargs,
		    const char *procname)
{
  int i;
  int num_args_passed = 0;
  for (i = 0; i<reqargs; i++) {
    if (!SCM_CONSP(rest))
      scm_wrong_num_args(gh_str02scm((char *) procname));
    *dest++ = SCM_CAR(rest);
    rest = SCM_CDR(rest);
    num_args_passed++;
  }
  for (i = 0; i<optargs && SCM_CONSP(rest); i++) {
    *dest++ = SCM_CAR(rest);
    rest = SCM_CDR(rest);
    num_args_passed++;
  }
  for (; i<optargs; i++)
    *dest++ = SCM_UNDEFINED;
  if (!SCM_NULLP(rest))
    scm_wrong_num_args(gh_str02scm((char *) procname));
  return num_args_passed;
}

#ifdef __cplusplus
}
#endif

/* guile.swg ends here */
