/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * php4run.swg
 *
 * PHP4 runtime library
 * ----------------------------------------------------------------------------- */

#ifdef __cplusplus
extern "C" {
#endif
#include "zend.h"
#include "zend_API.h"
#include "php.h"

#ifdef ZEND_RAW_FENTRY
/* ZEND_RAW_FENTRY was added somewhere between 5.2.0 and 5.2.3 */
# define SWIG_ZEND_NAMED_FE(ZN, N, A) ZEND_RAW_FENTRY((char*)#ZN, N, A, 0)
#else
/* This causes warnings from GCC >= 4.2 (assigning a string literal to char*).
 * But this seems to be unavoidable without directly assuming knowledge of
 * the structure, which changed between PHP4 and PHP5. */
# define SWIG_ZEND_NAMED_FE(ZN, N, A) ZEND_NAMED_FE(ZN, N, A)
#endif

#define SWIG_LONG_CONSTANT(N, V) zend_register_long_constant((char*)#N, sizeof(#N), V, CONST_CS | CONST_PERSISTENT, module_number TSRMLS_CC)
#define SWIG_DOUBLE_CONSTANT(N, V) zend_register_double_constant((char*)#N, sizeof(#N), V, CONST_CS | CONST_PERSISTENT, module_number TSRMLS_CC)
#define SWIG_STRING_CONSTANT(N, V) zend_register_stringl_constant((char*)#N, sizeof(#N), V, strlen(V), CONST_CS | CONST_PERSISTENT, module_number TSRMLS_CC)
#define SWIG_CHAR_CONSTANT(N, V) do {\
    static char swig_char = (V);\
    zend_register_stringl_constant((char*)#N, sizeof(#N), &swig_char, 1, CONST_CS | CONST_PERSISTENT, module_number TSRMLS_CC);\
} while (0)

/* These TSRMLS_ stuff should already be defined now, but with older php under
   redhat are not... */
#ifndef TSRMLS_D
#define TSRMLS_D
#endif
#ifndef TSRMLS_DC
#define TSRMLS_DC
#endif
#ifndef TSRMLS_C
#define TSRMLS_C
#endif
#ifndef TSRMLS_CC
#define TSRMLS_CC
#endif

#ifdef __cplusplus
}
#endif

/* But in fact SWIG_ConvertPtr is the native interface for getting typed
   pointer values out of zvals.  We need the TSRMLS_ macros for when we
   make PHP type calls later as we handle php resources */
#define SWIG_ConvertPtr(obj,pp,type,flags) SWIG_ZTS_ConvertPtr(obj,pp,type,flags TSRMLS_CC)


#define SWIG_fail goto fail

static const char *default_error_msg = "Unknown error occurred";
static int default_error_code = E_ERROR;

#define SWIG_PHP_Arg_Error_Msg(argnum,extramsg) "Error in argument " #argnum " "#extramsg

#define SWIG_PHP_Error(code,msg) do { SWIG_ErrorCode() = code; SWIG_ErrorMsg() = msg; SWIG_fail; } while (0)

#define SWIG_contract_assert(expr,msg) \
  if (!(expr) ) { zend_printf("Contract Assert Failed %s\n",msg ); } else

/* Standard SWIG API */
#define SWIG_GetModule(clientdata) SWIG_Php4_GetModule()
#define SWIG_SetModule(clientdata, pointer) SWIG_Php4_SetModule(pointer)

/* used to wrap returned objects in so we know whether they are newobject
   and need freeing, or not */
typedef struct _swig_object_wrapper {
  void * ptr;
  int newobject;
} swig_object_wrapper;

/* empty zend destructor for types without one */
static ZEND_RSRC_DTOR_FUNC(SWIG_landfill) { (void)rsrc; }

#define SWIG_SetPointerZval(a,b,c,d) SWIG_ZTS_SetPointerZval(a,b,c,d TSRMLS_CC)

static void
SWIG_ZTS_SetPointerZval(zval *z, void *ptr, swig_type_info *type, int newobject TSRMLS_DC) {
  swig_object_wrapper *value=NULL;
  /*
   * First test for Null pointers.  Return those as PHP native NULL
   */
  if (!ptr ) {
    ZVAL_NULL(z);
    return;
  }
  if (type->clientdata) {
    if (! (*(int *)(type->clientdata)))
      zend_error(E_ERROR, "Type: %s failed to register with zend",type->name);
    value=(swig_object_wrapper *)emalloc(sizeof(swig_object_wrapper));
    value->ptr=ptr;
    value->newobject=newobject;
    ZEND_REGISTER_RESOURCE(z, value, *(int *)(type->clientdata));
    return;
  }
  zend_error(E_ERROR, "Type: %s not registered with zend",type->name);
}

/* This pointer conversion routine takes the native pointer p (along with
   its type name) and converts it by calling appropriate casting functions
   according to ty.  The resultant pointer is returned, or NULL is returned
   if the pointer can't be cast.

   Sadly PHP has no API to find a type name from a type id, only from an
   instance of a resource of the type id, so we have to pass type_name as well.

   The two functions which might call this are:
   SWIG_ZTS_ConvertResourcePtr which gets the type name from the resource
   and the registered zend destructors for which we have one per type each
   with the type name hard wired in. */
static void *
SWIG_ZTS_ConvertResourceData(void * p, const char *type_name, swig_type_info *ty TSRMLS_DC) {
  swig_cast_info *tc;
  void *result = 0;

  if (!ty) {
    /* They don't care about the target type, so just pass on the pointer! */
    return p;
  }

  if (! type_name) {  
    /* can't convert p to ptr type ty if we don't know what type p is */
    return NULL;
  }

  /* convert and cast p from type_name to ptr as ty. */
  tc = SWIG_TypeCheck(type_name, ty);
  if (tc) {
    int newmemory = 0;
    result = SWIG_TypeCast(tc, p, &newmemory);
    assert(!newmemory); /* newmemory handling not yet implemented */
  }
  return result;
}

/* This function returns a pointer of type ty by extracting the pointer
   and type info from the resource in z.  z must be a resource.
   If it fails, NULL is returned.
   It uses SWIG_ZTS_ConvertResourceData to do the real work. */
static void *
SWIG_ZTS_ConvertResourcePtr(zval *z, swig_type_info *ty, int flags TSRMLS_DC) {
  swig_object_wrapper *value;
  void *p;
  int type;
  char *type_name;

  value = (swig_object_wrapper *) zend_list_find(z->value.lval, &type);
  if ( flags && SWIG_POINTER_DISOWN ) {
    value->newobject = 0;
  }
  p = value->ptr;
  if (type==-1) return NULL;

  type_name=zend_rsrc_list_get_rsrc_type(z->value.lval TSRMLS_CC);

  return SWIG_ZTS_ConvertResourceData(p, type_name, ty TSRMLS_CC);
}

/* We allow passing of a RESOURCE pointing to the object or an OBJECT whose
   _cPtr is a resource pointing to the object */
static int
SWIG_ZTS_ConvertPtr(zval *z, void **ptr, swig_type_info *ty, int flags TSRMLS_DC) {
  if (z == NULL) {
    *ptr = 0;
    return 0;
  }

  switch (z->type) {
    case IS_OBJECT: {
      zval ** _cPtr;
      if (zend_hash_find(HASH_OF(z),(char*)"_cPtr",sizeof("_cPtr"),(void**)&_cPtr)==SUCCESS) {
	if ((*_cPtr)->type==IS_RESOURCE) {
	  *ptr = SWIG_ZTS_ConvertResourcePtr(*_cPtr, ty, flags TSRMLS_CC);
	  return (*ptr == NULL ? -1 : 0);
	}
      }
      break;
    }
    case IS_RESOURCE:
      *ptr = SWIG_ZTS_ConvertResourcePtr(z, ty, flags TSRMLS_CC);
      return (*ptr == NULL ? -1 : 0);
    case IS_NULL:
      *ptr = 0;
      return 0;
  }

  return -1;
}

static char const_name[] = "swig_runtime_data_type_pointer";
static swig_module_info *SWIG_Php4_GetModule() {
  zval *pointer;
  swig_module_info *ret = 0;

  MAKE_STD_ZVAL(pointer);

  TSRMLS_FETCH();

  if (zend_get_constant(const_name, sizeof(const_name), pointer TSRMLS_CC)) {
    if (pointer->type == IS_LONG) {
      ret = (swig_module_info *) pointer->value.lval;
    }
  } 
  FREE_ZVAL(pointer);
  return ret; 
}

static void SWIG_Php4_SetModule(swig_module_info *pointer) {
  TSRMLS_FETCH();
  REGISTER_MAIN_LONG_CONSTANT(const_name, (long) pointer, 0);
}
