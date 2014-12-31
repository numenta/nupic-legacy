%insert(init) %{

#include <assert.h>

SWIGRUNTIME void
SWIG_V8_SetModule(void *, swig_module_info *swig_module) {
  v8::Local<v8::Object> global_obj = v8::Context::GetCurrent()->Global();
  v8::Local<v8::External> mod = v8::External::New(swig_module);
  assert(!mod.IsEmpty());
  global_obj->SetHiddenValue(v8::String::New("swig_module_info_data"), mod);
}

SWIGRUNTIME swig_module_info *
SWIG_V8_GetModule(void *) {
  v8::Local<v8::Object> global_obj = v8::Context::GetCurrent()->Global();
  v8::Local<v8::Value> moduleinfo = global_obj->GetHiddenValue(v8::String::New("swig_module_info_data"));

  if (moduleinfo.IsEmpty())
  {
    // It's not yet loaded
    return 0;
  }

  v8::Local<v8::External> moduleinfo_extern = v8::Local<v8::External>::Cast(moduleinfo);

  if (moduleinfo_extern.IsEmpty())
  {
    // Something's not right
    return 0;
  }

  void *ptr = moduleinfo_extern->Value();
  assert(ptr);
  swig_module_info *retptr = static_cast<swig_module_info *>(ptr);
  assert(retptr);
  return retptr;
}

#define SWIG_GetModule(clientdata)                SWIG_V8_GetModule(clientdata)
#define SWIG_SetModule(clientdata, pointer)       SWIG_V8_SetModule(clientdata, pointer)

%}

%insert(init) "swiginit.swg"

// Open the initializer function definition here

%fragment ("js_initializer_define", "templates") %{
#define SWIGV8_INIT $jsname_initialize
%}

%insert(init) %{
// Note: 'extern "C"'' disables name mangling which makes it easier to load the symbol manually
// TODO: is it ok to do that?
extern "C"
#if (NODE_MODULE_VERSION < 0x000C)
void SWIGV8_INIT (v8::Handle<v8::Object> exports)
#else
void SWIGV8_INIT (v8::Handle<v8::Object> exports, v8::Handle<v8::Object> /*module*/)
#endif
{
  SWIG_InitializeModule(static_cast<void *>(&exports));

  v8::HandleScope scope;
  v8::Handle<v8::Object> exports_obj = exports;
%}


/* -----------------------------------------------------------------------------
 * js_initializer:  template for the module initializer function
 *   - $jsname:                   module name
 *   - $jsv8nspaces:              part with code creating namespace objects
 *   - $jsv8classtemplates:       part with code creating class templates
 *   - $jsv8wrappers:             part with code that registers wrapper functions
 *   - $jsv8inheritance:          part with inherit statements
 *   - $jsv8classinstances:       part with code creating class objects
 *   - $jsv8staticwrappers:       part with code adding static functions to class objects
 *   - $jsv8registerclasses:      part with code that registers class objects in namespaces
 *   - $jsv8registernspaces:      part with code that registers namespaces in parent namespaces
 * ----------------------------------------------------------------------------- */
%fragment("js_initializer", "templates")
%{
  // a class template for creating proxies of undefined types
#if (SWIG_V8_VERSION < 0x031900)
  SWIGV8_SWIGTYPE_Proxy_class_templ = v8::Persistent<v8::FunctionTemplate>::New(SWIGV8_CreateClassTemplate("SwigProxy"));
#else
  SWIGV8_SWIGTYPE_Proxy_class_templ.Reset(v8::Isolate::GetCurrent(), SWIGV8_CreateClassTemplate("SwigProxy"));
#endif

  /* create objects for namespaces */
  $jsv8nspaces

  /* create class templates */
  $jsv8classtemplates

  /* register wrapper functions */
  $jsv8wrappers

  /* setup inheritances */
  $jsv8inheritance

  /* class instances */
  $jsv8classinstances

  /* add static class functions and variables */
  $jsv8staticwrappers

  /* register classes */
  $jsv8registerclasses

  /* create and register namespace objects */
  $jsv8registernspaces
}

#if defined(BUILDING_NODE_EXTENSION)
NODE_MODULE($jsname, $jsname_initialize)
#endif
%}
