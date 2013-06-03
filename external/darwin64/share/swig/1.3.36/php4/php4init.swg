
/* ------------------------------------------------------------
 * The start of the PHP initialization function 
 * ------------------------------------------------------------ */

%insert(init) "swiginit.swg"

%init %{
  SWIG_php_minit {
    SWIG_InitializeModule(0);
%}

