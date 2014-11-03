/* -----------------------------------------------------------------------------
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
  the function is always called SWIG_init, but an earlier #define will rename it
*/
#if ((SWIG_LUA_TARGET == SWIG_LUA_FLAVOR_ELUA) || (SWIG_LUA_TARGET == SWIG_LUA_FLAVOR_ELUAC))
LUALIB_API int SWIG_init(lua_State* L)
#else
SWIGEXPORT int SWIG_init(lua_State* L) /* default Lua action */
#endif
{
#if (SWIG_LUA_TARGET != SWIG_LUA_FLAVOR_ELUAC) /* valid for both Lua and eLua */
  int i;
  /* start with global table */
  lua_pushglobaltable (L);
  /* SWIG's internal initalisation */
  SWIG_InitializeModule((void*)L);
  SWIG_PropagateClientData();
#endif

#if ((SWIG_LUA_TARGET != SWIG_LUA_FLAVOR_ELUA) && (SWIG_LUA_TARGET != SWIG_LUA_FLAVOR_ELUAC))
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
#endif

#if (SWIG_LUA_TARGET != SWIG_LUA_FLAVOR_ELUAC)
  /* set up base class pointers (the hierarchy) */
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
#endif

#if ((SWIG_LUA_TARGET != SWIG_LUA_FLAVOR_ELUA) && (SWIG_LUA_TARGET != SWIG_LUA_FLAVOR_ELUAC))
  /* constants */
  SWIG_Lua_InstallConstants(L,swig_constants);
#endif

#if (SWIG_LUA_TARGET != SWIG_LUA_FLAVOR_ELUAC)
  /* invoke user-specific initialization */
  SWIG_init_user(L);
  /* end module */
  /* Note: We do not clean up the stack here (Lua will do this for us). At this
     point, we have the globals table and out module table on the stack. Returning
     one value makes the module table the result of the require command. */
  return 1;
#else
  return 0;
#endif
}

#ifdef __cplusplus
}
#endif

%}

/* Note: the initialization function is closed after all code is generated */

