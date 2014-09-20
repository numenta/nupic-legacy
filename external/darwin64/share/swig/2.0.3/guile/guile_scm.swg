/* -----------------------------------------------------------------------------
 * guile_scm.swg
 *
 * This SWIG interface file is processed if the Guile module is run
 * with SCM_ flavor.
 * ----------------------------------------------------------------------------- */

#define SWIGGUILE_SCM

%runtime "swigrun.swg"       // Common C API type-checking code

%runtime "guile_scm_run.swg"
%include <ghinterface.i>
%include <guile.i>

%runtime %{

#define GUILE_MAYBE_VALUES \
      if (gswig_list_p) gswig_result = scm_values(gswig_result);

#define GUILE_MAYBE_VECTOR \
      if (gswig_list_p) gswig_result = scm_vector(gswig_result);

#define SWIG_APPEND_VALUE(object)						\
    if (gswig_result == SCM_UNSPECIFIED)						\
        gswig_result = object;							\
    else {									\
      if (!gswig_list_p) {							\
	      gswig_list_p = 1;							\
	      gswig_result = scm_listify(gswig_result, object, SCM_UNDEFINED);	\
      }									\
      else									\
            gswig_result = scm_append(scm_listify(gswig_result, scm_listify(object, SCM_UNDEFINED), SCM_UNDEFINED));		\
    }
    /* used by Lib/exception.i */
    #define gh_symbol2scm scm_str2symbol
    /* useb by Lib/cdata.i */
    #define gh_str2scm scm_mem2string

%}

%insert(init) "swiginit.swg"

%init %{
SWIG_GUILE_INIT_STATIC void
SWIG_init(void)
{
  SWIG_InitializeModule(0);
  SWIG_PropagateClientData();
%}
