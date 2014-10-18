/* -----------------------------------------------------------------------------
 * phprun.swg
 *
 * PHP runtime library
 * ----------------------------------------------------------------------------- */

#ifdef __cplusplus
extern "C" {
#endif
#include "zend.h"
#include "zend_API.h"
#include "zend_exceptions.h"
#include "php.h"
#include "ext/standard/php_string.h"
#include <stdlib.h> /* for abort(), used in generated code. */

#ifdef ZEND_RAW_FENTRY
/* ZEND_RAW_FENTRY was added somewhere between 5.2.0 and 5.2.3 */
# define SWIG_ZEND_NAMED_FE(ZN, N, A) ZEND_RAW_FENTRY((char*)#ZN, N, A, 0)
#else
/* This causes warnings from GCC >= 4.2 (assigning a string literal to char*).
 * But this seems to be unavoidable without directly assuming knowledge of
 * the structure, which changed between PHP4 and PHP5. */
# define SWIG_ZEND_NAMED_FE(ZN, N, A) ZEND_NAMED_FE(ZN, N, A)
#endif

#ifndef Z_SET_ISREF_P
/* For PHP < 5.3 */
# define Z_SET_ISREF_P(z) (z)->is_ref = 1
#endif
#ifndef Z_SET_REFCOUNT_P
/* For PHP < 5.3 */
# define Z_SET_REFCOUNT_P(z, rc) (z)->refcount = (rc)
#endif

#define SWIG_LONG_CONSTANT(N, V) zend_register_long_constant((char*)#N, sizeof(#N), V, CONST_CS | CONST_PERSISTENT, module_number TSRMLS_CC)
#define SWIG_DOUBLE_CONSTANT(N, V) zend_register_double_constant((char*)#N, sizeof(#N), V, CONST_CS | CONST_PERSISTENT, module_number TSRMLS_CC)
#define SWIG_STRING_CONSTANT(N, V) zend_register_stringl_constant((char*)#N, sizeof(#N), (char*)(V), strlen(V), CONST_CS | CONST_PERSISTENT, module_number TSRMLS_CC)
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
#define SWIG_GetModule(clientdata) SWIG_Php_GetModule(clientdata)
#define SWIG_SetModule(clientdata, pointer) SWIG_Php_SetModule(pointer)

/* used to wrap returned objects in so we know whether they are newobject
   and need freeing, or not */
typedef struct {
  void * ptr;
  int newobject;
} swig_object_wrapper;

/* empty zend destructor for types without one */
static ZEND_RSRC_DTOR_FUNC(SWIG_landfill) { (void)rsrc; }

#define SWIG_SetPointerZval(a,b,c,d) SWIG_ZTS_SetPointerZval(a,b,c,d TSRMLS_CC)
#define SWIG_as_voidptr(a) const_cast< void * >(static_cast< const void * >(a))

static void
SWIG_ZTS_SetPointerZval(zval *z, void *ptr, swig_type_info *type, int newobject TSRMLS_DC) {
  /*
   * First test for Null pointers.  Return those as PHP native NULL
   */
  if (!ptr ) {
    ZVAL_NULL(z);
    return;
  }
  if (type->clientdata) {
    swig_object_wrapper *value;
    if (! (*(int *)(type->clientdata)))
      zend_error(E_ERROR, "Type: %s failed to register with zend",type->name);
    value=(swig_object_wrapper *)emalloc(sizeof(swig_object_wrapper));
    value->ptr=ptr;
    value->newobject=(newobject & 1);
    if ((newobject & 2) == 0) {
      /* Just register the pointer as a resource. */
      ZEND_REGISTER_RESOURCE(z, value, *(int *)(type->clientdata));
    } else {
      /*
       * Wrap the resource in an object, the resource will be accessible
       * via the "_cPtr" member. This is currently only used by
       * directorin typemaps.
       */
      zval *resource;
      zend_class_entry **ce = NULL;
      const char *type_name = type->name+3; /* +3 so: _p_Foo -> Foo */
      size_t type_name_len;
      int result;
      const char * p;

      /* Namespace__Foo -> Foo */
      /* FIXME: ugly and goes wrong for classes with __ in their names. */
      while ((p = strstr(type_name, "__")) != NULL) {
        type_name = p + 2;
      }
      type_name_len = strlen(type_name);

      MAKE_STD_ZVAL(resource);
      ZEND_REGISTER_RESOURCE(resource, value, *(int *)(type->clientdata));
      if (SWIG_PREFIX_LEN > 0) {
        char * classname = (char*)emalloc(SWIG_PREFIX_LEN + type_name_len + 1);
        strcpy(classname, SWIG_PREFIX);
        strcpy(classname + SWIG_PREFIX_LEN, type_name);
        result = zend_lookup_class(classname, SWIG_PREFIX_LEN + type_name_len, &ce TSRMLS_CC);
        efree(classname);
      } else {
        result = zend_lookup_class((char *)type_name, type_name_len, &ce TSRMLS_CC);
      }
      if (result != SUCCESS) {
        /* class does not exist */
        object_init(z);
      } else {
        object_init_ex(z, *ce);
      }
      Z_SET_REFCOUNT_P(z, 1);
      Z_SET_ISREF_P(z);
      zend_hash_update(HASH_OF(z), (char*)"_cPtr", sizeof("_cPtr"), (void*)&resource, sizeof(zval), NULL);
    }
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
  const char *type_name;

  value = (swig_object_wrapper *) zend_list_find(z->value.lval, &type);
  if (type==-1) return NULL;
  if (flags & SWIG_POINTER_DISOWN) {
    value->newobject = 0;
  }
  p = value->ptr;

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
static swig_module_info *SWIG_Php_GetModule(void *SWIGUNUSEDPARM(clientdata)) {
  zval *pointer;
  swig_module_info *ret = 0;
  TSRMLS_FETCH();

  MAKE_STD_ZVAL(pointer);

  if (zend_get_constant(const_name, sizeof(const_name) - 1, pointer TSRMLS_CC)) {
    if (pointer->type == IS_LONG) {
      ret = (swig_module_info *) pointer->value.lval;
    }
  } 
  FREE_ZVAL(pointer);
  return ret; 
}

static void SWIG_Php_SetModule(swig_module_info *pointer) {
  TSRMLS_FETCH();
  REGISTER_MAIN_LONG_CONSTANT(const_name, (long) pointer, 0);
}
