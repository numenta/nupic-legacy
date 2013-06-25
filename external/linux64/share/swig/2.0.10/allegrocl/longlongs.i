/* -----------------------------------------------------------------------------
 * longlongs.i
 *
 * Typemap addition for support of 'long long' type and 'unsigned long long 
 * Makes use of swig-def-foreign-class, so this header should be loaded
 * after allegrocl.swg and after any custom user identifier-conversion
 * functions have been defined.
 * ----------------------------------------------------------------------------- */

#ifdef Acl64Bit
%typemap(ctype) long long, unsigned long long "$1_ltype";
%typemap(out) long long, unsigned long long "$result = $1;";

%typemap(ffitype) long long ":nat";
%typemap(ffitype) unsigned long long ":unsigned-nat";

%typemap(lout) long long, unsigned long long "  #+64bit (cl::setq ACL_ffresult $body)";

#else
%typemap(out) long long, unsigned long long "$result = &$1;";
%typemap(ffitype) long long "(:struct (l1 :long) (l2 :long))";

%typemap(ffitype) unsigned long long "(:struct (l1 :unsigned-long) (l2 :unsigned-long))";

%typemap(lout) long long 
"  (cl::setq ACL_ffresult (make-instance '#.(swig-insert-id \"longlong\" () :type :class)
                  :foreign-address $body))";

%typemap(lout) unsigned long long
"  (cl:setq ACL_ffresult (make-instance '#.(swig-insert-id \"ulonglong\" () :type :class)
                  :foreign-address $body))";

#endif

%typemap(in) long long, unsigned long long "$1 = $input;";


%insert("lisphead") %{

#-64bit
(swig-def-foreign-class "longlong"
 (ff:foreign-pointer)
 (:struct (l1 :long) (l2 :long)))

#-64bit
(swig-def-foreign-class "ulonglong"
 (ff:foreign-pointer)
 (:struct (l1 :unsigned-long) (l2 :unsigned-long)))
%}
