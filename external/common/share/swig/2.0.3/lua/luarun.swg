/* -----------------------------------------------------------------------------
 * luarun.swg
 *
 * This file contains the runtime support for Lua modules
 * and includes code for managing global variables and pointer
 * type checking.
 * ----------------------------------------------------------------------------- */

#ifdef __cplusplus
extern "C" {
#endif

#include "lua.h"
#include "lauxlib.h"
#include <stdlib.h>  /* for malloc */
#include <assert.h>  /* for a few sanity tests */

/* -----------------------------------------------------------------------------
 * global swig types
 * ----------------------------------------------------------------------------- */
/* Constant table */
#define SWIG_LUA_INT     1
#define SWIG_LUA_FLOAT   2
#define SWIG_LUA_STRING  3
#define SWIG_LUA_POINTER 4
#define SWIG_LUA_BINARY  5
#define SWIG_LUA_CHAR    6

/* Structure for variable linking table */
typedef struct {
  const char *name;
  lua_CFunction get;
  lua_CFunction set;
} swig_lua_var_info;

/* Constant information structure */
typedef struct {
    int type;
    char *name;
    long lvalue;
    double dvalue;
    void   *pvalue;
    swig_type_info **ptype;
} swig_lua_const_info;

typedef struct {
  const char     *name;
  lua_CFunction   method;
} swig_lua_method;

typedef struct {
  const char     *name;
  lua_CFunction   getmethod;
  lua_CFunction   setmethod;
} swig_lua_attribute;

typedef struct swig_lua_class {
  const char    *name;
  swig_type_info   **type;
  lua_CFunction  constructor;
  void    (*destructor)(void *);
  swig_lua_method   *methods;
  swig_lua_attribute     *attributes;
  struct swig_lua_class **bases;
  const char **base_names;
} swig_lua_class;

/* this is the struct for wrappering all pointers in SwigLua
*/
typedef struct {
  swig_type_info   *type;
  int     own;  /* 1 if owned & must be destroyed */
  void        *ptr;
} swig_lua_userdata;

/* this is the struct for wrapping arbitary packed binary data
(currently it is only used for member function pointers)
the data ordering is similar to swig_lua_userdata, but it is currently not possible
to tell the two structures apart within SWIG, other than by looking at the type
*/
typedef struct {
  swig_type_info   *type;
  int     own;  /* 1 if owned & must be destroyed */
  char data[1];       /* arbitary amount of data */    
} swig_lua_rawdata;

/* Common SWIG API */
#define SWIG_NewPointerObj(L, ptr, type, owner)       SWIG_Lua_NewPointerObj(L, (void *)ptr, type, owner)
#define SWIG_ConvertPtr(L,idx, ptr, type, flags)    SWIG_Lua_ConvertPtr(L,idx,ptr,type,flags)
#define SWIG_MustGetPtr(L,idx, type,flags, argnum,fnname)  SWIG_Lua_MustGetPtr(L,idx, type,flags, argnum,fnname)
/* for C++ member pointers, ie, member methods */
#define SWIG_ConvertMember(L, idx, ptr, sz, ty)       SWIG_Lua_ConvertPacked(L, idx, ptr, sz, ty)
#define SWIG_NewMemberObj(L, ptr, sz, type)      SWIG_Lua_NewPackedObj(L, ptr, sz, type)

/* Runtime API */
#define SWIG_GetModule(clientdata) SWIG_Lua_GetModule((lua_State*)(clientdata))
#define SWIG_SetModule(clientdata, pointer) SWIG_Lua_SetModule((lua_State*) (clientdata), pointer)
#define SWIG_MODULE_CLIENTDATA_TYPE lua_State*

/* Contract support */
#define SWIG_contract_assert(expr, msg)  \
  if (!(expr)) { lua_pushstring(L, (char *) msg); goto fail; } else

/* helper #defines */
#define SWIG_fail {goto fail;}
#define SWIG_fail_arg(func_name,argnum,type) \
  {lua_pushfstring(L,"Error in %s (arg %d), expected '%s' got '%s'",\
  func_name,argnum,type,SWIG_Lua_typename(L,argnum));\
  goto fail;}
#define SWIG_fail_ptr(func_name,argnum,type) \
  SWIG_fail_arg(func_name,argnum,(type && type->str)?type->str:"void*")
#define SWIG_check_num_args(func_name,a,b) \
  if (lua_gettop(L)<a || lua_gettop(L)>b) \
  {lua_pushfstring(L,"Error in %s expected %d..%d args, got %d",func_name,a,b,lua_gettop(L));\
  goto fail;}


#define SWIG_Lua_get_table(L,n) \
  (lua_pushstring(L, n), lua_rawget(L,-2))

#define SWIG_Lua_add_function(L,n,f) \
  (lua_pushstring(L, n), \
      lua_pushcfunction(L, f), \
      lua_rawset(L,-3))

/* special helper for allowing 'nil' for usertypes */
#define SWIG_isptrtype(L,I) (lua_isuserdata(L,I) || lua_isnil(L,I))

#ifdef __cplusplus
/* Special helper for member function pointers 
it gets the address, casts it, then dereferences it */
//#define SWIG_mem_fn_as_voidptr(a)  (*((char**)&(a)))
#endif

/* storing/access of swig_module_info */
SWIGRUNTIME swig_module_info *
SWIG_Lua_GetModule(lua_State* L) {
  swig_module_info *ret = 0;
  lua_pushstring(L,"swig_runtime_data_type_pointer" SWIG_RUNTIME_VERSION SWIG_TYPE_TABLE_NAME);
  lua_rawget(L,LUA_REGISTRYINDEX);
  if (lua_islightuserdata(L,-1))
    ret=(swig_module_info*)lua_touserdata(L,-1);
  lua_pop(L,1);  /* tidy */
  return ret;
}

SWIGRUNTIME void
SWIG_Lua_SetModule(lua_State* L, swig_module_info *module) {
  /* add this all into the Lua registry: */
  lua_pushstring(L,"swig_runtime_data_type_pointer" SWIG_RUNTIME_VERSION SWIG_TYPE_TABLE_NAME);
  lua_pushlightuserdata(L,(void*)module);
  lua_rawset(L,LUA_REGISTRYINDEX);
}

/* -----------------------------------------------------------------------------
 * global variable support code: modules
 * ----------------------------------------------------------------------------- */

/* this function is called when trying to set an immutable.
default value is to print an error.
This can removed with a compile flag SWIGLUA_IGNORE_SET_IMMUTABLE */
SWIGINTERN int SWIG_Lua_set_immutable(lua_State* L)
{
/*  there should be 1 param passed in: the new value */
#ifndef SWIGLUA_IGNORE_SET_IMMUTABLE
  lua_pop(L,1);  /* remove it */
  lua_pushstring(L,"This variable is immutable");
  lua_error(L);
#endif
    return 0;   /* should not return anything */
}

/* the module.get method used for getting linked data */
SWIGINTERN int SWIG_Lua_module_get(lua_State* L)
{
/*  there should be 2 params passed in
  (1) table (not the meta table)
  (2) string name of the attribute
  printf("SWIG_Lua_module_get %p(%s) '%s'\n",
   lua_topointer(L,1),lua_typename(L,lua_type(L,1)),
   lua_tostring(L,2));
*/
  /* get the metatable */
  assert(lua_istable(L,1));  /* just in case */
  lua_getmetatable(L,1);  /* get the metatable */
  assert(lua_istable(L,-1));  /* just in case */
  SWIG_Lua_get_table(L,".get");  /* get the .get table */
  lua_remove(L,3);  /* remove metatable */
  if (lua_istable(L,-1))
  {
    /* look for the key in the .get table */
    lua_pushvalue(L,2);  /* key */
    lua_rawget(L,-2);
    lua_remove(L,3);  /* remove .get */
    if (lua_iscfunction(L,-1))
    {  /* found it so call the fn & return its value */
      lua_call(L,0,1);
      return 1;
    }
    lua_pop(L,1);  /* remove the top */
  }
  lua_pop(L,1);  /* remove the .get */
  lua_pushnil(L);  /* return a nil */
    return 1;
}

/* the module.set method used for setting linked data */
SWIGINTERN int SWIG_Lua_module_set(lua_State* L)
{
/*  there should be 3 params passed in
  (1) table (not the meta table)
  (2) string name of the attribute
  (3) any for the new value
*/
  /* get the metatable */
  assert(lua_istable(L,1));  /* just in case */
  lua_getmetatable(L,1);  /* get the metatable */
  assert(lua_istable(L,-1));  /* just in case */
  SWIG_Lua_get_table(L,".set");  /* get the .set table */
  lua_remove(L,4);  /* remove metatable */
  if (lua_istable(L,-1))
  {
    /* look for the key in the .set table */
    lua_pushvalue(L,2);  /* key */
    lua_rawget(L,-2);
    lua_remove(L,4);  /* remove .set */
    if (lua_iscfunction(L,-1))
    {  /* found it so call the fn & return its value */
      lua_pushvalue(L,3);  /* value */
      lua_call(L,1,0);
      return 0;
    }
  }
  lua_settop(L,3);  /* reset back to start */
  /* we now have the table, key & new value, so just set directly */
  lua_rawset(L,1);  /* add direct */
  return 0;
}

/* registering a module in lua */
SWIGINTERN void  SWIG_Lua_module_begin(lua_State* L,const char* name)
{
  assert(lua_istable(L,-1));  /* just in case */
  lua_pushstring(L,name);
  lua_newtable(L);   /* the table */
  /* add meta table */
  lua_newtable(L);    /* the meta table */
  SWIG_Lua_add_function(L,"__index",SWIG_Lua_module_get);
  SWIG_Lua_add_function(L,"__newindex",SWIG_Lua_module_set);
  lua_pushstring(L,".get");
  lua_newtable(L);    /* the .get table */
  lua_rawset(L,-3);  /* add .get into metatable */
  lua_pushstring(L,".set");
  lua_newtable(L);    /* the .set table */
  lua_rawset(L,-3);  /* add .set into metatable */
  lua_setmetatable(L,-2);  /* sets meta table in module */
  lua_rawset(L,-3);        /* add module into parent */
  SWIG_Lua_get_table(L,name);   /* get the table back out */
}

/* ending the register */
SWIGINTERN void  SWIG_Lua_module_end(lua_State* L)
{
  lua_pop(L,1);       /* tidy stack (remove module) */
}

/* adding a linked variable to the module */
SWIGINTERN void SWIG_Lua_module_add_variable(lua_State* L,const char* name,lua_CFunction getFn,lua_CFunction setFn)
{
  assert(lua_istable(L,-1));  /* just in case */
  lua_getmetatable(L,-1);  /* get the metatable */
  assert(lua_istable(L,-1));  /* just in case */
  SWIG_Lua_get_table(L,".get"); /* find the .get table */
  assert(lua_istable(L,-1));  /* should be a table: */
  SWIG_Lua_add_function(L,name,getFn);
  lua_pop(L,1);       /* tidy stack (remove table) */
  if (setFn)  /* if there is a set fn */
  {
    SWIG_Lua_get_table(L,".set"); /* find the .set table */
    assert(lua_istable(L,-1));  /* should be a table: */
    SWIG_Lua_add_function(L,name,setFn);
    lua_pop(L,1);       /* tidy stack (remove table) */
  }
  lua_pop(L,1);       /* tidy stack (remove meta) */
}

/* adding a function module */
SWIGINTERN void  SWIG_Lua_module_add_function(lua_State* L,const char* name,lua_CFunction fn)
{
  SWIG_Lua_add_function(L,name,fn);
}

/* -----------------------------------------------------------------------------
 * global variable support code: classes
 * ----------------------------------------------------------------------------- */

/* the class.get method, performs the lookup of class attributes */
SWIGINTERN int  SWIG_Lua_class_get(lua_State* L)
{
/*  there should be 2 params passed in
  (1) userdata (not the meta table)
  (2) string name of the attribute
*/
  assert(lua_isuserdata(L,-2));  /* just in case */
  lua_getmetatable(L,-2);    /* get the meta table */
  assert(lua_istable(L,-1));  /* just in case */
  SWIG_Lua_get_table(L,".get"); /* find the .get table */
  assert(lua_istable(L,-1));  /* just in case */
  /* look for the key in the .get table */
  lua_pushvalue(L,2);  /* key */
  lua_rawget(L,-2);
  lua_remove(L,-2); /* stack tidy, remove .get table */
  if (lua_iscfunction(L,-1))
  {  /* found it so call the fn & return its value */
    lua_pushvalue(L,1);  /* the userdata */
    lua_call(L,1,1);  /* 1 value in (userdata),1 out (result) */
    lua_remove(L,-2); /* stack tidy, remove metatable */
    return 1;
  }
  lua_pop(L,1);  /* remove whatever was there */
  /* ok, so try the .fn table */
  SWIG_Lua_get_table(L,".fn"); /* find the .get table */
  assert(lua_istable(L,-1));  /* just in case */
  lua_pushvalue(L,2);  /* key */
  lua_rawget(L,-2);  /* look for the fn */
  lua_remove(L,-2); /* stack tidy, remove .fn table */
  if (lua_isfunction(L,-1)) /* note: if its a C function or lua function */
  {  /* found it so return the fn & let lua call it */
    lua_remove(L,-2); /* stack tidy, remove metatable */
    return 1;
  }
  lua_pop(L,1);  /* remove whatever was there */
  /* NEW: looks for the __getitem() fn
  this is a user provided get fn */
  SWIG_Lua_get_table(L,"__getitem"); /* find the __getitem fn */
  if (lua_iscfunction(L,-1))  /* if its there */
  {  /* found it so call the fn & return its value */
    lua_pushvalue(L,1);  /* the userdata */
    lua_pushvalue(L,2);  /* the parameter */
    lua_call(L,2,1);  /* 2 value in (userdata),1 out (result) */
    lua_remove(L,-2); /* stack tidy, remove metatable */
    return 1;
  }
  return 0;  /* sorry not known */
}

/* the class.set method, performs the lookup of class attributes */
SWIGINTERN int  SWIG_Lua_class_set(lua_State* L)
{
/*  there should be 3 params passed in
  (1) table (not the meta table)
  (2) string name of the attribute
  (3) any for the new value
printf("SWIG_Lua_class_set %p(%s) '%s' %p(%s)\n",
      lua_topointer(L,1),lua_typename(L,lua_type(L,1)),
      lua_tostring(L,2),
      lua_topointer(L,3),lua_typename(L,lua_type(L,3)));*/

  assert(lua_isuserdata(L,1));  /* just in case */
  lua_getmetatable(L,1);    /* get the meta table */
  assert(lua_istable(L,-1));  /* just in case */

  SWIG_Lua_get_table(L,".set"); /* find the .set table */
  if (lua_istable(L,-1))
  {
    /* look for the key in the .set table */
    lua_pushvalue(L,2);  /* key */
    lua_rawget(L,-2);
    if (lua_iscfunction(L,-1))
    {  /* found it so call the fn & return its value */
      lua_pushvalue(L,1);  /* userdata */
      lua_pushvalue(L,3);  /* value */
      lua_call(L,2,0);
      return 0;
    }
    lua_pop(L,1);  /* remove the value */
  }
  lua_pop(L,1);  /* remove the value .set table */
  /* NEW: looks for the __setitem() fn
  this is a user provided set fn */
  SWIG_Lua_get_table(L,"__setitem"); /* find the fn */
  if (lua_iscfunction(L,-1))  /* if its there */
  {  /* found it so call the fn & return its value */
    lua_pushvalue(L,1);  /* the userdata */
    lua_pushvalue(L,2);  /* the parameter */
    lua_pushvalue(L,3);  /* the value */
    lua_call(L,3,0);  /* 3 values in ,0 out */
    lua_remove(L,-2); /* stack tidy, remove metatable */
    return 1;
  }
  return 0;
}

/* the class.destruct method called by the interpreter */
SWIGINTERN int  SWIG_Lua_class_destruct(lua_State* L)
{
/*  there should be 1 params passed in
  (1) userdata (not the meta table) */
  swig_lua_userdata* usr;
  swig_lua_class* clss;
  assert(lua_isuserdata(L,-1));  /* just in case */
  usr=(swig_lua_userdata*)lua_touserdata(L,-1);  /* get it */
  /* if must be destroyed & has a destructor */
  if (usr->own) /* if must be destroyed */
  {
    clss=(swig_lua_class*)usr->type->clientdata;  /* get the class */
    if (clss && clss->destructor)  /* there is a destroy fn */
    {
      clss->destructor(usr->ptr);  /* bye bye */
    }
  }
  return 0;
}

/* gets the swig class registry (or creates it) */
SWIGINTERN void  SWIG_Lua_get_class_registry(lua_State* L)
{
  /* add this all into the swig registry: */
  lua_pushstring(L,"SWIG");
  lua_rawget(L,LUA_REGISTRYINDEX);  /* get the registry */
  if (!lua_istable(L,-1))  /* not there */
  {  /* must be first time, so add it */
    lua_pop(L,1);  /* remove the result */
    lua_pushstring(L,"SWIG");
    lua_newtable(L);
    lua_rawset(L,LUA_REGISTRYINDEX);
    /* then get it */
    lua_pushstring(L,"SWIG");
    lua_rawget(L,LUA_REGISTRYINDEX);
  }
}

/* helper fn to get the classes metatable from the register */
SWIGINTERN void  SWIG_Lua_get_class_metatable(lua_State* L,const char* cname)
{
  SWIG_Lua_get_class_registry(L);  /* get the registry */
  lua_pushstring(L,cname);  /* get the name */
  lua_rawget(L,-2);    /* get it */
  lua_remove(L,-2);    /* tidy up (remove registry) */
}

/* helper add a variable to a registered class */
SWIGINTERN void  SWIG_Lua_add_class_variable(lua_State* L,const char* name,lua_CFunction getFn,lua_CFunction setFn)
{
  assert(lua_istable(L,-1));  /* just in case */
  SWIG_Lua_get_table(L,".get"); /* find the .get table */
  assert(lua_istable(L,-1));  /* just in case */
  SWIG_Lua_add_function(L,name,getFn);
  lua_pop(L,1);       /* tidy stack (remove table) */
  if (setFn)
  {
    SWIG_Lua_get_table(L,".set"); /* find the .set table */
    assert(lua_istable(L,-1));  /* just in case */
    SWIG_Lua_add_function(L,name,setFn);
    lua_pop(L,1);       /* tidy stack (remove table) */
  }
}

/* helper to recursively add class details (attributes & operations) */
SWIGINTERN void  SWIG_Lua_add_class_details(lua_State* L,swig_lua_class* clss)
{
  int i;
  /* call all the base classes first: we can then override these later: */
  for(i=0;clss->bases[i];i++)
  {
    SWIG_Lua_add_class_details(L,clss->bases[i]);
  }
  /* add fns */
  for(i=0;clss->attributes[i].name;i++){
    SWIG_Lua_add_class_variable(L,clss->attributes[i].name,clss->attributes[i].getmethod,clss->attributes[i].setmethod);
  }
  /* add methods to the metatable */
  SWIG_Lua_get_table(L,".fn"); /* find the .fn table */
  assert(lua_istable(L,-1));  /* just in case */
  for(i=0;clss->methods[i].name;i++){
    SWIG_Lua_add_function(L,clss->methods[i].name,clss->methods[i].method);
  }
  lua_pop(L,1);       /* tidy stack (remove table) */
  /*   add operator overloads
    these look ANY method which start with "__" and assume they
    are operator overloads & add them to the metatable
    (this might mess up is someone defines a method __gc (the destructor)*/
  for(i=0;clss->methods[i].name;i++){
    if (clss->methods[i].name[0]=='_' && clss->methods[i].name[1]=='_'){
      SWIG_Lua_add_function(L,clss->methods[i].name,clss->methods[i].method);
    }
  }
}

/* set up the base classes pointers.
Each class structure has a list of pointers to the base class structures.
This function fills them.
It cannot be done at compile time, as this will not work with hireachies
spread over more than one swig file. 
Therefore it must be done at runtime, querying the SWIG type system.
*/
SWIGINTERN void SWIG_Lua_init_base_class(lua_State* L,swig_lua_class* clss)
{
  int i=0;
  swig_module_info* module=SWIG_GetModule(L);
  for(i=0;clss->base_names[i];i++)
  {
    if (clss->bases[i]==0) /* not found yet */
    {
      /* lookup and cache the base class */
      swig_type_info *info = SWIG_TypeQueryModule(module,module,clss->base_names[i]);
      if (info) clss->bases[i] = (swig_lua_class *) info->clientdata;
    }
  }	
}

/* performs the entire class registration process */
SWIGINTERN void  SWIG_Lua_class_register(lua_State* L,swig_lua_class* clss)
{
  /*  add its constructor to module with the name of the class
  so you can do MyClass(...) as well as new_MyClass(...)
  BUT only if a constructor is defined
  (this overcomes the problem of pure virtual classes without constructors)*/
  if (clss->constructor)
    SWIG_Lua_add_function(L,clss->name,clss->constructor);

  SWIG_Lua_get_class_registry(L);  /* get the registry */
  lua_pushstring(L,clss->name);  /* get the name */
  lua_newtable(L);    /* create the metatable */
  /* add string of class name called ".type" */
  lua_pushstring(L,".type");
  lua_pushstring(L,clss->name);
  lua_rawset(L,-3);
  /* add a table called ".get" */
  lua_pushstring(L,".get");
  lua_newtable(L);
  lua_rawset(L,-3);
  /* add a table called ".set" */
  lua_pushstring(L,".set");
  lua_newtable(L);
  lua_rawset(L,-3);
  /* add a table called ".fn" */
  lua_pushstring(L,".fn");
  lua_newtable(L);
  lua_rawset(L,-3);
  /* add accessor fns for using the .get,.set&.fn */
  SWIG_Lua_add_function(L,"__index",SWIG_Lua_class_get);
  SWIG_Lua_add_function(L,"__newindex",SWIG_Lua_class_set);
  SWIG_Lua_add_function(L,"__gc",SWIG_Lua_class_destruct);
  /* add it */
  lua_rawset(L,-3);  /* metatable into registry */
  lua_pop(L,1);      /* tidy stack (remove registry) */

  SWIG_Lua_get_class_metatable(L,clss->name);
  SWIG_Lua_add_class_details(L,clss);  /* recursive adding of details (atts & ops) */
  lua_pop(L,1);      /* tidy stack (remove class metatable) */
}

/* -----------------------------------------------------------------------------
 * Class/structure conversion fns
 * ----------------------------------------------------------------------------- */

/* helper to add metatable to new lua object */
SWIGINTERN void _SWIG_Lua_AddMetatable(lua_State* L,swig_type_info *type)
{
  if (type->clientdata)  /* there is clientdata: so add the metatable */
  {
    SWIG_Lua_get_class_metatable(L,((swig_lua_class*)(type->clientdata))->name);
    if (lua_istable(L,-1))
    {
      lua_setmetatable(L,-2);
    }
    else
    {
      lua_pop(L,1);
    }
  }
}

/* pushes a new object into the lua stack */
SWIGRUNTIME void SWIG_Lua_NewPointerObj(lua_State* L,void* ptr,swig_type_info *type, int own)
{
  swig_lua_userdata* usr;
  if (!ptr){
    lua_pushnil(L);
    return;
  }
  usr=(swig_lua_userdata*)lua_newuserdata(L,sizeof(swig_lua_userdata));  /* get data */
  usr->ptr=ptr;  /* set the ptr */
  usr->type=type;
  usr->own=own;
  _SWIG_Lua_AddMetatable(L,type); /* add metatable */
}

/* takes a object from the lua stack & converts it into an object of the correct type
 (if possible) */
SWIGRUNTIME int  SWIG_Lua_ConvertPtr(lua_State* L,int index,void** ptr,swig_type_info *type,int flags)
{
  swig_lua_userdata* usr;
  swig_cast_info *cast;
  if (lua_isnil(L,index)){*ptr=0; return SWIG_OK;}    /* special case: lua nil => NULL pointer */
  usr=(swig_lua_userdata*)lua_touserdata(L,index);  /* get data */
  if (usr)
  {
    if (flags & SWIG_POINTER_DISOWN) /* must disown the object */
    {
        usr->own=0;
    }
    if (!type)            /* special cast void*, no casting fn */
    {
      *ptr=usr->ptr;
      return SWIG_OK; /* ok */
    }
    cast=SWIG_TypeCheckStruct(usr->type,type); /* performs normal type checking */
    if (cast)
    {
      int newmemory = 0;
      *ptr=SWIG_TypeCast(cast,usr->ptr,&newmemory);
      assert(!newmemory); /* newmemory handling not yet implemented */
      return SWIG_OK;  /* ok */
    }
  }
  return SWIG_ERROR;  /* error */
}

SWIGRUNTIME void* SWIG_Lua_MustGetPtr(lua_State* L,int index,swig_type_info *type,int flags,
       int argnum,const char* func_name){
  void* result;
  if (!SWIG_IsOK(SWIG_ConvertPtr(L,index,&result,type,flags))){
    lua_pushfstring(L,"Error in %s, expected a %s at argument number %d\n",
      func_name,(type && type->str)?type->str:"void*",argnum);
    lua_error(L);
  }
  return result;
}

/* pushes a packed userdata. user for member fn pointers only */
SWIGRUNTIME void SWIG_Lua_NewPackedObj(lua_State* L,void* ptr,size_t size,swig_type_info *type)
{
  swig_lua_rawdata* raw;
  assert(ptr); /* not acceptable to pass in a NULL value */
  raw=(swig_lua_rawdata*)lua_newuserdata(L,sizeof(swig_lua_rawdata)-1+size);  /* alloc data */
  raw->type=type;
  raw->own=0;
  memcpy(raw->data,ptr,size); /* copy the data */
  _SWIG_Lua_AddMetatable(L,type); /* add metatable */
}
    
/* converts a packed userdata. user for member fn pointers only */
SWIGRUNTIME int  SWIG_Lua_ConvertPacked(lua_State* L,int index,void* ptr,size_t size,swig_type_info *type)
{
  swig_lua_rawdata* raw;
  raw=(swig_lua_rawdata*)lua_touserdata(L,index);  /* get data */
  if (!raw) return SWIG_ERROR;  /* error */
  if (type==0 || type==raw->type) /* void* or identical type */
  {
    memcpy(ptr,raw->data,size); /* copy it */
    return SWIG_OK; /* ok */
  }
  return SWIG_ERROR;  /* error */
}

/* a function to get the typestring of a piece of data */
SWIGRUNTIME const char *SWIG_Lua_typename(lua_State *L, int tp)
{
  swig_lua_userdata* usr;
  if (lua_isuserdata(L,tp))
  {
    usr=(swig_lua_userdata*)lua_touserdata(L,tp);  /* get data */
    if (usr && usr->type && usr->type->str)
      return usr->type->str;
    return "userdata (unknown type)";
  }
  return lua_typename(L,lua_type(L,tp));
}

/* lua callable function to get the userdata's type */
SWIGRUNTIME int SWIG_Lua_type(lua_State* L)
{
  lua_pushstring(L,SWIG_Lua_typename(L,1));
  return 1;
}

/* lua callable function to compare userdata's value
the issue is that two userdata may point to the same thing
but to lua, they are different objects */
SWIGRUNTIME int SWIG_Lua_equal(lua_State* L)
{
  int result;
  swig_lua_userdata *usr1,*usr2;
  if (!lua_isuserdata(L,1) || !lua_isuserdata(L,2))  /* just in case */
    return 0;  /* nil reply */
  usr1=(swig_lua_userdata*)lua_touserdata(L,1);  /* get data */
  usr2=(swig_lua_userdata*)lua_touserdata(L,2);  /* get data */
  /*result=(usr1->ptr==usr2->ptr && usr1->type==usr2->type); only works if type is the same*/
  result=(usr1->ptr==usr2->ptr);
   lua_pushboolean(L,result);
  return 1;
}

/* -----------------------------------------------------------------------------
 * global variable support code: class/struct typemap functions
 * ----------------------------------------------------------------------------- */

/* Install Constants */
SWIGINTERN void
SWIG_Lua_InstallConstants(lua_State* L, swig_lua_const_info constants[]) {
  int i;
  for (i = 0; constants[i].type; i++) {
    switch(constants[i].type) {
    case SWIG_LUA_INT:
      lua_pushstring(L,constants[i].name);
      lua_pushnumber(L,(lua_Number)constants[i].lvalue);
      lua_rawset(L,-3);
      break;
    case SWIG_LUA_FLOAT:
      lua_pushstring(L,constants[i].name);
      lua_pushnumber(L,(lua_Number)constants[i].dvalue);
      lua_rawset(L,-3);
      break;
    case SWIG_LUA_CHAR:
      lua_pushstring(L,constants[i].name);
      lua_pushfstring(L,"%c",(char)constants[i].lvalue);
      lua_rawset(L,-3);
      break;
    case SWIG_LUA_STRING:
      lua_pushstring(L,constants[i].name);
      lua_pushstring(L,(char *) constants[i].pvalue);
      lua_rawset(L,-3);
      break;
    case SWIG_LUA_POINTER:
      lua_pushstring(L,constants[i].name);
      SWIG_NewPointerObj(L,constants[i].pvalue, *(constants[i]).ptype,0);
      lua_rawset(L,-3);
      break;
    case SWIG_LUA_BINARY:
      lua_pushstring(L,constants[i].name);
      SWIG_NewMemberObj(L,constants[i].pvalue,constants[i].lvalue,*(constants[i]).ptype);
      lua_rawset(L,-3);
      break;
    default:
      break;
    }
  }
}

/* -----------------------------------------------------------------------------
 * executing lua code from within the wrapper
 * ----------------------------------------------------------------------------- */

#ifndef SWIG_DOSTRING_FAIL /* Allows redefining of error function */
#define SWIG_DOSTRING_FAIL(S) fprintf(stderr,"%s\n",S)
#endif
/* Executes a C string in Lua a really simple way of calling lua from C
Unfortunately lua keeps changing its API's, so we need a conditional compile
In lua 5.0.X its lua_dostring()
In lua 5.1.X its luaL_dostring()
*/
SWIGINTERN int 
SWIG_Lua_dostring(lua_State *L, const char* str) {
  int ok,top;
  if (str==0 || str[0]==0) return 0; /* nothing to do */
  top=lua_gettop(L); /* save stack */
#if (defined(LUA_VERSION_NUM) && (LUA_VERSION_NUM>=501))
  ok=luaL_dostring(L,str);	/* looks like this is lua 5.1.X or later, good */
#else
  ok=lua_dostring(L,str);	/* might be lua 5.0.x, using lua_dostring */
#endif
  if (ok!=0) {
    SWIG_DOSTRING_FAIL(lua_tostring(L,-1));
  }
  lua_settop(L,top); /* restore the stack */
  return ok;
}    

#ifdef __cplusplus
}
#endif

/* ------------------------------ end luarun.swg  ------------------------------ */
