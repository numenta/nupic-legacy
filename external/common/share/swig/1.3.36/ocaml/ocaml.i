/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * ocaml.i
 *
 * SWIG Configuration File for Ocaml
 * ----------------------------------------------------------------------------- */

%runtime %{
#define SWIGSTATIC static
%}

/* Insert common stuff */
%insert(runtime) "swigrun.swg"

/* Include headers */
%insert(runtime) "ocamldec.swg"

/* Type registration */
%insert(init) "swiginit.swg"
%insert(init) "typeregister.swg"

%insert(mlitail) %{
  val swig_val : c_enum_type -> c_obj -> Swig.c_obj
%}

%insert(mltail) %{
  let rec swig_val t v = 
    match v with
        C_enum e -> enum_to_int t v
      | C_list l -> Swig.C_list (List.map (swig_val t) l)
      | C_array a -> Swig.C_array (Array.map (swig_val t) a)
      | _ -> Obj.magic v
%}

/*#ifndef SWIG_NOINCLUDE*/
%insert(runtime) "ocaml.swg"
/*#endif*/

%insert(classtemplate) "class.swg"

/* Definitions */
#define SWIG_malloc(size) swig_malloc(size, FUNC_NAME)
#define SWIG_free(mem) free(mem)

/* Read in standard typemaps. */
%include <swig.swg>
%include <typemaps.i>
%include <typecheck.i>
%include <exception.i>
%include <preamble.swg>

/* ocaml keywords */
/* There's no need to use this, because of my rewriting machinery.  C++
 * words never collide with ocaml keywords */

/* still we include the file, but the warning says that the offending
   name will be properly renamed. Just to let the user to know about
   it. */
%include <ocamlkw.swg>
