/* -----------------------------------------------------------------------------
 * pikerun.swg
 *
 * This file contains the runtime support for Pike modules
 * and includes code for managing global variables and pointer
 * type checking.
 * ----------------------------------------------------------------------------- */

#ifdef __cplusplus
extern "C" {
#endif
#include "object.h"
#include "program.h"
#ifdef __cplusplus
}
#endif

/* Stores information about a wrapped object */
typedef struct swig_object_wrapper {
    void *self;
    swig_type_info *type;
} swig_object_wrapper;

#ifdef THIS
#undef THIS
#endif
#define THIS (((swig_object_wrapper *) Pike_fp->current_storage)->self)

#define SWIG_ConvertPtr SWIG_Pike_ConvertPtr
#define SWIG_NewPointerObj SWIG_Pike_NewPointerObj
#define SWIG_GetModule(clientdata) SWIG_Pike_GetModule()
#define SWIG_SetModule(clientdata, pointer) SWIG_Pike_SetModule(pointer)

/* These need to be filled in before type sharing between modules will work */
static swig_module_info *SWIG_Pike_GetModule() {
  return 0;
}

static void SWIG_Pike_SetModule(swig_module_info *pointer) {

}

/* Convert a pointer value */
static int
SWIG_Pike_ConvertPtr(struct object *obj, void **ptr, swig_type_info *ty, int flags) {
    struct program *pr;
    swig_cast_info *tc;
    swig_object_wrapper *obj_wrapper;
    
    if (ty) {
        pr = (struct program *) ty->clientdata;
        obj_wrapper = (swig_object_wrapper *) get_storage(obj, pr);
        if (obj_wrapper && obj_wrapper->type) {
            tc = SWIG_TypeCheckStruct(obj_wrapper->type, ty);
            if (tc) {
                int newmemory = 0;
                *ptr = SWIG_TypeCast(tc, obj_wrapper->self, &newmemory);
                assert(!newmemory); /* newmemory handling not yet implemented */
                return 0;
            }
        }
    }
    return -1;
}

/* Create a new pointer object */
static struct object *
SWIG_Pike_NewPointerObj(void *ptr, swig_type_info *type, int own) {
    return 0;
}
