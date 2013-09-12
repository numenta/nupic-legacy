/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * luaruntime.swg
 *
 * all the runtime code for .
 * ----------------------------------------------------------------------------- */

%runtime "swigrun.swg";         /* Common C API type-checking code */
%runtime "luarun.swg";          /* Lua runtime stuff */

%insert(initbeforefunc) "swiginit.swg"

%insert(initbeforefunc) %{

/* Forward declaration of where the user's %init{} gets inserted */
void SWIG_init_user(lua_State* L );
    
#ifdef __cplusplus
extern "C" {
#endif
/* this is the initialization function
  added at the very end of the code
  the function is always called SWIG_init, but an eariler #define will rename it
*/
SWIGEXPORT int SWIG_init(lua_State* L)
{
  int i;
  /* start with global table */
  lua_pushvalue(L,LUA_GLOBALSINDEX);
  /* SWIG's internal initalisation */
  SWIG_InitializeModule((void*)L);
  SWIG_PropagateClientData();
  /* add a global fn */
  SWIG_Lua_add_function(L,"swig_type",SWIG_Lua_type);
  SWIG_Lua_add_function(L,"swig_equals",SWIG_Lua_equal);
  /* begin the module (its a table with the same name as the module) */
  SWIG_Lua_module_begin(L,SWIG_name);
  /* add commands/functions */
  for (i = 0; swig_commands[i].name; i++){
    SWIG_Lua_module_add_function(L,swig_commands[i].name,swig_commands[i].func);
  }
  /* add variables */
  for (i = 0; swig_variables[i].name; i++){
    SWIG_Lua_module_add_variable(L,swig_variables[i].name,swig_variables[i].get,swig_variables[i].set);
  }
  /* set up base class pointers (the hierachy) */
  for (i = 0; swig_types[i]; i++){
    if (swig_types[i]->clientdata){
      SWIG_Lua_init_base_class(L,(swig_lua_class*)(swig_types[i]->clientdata));
    }
  }
  /* additional registration structs & classes in lua */
  for (i = 0; swig_types[i]; i++){
    if (swig_types[i]->clientdata){
      SWIG_Lua_class_register(L,(swig_lua_class*)(swig_types[i]->clientdata));
    }
  }
  /* constants */
  SWIG_Lua_InstallConstants(L,swig_constants);
  /* invoke user-specific initialization */
  SWIG_init_user(L);
  /* end module */
  lua_pop(L,1);  /* tidy stack (remove module table)*/
  lua_pop(L,1);  /* tidy stack (remove global table)*/
  return 1;
}

#ifdef __cplusplus
}
#endif

%}

/* Note: the initialization function is closed after all code is generated */

