%insert(runtime) %{
#include <octave/oct.h>
#include <octave/parse.h>
#include <octave/ov-fcn-handle.h>
#include <octave/Cell.h>
#include <octave/oct-map.h>
%}

%insert(runtime) "swigrun.swg";
%insert(runtime) "swigerrors.swg";
%insert(runtime) "octrun.swg";

%insert(initbeforefunc) "swiginit.swg"

%insert(initbeforefunc) %{

static void SWIG_init_user(octave_swig_type* module_ns);

DEFUN_DLD (SWIG_name,args,nargout,SWIG_name_d) {
  static bool already_init=false;
  if (already_init)
    return octave_value_list();
  already_init=true;

  octave_swig_ref::register_type();
  octave_swig_packed::register_type();
  SWIG_InitializeModule(0);
  SWIG_PropagateClientData();
  
  install_builtin_function(swig_type,"swig_type",std::string());
  install_builtin_function(swig_typequery,"swig_typequery",std::string());
  install_builtin_function(swig_this,"swig_this",std::string());
  install_builtin_function(swig_subclass,"subclass",std::string());

  bool global_option=true; // * swig cli option should control this default
  for (int j=0;j<args.length();++j)
    if (args(j).is_string()&&args(j).string_value()=="noglobal")
      global_option=true;
    else if (args(j).is_string()&&args(j).string_value()=="noglobal")
      global_option=false;

  octave_swig_type* cvar_ns=new octave_swig_type;
  for (int j=0;swig_globals[j].name;++j)
    if (swig_globals[j].get_method)
      cvar_ns->assign(swig_globals[j].name,&swig_globals[j]);

  octave_swig_type* module_ns=new octave_swig_type(0, 0, 0, true);
  module_ns->assign("cvar",Swig::swig_value_ref(cvar_ns));
  for (int j=0;swig_globals[j].name;++j)
    if (swig_globals[j].method)
      module_ns->assign(swig_globals[j].name,&swig_globals[j]);

  // * need better solution here; swig_type -> octave_class mapping is 
  // * really n-to-1, in some cases such as template partial spec, etc. 
  // * see failing tests.
  for (int j=0;swig_types[j];++j)
    if (swig_types[j]->clientdata) {
      swig_octave_class* c=(swig_octave_class*)swig_types[j]->clientdata;
      module_ns->assign(c->name,
			Swig::swig_value_ref
			(new octave_swig_type(0,swig_types[j])));
    }

  SWIG_init_user(module_ns);

  SWIG_InstallOps(octave_swig_ref::static_type_id());

  // the incref is necessary so install_global doesn't destroy module_ns,
  // as it would if it installed something with the same name as the module.
  module_ns->incref();
  if (global_option)
    module_ns->install_global();
  module_ns->decref();

#if OCTAVE_API_VERSION_NUMBER<37
  link_to_global_variable(curr_sym_tab->lookup(SWIG_name_d,true));
#else
  symbol_table::varref(SWIG_name_d);
  symbol_table::mark_global(SWIG_name_d);
#endif
  set_global_value(SWIG_name_d,Swig::swig_value_ref(module_ns));

#if OCTAVE_API_VERSION_NUMBER>=37
  mlock();
#endif

  return octave_value_list();
}

// workaround bug in octave where installing global variable of custom type and then
// exiting without explicitly clearing the variable causes octave to segfault.
#if OCTAVE_API_VERSION_NUMBER>=37
struct oct_file_unload {
  ~oct_file_unload() {
    string_vector vars = symbol_table::global_variable_names();
    for (int i = 0; i < vars.length(); i++)
      symbol_table::clear_global(vars[i]);
  }
};
static oct_file_unload __unload;
#endif

%}

