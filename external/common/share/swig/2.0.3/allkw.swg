#ifndef __Lib_allkw_swg__
#define __Lib_allkw_swg__


/*  
  Include all the known keyword warnings.  Very useful for adding test
  files to the test-suite, or check if your own library is ok for all
  the swig supported languages.

  Use as 

    swig -Wallkw ...

  If you add a new language, remember to create a separete languagekw.swg
  file, and add it here.
  
*/

%include <chicken/chickenkw.swg>
%include <csharp/csharpkw.swg>
%include <d/dkw.swg>
%include <java/javakw.swg>
%include <php/phpkw.swg>
%include <pike/pikekw.swg>
%include <python/pythonkw.swg>
%include <ocaml/ocamlkw.swg>
%include <ruby/rubykw.swg>
%include <tcl/tclkw.swg>
%include <perl5/perlkw.swg>


#endif //__Lib_allkw_swg__
