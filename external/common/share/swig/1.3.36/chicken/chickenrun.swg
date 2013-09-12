/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * chickenrun.swg
 *
 * ----------------------------------------------------------------------------- */

#include <chicken.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#if defined(_MSC_VER) || defined(__BORLANDC__) || defined(_WATCOM)
# ifndef snprintf
#  define snprintf _snprintf
# endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define SWIG_malloc(size) \
  malloc(size)
#define SWIG_free(mem) \
  free(mem)
#define SWIG_MakeString(c) \
  SWIG_Chicken_MakeString(c)
#define SWIG_ConvertPtr(s, result, type, flags) \
  SWIG_Chicken_ConvertPtr(s, result, type, flags)
#define SWIG_MustGetPtr(s, type, argnum, flags) \
  SWIG_Chicken_MustGetPtr(s, type, argnum, flags)
#define SWIG_NewPointerObj(ptr, type, owner) \
  SWIG_Chicken_NewPointerObj((void*)ptr, type, owner, &known_space)
#define swig_barf SWIG_Chicken_Barf
#define SWIG_ThrowException(val) SWIG_Chicken_ThrowException(val)

#define SWIG_contract_assert(expr, message) if (!(expr)) { \
                                              SWIG_Chicken_Barf(SWIG_BARF1_CONTRACT_ASSERT, C_text(message)); } else

/* Runtime API */
#define SWIG_GetModule(clientdata) SWIG_Chicken_GetModule()
#define SWIG_SetModule(clientdata, pointer) SWIG_Chicken_SetModule(pointer)

#define C_swig_is_bool(x) C_truep (C_booleanp (x))
#define C_swig_is_char(x) C_truep (C_charp (x))
#define C_swig_is_fixnum(x) C_truep (C_fixnump (x))
#define C_swig_is_flonum(x) (C_truep (C_blockp (x)) && C_truep (C_flonump (x)))
#define C_swig_is_string(x) (C_truep (C_blockp (x)) && C_truep (C_stringp (x)))
#define C_swig_is_vector(x) (C_truep (C_blockp (x)) && C_truep (C_vectorp (x)))
#define C_swig_is_list(x) (C_truep (C_i_listp (x)))
#define C_swig_is_pair(x) (C_truep (C_blockp(x)) && C_truep (C_pairp(x)))
#define C_swig_is_ptr(x) (C_truep (C_blockp (x)) && C_truep (C_pointerp (x)))
#define C_swig_is_swigpointer(x) (C_truep (C_blockp(x)) && C_truep (C_swigpointerp(x)))
#define C_swig_is_closurep(x) (C_truep (C_blockp(x)) && C_truep(C_closurep(x)))
#define C_swig_is_number(x) (C_swig_is_fixnum(x) || C_swig_is_flonum(x))
#define C_swig_is_long(x) C_swig_is_number(x)

#define C_swig_sizeof_closure(num) (num+1)

#define SWIG_Chicken_SetupArgout { \
  C_word *a = C_alloc(C_swig_sizeof_closure(2)); \
  C_word *closure = a; \
  *(a++)=C_CLOSURE_TYPE|2; \
  *(a++)=(C_word)SWIG_Chicken_ApplyResults; \
  *(a++)=continuation; \
  continuation=(C_word)closure; \
}

#define SWIG_APPEND_VALUE(obj) { \
  C_word val = (C_word)(obj); \
  if (val != C_SCHEME_UNDEFINED) { \
    C_word *a = C_alloc(C_swig_sizeof_closure(3)); \
    C_word *closure = a; \
    *(a++)=C_CLOSURE_TYPE|3; \
    *(a++)=(C_word)SWIG_Chicken_MultiResultBuild; \
    *(a++)=(C_word)continuation; \
    *(a++)=val; \
    continuation=(C_word)closure; \
  } }

#define SWIG_Chicken_FindCreateProxy(func,obj) \
  if (C_swig_is_swigpointer(obj)) { \
    swig_type_info *t = (swig_type_info *) C_block_item(obj, 1); \
    if (t && t->clientdata &&    ((swig_chicken_clientdata *)t->clientdata)->gc_proxy_create) { \
      func = CHICKEN_gc_root_ref( ((swig_chicken_clientdata *)t->clientdata)->gc_proxy_create); \
    } else { \
      func = C_SCHEME_FALSE; \
    } \
  } else { \
    func = C_SCHEME_FALSE; \
  }


enum {
  SWIG_BARF1_BAD_ARGUMENT_TYPE /* 1 arg */,
  SWIG_BARF1_ARGUMENT_NULL /* 1 arg */,
  SWIG_BARF1_CONTRACT_ASSERT /* 1 arg */,
};

typedef C_word (*swig_chicken_destructor)(C_word,C_word,C_word,C_word);
typedef struct swig_chicken_clientdata {
  void *gc_proxy_create;
  swig_chicken_destructor destroy;
} swig_chicken_clientdata;
  
static char *
SWIG_Chicken_MakeString(C_word str) {
  char *ret;
  size_t l;

  l = C_header_size(str);
  ret = (char *) SWIG_malloc( (l + 1) * sizeof(char));
  if (!ret) return NULL;

  memcpy(ret, C_c_string(str), l);
  ret[l] = '\0';
  return ret;
}

static C_word SWIG_Chicken_LookupSymbol(char *name, C_SYMBOL_TABLE *stable) {
  C_word *a = C_alloc(C_SIZEOF_STRING (strlen (name)));
  C_word n = C_string2(&a, name);
  C_word sym = C_find_symbol(n, stable);
  if (C_truep(sym)) {
    return C_symbol_value(sym);
  } else {
    return C_SCHEME_FALSE;
  }
}

/* Just a helper function.  Do not export it */
static void SWIG_Chicken_Panic (C_char *) C_noret;
static void SWIG_Chicken_Panic (C_char *msg)
{
  C_word *a = C_alloc (C_SIZEOF_STRING (strlen (msg)));
  C_word scmmsg = C_string2 (&a, msg);
  C_halt (scmmsg);
  exit (5); /* should never get here */
}

static void
SWIG_Chicken_Barf(int code, C_char *msg, ...) C_noret;
static void
SWIG_Chicken_Barf(int code, C_char *msg, ...)
{
  char *errorhook = C_text("\003syserror-hook");
  C_word *a = C_alloc (C_SIZEOF_STRING (strlen (errorhook)));
  C_word err = C_intern2 (&a, errorhook);
  int c = -1;
  int i, barfval;
  va_list v;

  
  C_temporary_stack = C_temporary_stack_bottom;
  err = C_block_item(err, 0);

  if(C_immediatep (err))
    SWIG_Chicken_Panic (C_text ("`##sys#error-hook' is not defined"));

  switch (code) {
  case SWIG_BARF1_BAD_ARGUMENT_TYPE:
    barfval = C_BAD_ARGUMENT_TYPE_ERROR;
    c = 1;
    break;
  case SWIG_BARF1_ARGUMENT_NULL:
    barfval = C_BAD_ARGUMENT_TYPE_ERROR;
    c = 1;
    break;
  case SWIG_BARF1_CONTRACT_ASSERT:
    barfval = C_BAD_ARGUMENT_TYPE_ERROR;
    c = 1;
    break;
  default:
    SWIG_Chicken_Panic (C_text (msg));
  };

  if(c > 0 && !C_immediatep (err)) {
    C_save (C_fix (barfval));

    i = c;
    if (i) {
      C_word *b = C_alloc (C_SIZEOF_STRING (strlen (msg)));
      C_word scmmsg = C_string2 (&b, msg);
      C_save (scmmsg);
      i--;
    }

    va_start (v, msg);

    while(i--)
      C_save (va_arg (v, C_word));

    va_end (v);
    C_do_apply (c + 1, err, 
		C_SCHEME_UNDEFINED);  /* <- no continuation is passed:
					 '##sys#error-hook' may not
					 return! */
  }
  else if (msg) {
    SWIG_Chicken_Panic (msg);
  }
  else {
    SWIG_Chicken_Panic (C_text ("unspecified panic"));
  }
}

static void SWIG_Chicken_ThrowException(C_word value) C_noret;
static void SWIG_Chicken_ThrowException(C_word value)
{
  char *aborthook = C_text("\003sysabort");
  C_word *a = C_alloc(C_SIZEOF_STRING(strlen(aborthook)));
  C_word abort = C_intern2(&a, aborthook);

  abort = C_block_item(abort, 0);
  if (C_immediatep(abort))
    SWIG_Chicken_Panic(C_text("`##sys#abort' is not defined"));

  C_save(value);
  C_do_apply(1, abort, C_SCHEME_UNDEFINED);
}

static void
SWIG_Chicken_Finalizer(C_word argc, C_word closure, C_word continuation, C_word s)
{
  swig_type_info *type;
  swig_chicken_clientdata *cdata;

  if (argc == 3 && s != C_SCHEME_FALSE && C_swig_is_swigpointer(s)) {
    type = (swig_type_info *) C_block_item(s, 1);
    if (type) {
      cdata = (swig_chicken_clientdata *) type->clientdata;
      if (cdata && cdata->destroy) {
	/* this will not return, but will continue correctly */
        cdata->destroy(3,closure,continuation,s);
      }
    }
  }
  C_kontinue(continuation, C_SCHEME_UNDEFINED);
}
static C_word finalizer_obj[2] = {(C_word) (C_CLOSURE_TYPE|1), (C_word) SWIG_Chicken_Finalizer};

static C_word
SWIG_Chicken_NewPointerObj(void *ptr, swig_type_info *type, int owner, C_word **data)
{
  swig_chicken_clientdata *cdata = (swig_chicken_clientdata *) type->clientdata;

  if (ptr == NULL)
    return C_SCHEME_FALSE;
  else {
    C_word cptr = C_swigmpointer(data, ptr, type);
    /* add finalizer to object */
    #ifndef SWIG_CHICKEN_NO_COLLECTION
    if (owner)
      C_do_register_finalizer(cptr, (C_word) finalizer_obj);
    #endif

    return cptr;
  }
}

/* Return 0 if successful. */
static int
SWIG_Chicken_ConvertPtr(C_word s, void **result, swig_type_info *type, int flags)
{
  swig_cast_info *cast;
  swig_type_info *from;

  if (s == C_SCHEME_FALSE) {
    *result = NULL;
  } else if (C_swig_is_swigpointer(s)) {
    /* try and convert type */
    from = (swig_type_info *) C_block_item(s, 1);
    if (!from) return 1;
    if (type) {
      cast = SWIG_TypeCheckStruct(from, type);
      if (cast) {
        int newmemory = 0;
        *result = SWIG_TypeCast(cast, (void *) C_block_item(s, 0), &newmemory);
        assert(!newmemory); /* newmemory handling not yet implemented */
      } else {
        return 1;
      }
    } else {
      *result = (void *) C_block_item(s, 0);
    }

    /* check if we are disowning this object */
    if (flags & SWIG_POINTER_DISOWN) {
      C_do_unregister_finalizer(s);
    }
  } else {
    return 1;
  }

  return 0;
}

static SWIGINLINE void *
SWIG_Chicken_MustGetPtr (C_word s, swig_type_info *type, int argnum, int flags)
{
  void *result;
  char err_msg[256];
  if (SWIG_Chicken_ConvertPtr(s, &result, type, flags)) {
    /* type mismatch */
    snprintf(err_msg, sizeof(err_msg), "Type error in argument #%i: expected %s", argnum, (type->str ? type->str : type->name));
    SWIG_Chicken_Barf(SWIG_BARF1_BAD_ARGUMENT_TYPE, err_msg);
  }
  return result;
}

static char *chicken_runtimevar_name = "type_pointer" SWIG_TYPE_TABLE_NAME;

static swig_module_info *
SWIG_Chicken_GetModule() {
    swig_module_info *ret = 0;
    C_word sym;

    /* lookup the type pointer... it is stored in it's own symbol table */
    C_SYMBOL_TABLE *stable = C_find_symbol_table("swig_runtime_data" SWIG_RUNTIME_VERSION);
    if (stable != NULL) {
      sym = SWIG_Chicken_LookupSymbol(chicken_runtimevar_name, stable);
      if (C_truep(sym) && C_swig_is_ptr(sym)) {
        ret = (swig_module_info *) C_block_item(sym, 0);
      }
    }

    return ret;
}

static void
SWIG_Chicken_SetModule(swig_module_info *module) {
    C_word *a;
    C_SYMBOL_TABLE *stable;
    C_word sym;
    C_word pointer;
    static C_word *space = 0;
    
    /* type pointer is stored in it's own symbol table */
    stable = C_find_symbol_table("swig_runtime_data" SWIG_RUNTIME_VERSION);
    if (stable == NULL) {
      stable = C_new_symbol_table("swig_runtime_data" SWIG_RUNTIME_VERSION, 16);
    }

    if (!space) {
      space = (C_word *) C_malloc((C_SIZEOF_POINTER + C_SIZEOF_INTERNED_SYMBOL(C_strlen(chicken_runtimevar_name))) * sizeof(C_word));
    }
    a = space;
    pointer = C_mpointer(&a, (void *) module);
    sym = C_intern_in(&a, C_strlen(chicken_runtimevar_name), chicken_runtimevar_name, stable);
    C_set_block_item(sym, 0, pointer);
}

static C_word SWIG_Chicken_MultiResultBuild(C_word num, C_word closure, C_word lst) {
  C_word cont = C_block_item(closure,1);
  C_word obj = C_block_item(closure,2);
  C_word func;

  SWIG_Chicken_FindCreateProxy(func,obj);

  if (C_swig_is_closurep(func)) {
    ((C_proc4)(void *)C_block_item(func, 0))(4,func,cont,obj,lst);
  } else {
    C_word *a = C_alloc(C_SIZEOF_PAIR);
    C_kontinue(cont,C_pair(&a,obj,lst));
  }
  return C_SCHEME_UNDEFINED; /* never reached */
}

static C_word SWIG_Chicken_ApplyResults(C_word num, C_word closure, C_word result) {
  C_apply_values(3,C_SCHEME_UNDEFINED,C_block_item(closure,1),result);
  return C_SCHEME_UNDEFINED; /* never reached */
}

#ifdef __cplusplus
}
#endif
