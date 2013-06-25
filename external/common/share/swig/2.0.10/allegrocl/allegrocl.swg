/* Define a C preprocessor symbol that can be used in interface files
   to distinguish between the SWIG language modules. */ 

#define SWIG_ALLEGRO_CL

#define %ffargs(...) %feature("ffargs", "1", ##__VA_ARGS__)
%ffargs(strings_convert="t");

/* typemaps for argument and result type conversions. */
%typemap(lin,numinputs=1)	SWIGTYPE 	"(cl::let (($out $in))\n  $body)";

%typemap(lout) bool, char, unsigned char, signed char,
               short, signed short, unsigned short,
               int, signed int, unsigned int,
               long, signed long, unsigned long,
               float, double, long double, char *, void *,
               enum SWIGTYPE    "(cl::setq ACL_ffresult $body)";
%typemap(lout) void "$body";
#ifdef __cplusplus
%typemap(lout) SWIGTYPE[ANY], SWIGTYPE *,
               SWIGTYPE &       
%{ (cl:let* ((address $body)
	  (new-inst (cl:make-instance '$lclass :foreign-address address)))
     (cl:when (cl:and $owner (cl:not (cl:zerop address)))
       (excl:schedule-finalization new-inst #'$ldestructor))
     (cl:setq ACL_ffresult new-inst)) %}

%typemap(lout) SWIGTYPE         "(cl::let* ((address $body)\n         (new-inst (cl::make-instance '$lclass :foreign-address address)))\n    (cl::unless (cl::zerop address)\n      (excl:schedule-finalization new-inst #'$ldestructor))\n    (cl::setq ACL_ffresult new-inst))";
#else
%typemap(lout) SWIGTYPE[ANY], SWIGTYPE *, SWIGTYPE &, SWIGTYPE
%{ (cl:let* ((address $body)
	  (new-inst (cl:make-instance '$lclass :foreign-address address)))
     (cl:setq ACL_ffresult new-inst)) %}
#endif

%typemap(lisptype) bool, const bool "cl:boolean";
%typemap(lisptype) char, const char "cl:character";
%typemap(lisptype) unsigned char, const unsigned char "cl:integer";
%typemap(lisptype) signed char, const signed char "cl:integer";

%typemap(ffitype) bool, const bool ":int";
%typemap(ffitype) char, const char,
		  signed char, const signed char ":char";
%typemap(ffitype) unsigned char, const unsigned char ":unsigned-char";
%typemap(ffitype) short, const short,
		  signed short, const signed short ":short";
%typemap(ffitype) unsigned short, const unsigned short ":unsigned-short";
%typemap(ffitype) int, const int, signed int, const signed int ":int";
%typemap(ffitype) unsigned int, const unsigned int ":unsigned-int";
%typemap(ffitype) long, const long, signed long, const signed long ":long";
%typemap(ffitype) unsigned long, const unsigned long ":unsigned-long";
%typemap(ffitype) float, const float ":float";
%typemap(ffitype) double, const double ":double";
%typemap(ffitype) char *, const char *, signed char *,
		  const signed char *, signed char &,
		  const signed char &			 "(* :char)";
%typemap(ffitype) unsigned char *, const unsigned char *,
		  unsigned char &, const unsigned char & "(* :unsigned-char)";
%typemap(ffitype) short *, const short *, short &,
		  const short &				"(* :short)";
%typemap(ffitype) unsigned short *, const unsigned short *,
		  unsigned short &, const unsigned short & "(* :unsigned-short)";
%typemap(ffitype) int *, const int *, int &, const int & "(* :int)";
%typemap(ffitype) unsigned int *, const unsigned int *,
		  unsigned int &, const unsigned int &	"(* :unsigned-int)";
%typemap(ffitype) void * "(* :void)";
%typemap(ffitype) void ":void";
%typemap(ffitype) enum SWIGTYPE ":int";
%typemap(ffitype) SWIGTYPE & "(* :void)";

/* const typemaps
idea: marshall all primitive c types to their respective lisp types
to maintain const corretness. For pointers/references, all bets
are off if you try to modify them.

idea: add a constant-p slot to the base foreign-pointer class. For
constant pointer/references check this value when setting (around method?)
and error if a setf operation is performed on the address of this object.

*/

/* 
%exception %{
   try {
      $action
   } catch (...) {
      return $null;
   }
%}

*/

// %typemap(throws) SWIGTYPE {
//   (void)$1;
//   SWIG_fail;
// }

%typemap(ctype) bool, const bool		"int";
%typemap(ctype) char, unsigned char, signed char,
                short, signed short, unsigned short,
                int, signed int, unsigned int,
                long, signed long, unsigned long,
                float, double, long double, char *, void *, void,
                enum SWIGTYPE, SWIGTYPE *, SWIGTYPE[],
                SWIGTYPE[ANY], SWIGTYPE &, const SWIGTYPE  "$1_ltype";
%typemap(ctype) SWIGTYPE                   "$&1_type";

%typemap(in) bool                          "$1 = (bool)$input;";
%typemap(in) char, unsigned char, signed char,
             short, signed short, unsigned short,
             int, signed int, unsigned int,
             long, signed long, unsigned long,
             float, double, long double, char *, void *, void,
             enum SWIGTYPE, SWIGTYPE *, SWIGTYPE[],
             SWIGTYPE[ANY], SWIGTYPE &     "$1 = $input;";
%typemap(in) SWIGTYPE                      "$1 = *$input;";

/* We don't need to do any actual C-side typechecking, but need to
   use the precedence values to choose which overloaded function
   interfaces to generate when conflicts arise. */

/* predefined precedence values

Symbolic Name                   Precedence Value
------------------------------  ------------------
SWIG_TYPECHECK_POINTER           0  
SWIG_TYPECHECK_VOIDPTR           10 
SWIG_TYPECHECK_BOOL              15 
SWIG_TYPECHECK_UINT8             20 
SWIG_TYPECHECK_INT8              25 
SWIG_TYPECHECK_UINT16            30 
SWIG_TYPECHECK_INT16             35 
SWIG_TYPECHECK_UINT32            40 
SWIG_TYPECHECK_INT32             45 
SWIG_TYPECHECK_UINT64            50 
SWIG_TYPECHECK_INT64             55 
SWIG_TYPECHECK_UINT128           60 
SWIG_TYPECHECK_INT128            65 
SWIG_TYPECHECK_INTEGER           70 
SWIG_TYPECHECK_FLOAT             80 
SWIG_TYPECHECK_DOUBLE            90 
SWIG_TYPECHECK_COMPLEX           100 
SWIG_TYPECHECK_UNICHAR           110 
SWIG_TYPECHECK_UNISTRING         120 
SWIG_TYPECHECK_CHAR              130 
SWIG_TYPECHECK_STRING            140 
SWIG_TYPECHECK_BOOL_ARRAY        1015 
SWIG_TYPECHECK_INT8_ARRAY        1025 
SWIG_TYPECHECK_INT16_ARRAY       1035 
SWIG_TYPECHECK_INT32_ARRAY       1045 
SWIG_TYPECHECK_INT64_ARRAY       1055 
SWIG_TYPECHECK_INT128_ARRAY      1065 
SWIG_TYPECHECK_FLOAT_ARRAY       1080 
SWIG_TYPECHECK_DOUBLE_ARRAY      1090 
SWIG_TYPECHECK_CHAR_ARRAY        1130 
SWIG_TYPECHECK_STRING_ARRAY      1140
*/

%typecheck(SWIG_TYPECHECK_BOOL) bool { $1 = 1; };
%typecheck(SWIG_TYPECHECK_CHAR) char { $1 = 1; };
%typecheck(SWIG_TYPECHECK_FLOAT) float { $1 = 1; };
%typecheck(SWIG_TYPECHECK_DOUBLE) double { $1 = 1; };
%typecheck(SWIG_TYPECHECK_STRING) char * { $1 = 1; };
%typecheck(SWIG_TYPECHECK_INTEGER)
                    unsigned char, signed char,
                    short, signed short, unsigned short,
                    int, signed int, unsigned int,
                    long, signed long, unsigned long,
                    enum SWIGTYPE { $1 = 1; };
%typecheck(SWIG_TYPECHECK_POINTER) SWIGTYPE *, SWIGTYPE &,
				   SWIGTYPE[], SWIGTYPE[ANY],
				   SWIGTYPE { $1 = 1; };

/* This maps C/C++ types to Lisp classes for overload dispatch */

%typemap(lispclass) bool "t";
%typemap(lispclass) char "cl:character";
%typemap(lispclass) unsigned char, signed char,
                    short, signed short, unsigned short,
                    int, signed int, unsigned int,
                    long, signed long, unsigned long,
                    enum SWIGTYPE       "cl:integer";
%typemap(lispclass) float "cl:single-float";
%typemap(lispclass) double "cl:double-float";
%typemap(lispclass) char * "cl:string";

%typemap(out) void                          "";
%typemap(out) bool                          "$result = (int)$1;";
%typemap(out) char, unsigned char, signed char,
              short, signed short, unsigned short,
              int, signed int, unsigned int,
              long, signed long, unsigned long,
              float, double, long double, char *, void *,
              enum SWIGTYPE, SWIGTYPE *,
              SWIGTYPE[ANY], SWIGTYPE &    "$result = $1;";
#ifdef __cplusplus
%typemap(out) SWIGTYPE                     "$result = new $1_ltype($1);";
#else
%typemap(out) SWIGTYPE {
  $result = ($&1_ltype) malloc(sizeof($1_type));
  memmove($result, &$1, sizeof($1_type));
}
#endif

//////////////////////////////////////////////////////////////
// UCS-2 string conversion

// should this be SWIG_TYPECHECK_CHAR?
%typecheck(SWIG_TYPECHECK_UNICHAR) wchar_t { $1 = 1; };

%typemap(in)        wchar_t "$1 = $input;";
%typemap(lin,numinputs=1)       wchar_t "(cl::let (($out (cl:char-code $in)))\n  $body)";
%typemap(lin,numinputs=1)       wchar_t * "(excl:with-native-string ($out $in
:external-format #+little-endian :fat-le #-little-endian :fat)\n
$body)"

%typemap(out)       wchar_t "$result = $1;";
%typemap(lout)      wchar_t "(cl::setq ACL_ffresult (cl::code-char $body))";
%typemap(lout)      wchar_t * "(cl::setq ACL_ffresult (excl:native-to-string $body
:external-format #+little-endian :fat-le #-little-endian :fat))";

%typemap(ffitype)   wchar_t ":unsigned-short";
%typemap(lisptype)  wchar_t "";
%typemap(ctype)     wchar_t "wchar_t";
%typemap(lispclass) wchar_t "cl:character";
%typemap(lispclass) wchar_t * "cl:string";
//////////////////////////////////////////////////////////////

/* Array reference typemaps */
%apply SWIGTYPE & { SWIGTYPE ((&)[ANY]) }

/* const pointers */
%apply SWIGTYPE * { SWIGTYPE *const }

/* name conversion for overloaded operators. */
#ifdef __cplusplus
%rename(__add__)	     *::operator+;
%rename(__pos__)	     *::operator+();
%rename(__pos__)	     *::operator+() const;

%rename(__sub__)	     *::operator-;
%rename(__neg__)	     *::operator-() const;
%rename(__neg__)	     *::operator-();

%rename(__mul__)	     *::operator*;
%rename(__deref__)	     *::operator*();
%rename(__deref__)	     *::operator*() const;

%rename(__div__)	     *::operator/;
%rename(__mod__)	     *::operator%;
%rename(__logxor__)	     *::operator^;
%rename(__logand__)	     *::operator&;
%rename(__logior__)	     *::operator|;
%rename(__lognot__)	     *::operator~();
%rename(__lognot__)	     *::operator~() const;

%rename(__not__)	     *::operator!();
%rename(__not__)	     *::operator!() const;

%rename(__assign__)	     *::operator=;

%rename(__add_assign__)      *::operator+=;
%rename(__sub_assign__)	     *::operator-=;
%rename(__mul_assign__)	     *::operator*=;
%rename(__div_assign__)	     *::operator/=;
%rename(__mod_assign__)	     *::operator%=;
%rename(__logxor_assign__)   *::operator^=;
%rename(__logand_assign__)   *::operator&=;
%rename(__logior_assign__)   *::operator|=;

%rename(__lshift__)	     *::operator<<;
%rename(__lshift_assign__)   *::operator<<=;
%rename(__rshift__)	     *::operator>>;
%rename(__rshift_assign__)   *::operator>>=;

%rename(__eq__)		     *::operator==;
%rename(__ne__)		     *::operator!=;
%rename(__lt__)		     *::operator<;
%rename(__gt__)		     *::operator>;
%rename(__lte__)	     *::operator<=;
%rename(__gte__)	     *::operator>=;

%rename(__and__)	     *::operator&&;
%rename(__or__)		     *::operator||;

%rename(__preincr__)	     *::operator++();
%rename(__postincr__)	     *::operator++(int);
%rename(__predecr__)	     *::operator--();
%rename(__postdecr__)	     *::operator--(int);

%rename(__comma__)	     *::operator,();
%rename(__comma__)	     *::operator,() const;

%rename(__member_ref__)      *::operator->;
%rename(__member_func_ref__) *::operator->*;

%rename(__funcall__)	     *::operator();
%rename(__aref__)	     *::operator[];

%rename(__bool__)	     *::operator bool();
%rename(__bool__)	     *::operator bool() const;
#endif

%insert("lisphead") %{
(eval-when (:compile-toplevel :load-toplevel :execute)

  ;; avoid compiling ef-templates at runtime
  (excl:find-external-format :fat)
  (excl:find-external-format :fat-le)

;;; You can define your own identifier converter if you want.
;;; Use the -identifier-converter command line argument to
;;; specify its name.

(eval-when (:compile-toplevel :load-toplevel :execute)
   (cl::defparameter *swig-export-list* nil))

(cl::defconstant *void* :..void..)

;; parsers to aid in finding SWIG definitions in files.
(cl::defun scm-p1 (form)
  (let* ((info (cl::second form))
	 (id (car info))
	 (id-args (if (eq (cl::car form) 'swig-dispatcher)
		      (cl::cdr info)
		      (cl::cddr info))))
    (cl::apply *swig-identifier-converter* id 
	   (cl::progn (cl::when (cl::eq (cl::car form) 'swig-dispatcher)
		    (cl::remf id-args :arities))
		  id-args))))

(cl::defmacro defswig1 (name (&rest args) &body body)
  `(cl::progn (cl::defmacro ,name ,args
	    ,@body)
	  (excl::define-simple-parser ,name scm-p1)) )

(cl::defmacro defswig2 (name (&rest args) &body body)
  `(cl::progn (cl::defmacro ,name ,args
	    ,@body)
	  (excl::define-simple-parser ,name second)))

(defun read-symbol-from-string (string)
  (cl::multiple-value-bind (result position)
      (cl::read-from-string string nil "eof" :preserve-whitespace t)
    (cl::if (cl::and (cl::symbolp result)
    	             (cl::eql position (cl::length string)))
        result
	(cl::multiple-value-bind (sym)
	    (cl::intern string)
	  sym))))

(cl::defun full-name (id type arity class)
  ; We need some kind of a hack here to handle template classes
  ; and other synonym types right. We need the original name.
  (let*( (sym (read-symbol-from-string 
                (if (eq *swig-identifier-converter* 'identifier-convert-lispify)
                  (string-lispify id)
                  id)))
         (sym-class (find-class sym nil))
         (id (cond ( (not sym-class)
                     id )
                   ( (and sym-class
                          (not (eq (class-name sym-class)
                                sym)))
                     (class-name sym-class) )
                   ( t
                     id ))) )
    (cl::case type
      (:getter (cl::format nil "~@[~A_~]~A" class id))
      (:constructor (cl::format nil "new_~A~@[~A~]" id arity))
      (:destructor (cl::format nil "delete_~A" id))
      (:type (cl::format nil "ff_~A" id))
      (:slot id)
      (:ff-operator (cl::format nil "ffi_~A" id))
      (otherwise (cl::format nil "~@[~A_~]~A~@[~A~]"
                         class id arity)))))
  
(cl::defun identifier-convert-null (id &key type class arity)
  (cl::if (cl::eq type :setter)
      `(cl::setf ,(identifier-convert-null
               id :type :getter :class class :arity arity))
      (read-symbol-from-string (full-name id type arity class))))

(cl::defun string-lispify (str)
  (cl::let ( (cname (excl::replace-regexp str "_" "-"))
             (lastcase :other)
             newcase char res ) 
    (cl::dotimes (n (cl::length cname))
      (cl::setf char (cl::schar cname n))
      (excl::if* (cl::alpha-char-p char)
         then
              (cl::setf newcase (cl::if (cl::upper-case-p char) :upper :lower))
              (cl::when (cl::and (cl::eq lastcase :lower)
                                 (cl::eq newcase :upper))
                ;; case change... add a dash
                (cl::push #\- res)
                (cl::setf newcase :other))
              (cl::push (cl::char-downcase char) res)
              (cl::setf lastcase newcase)
         else
              (cl::push char res)
              (cl::setf lastcase :other)))
    (cl::coerce (cl::nreverse res) 'string)))
  
(cl::defun identifier-convert-lispify (cname &key type class arity)
  (cl::assert (cl::stringp cname))
  (cl::when (cl::eq type :setter)
    (cl::return-from identifier-convert-lispify
      `(cl::setf ,(identifier-convert-lispify
               cname :type :getter :class class :arity arity))))
  (cl::setq cname (full-name cname type arity class))
  (cl::if (cl::eq type :constant)
      (cl::setf cname (cl::format nil "*~A*" cname)))
  (read-symbol-from-string (string-lispify cname)))

(cl::defun id-convert-and-export (name &rest kwargs)
  (cl::multiple-value-bind (symbol package)
      (cl::apply *swig-identifier-converter* name kwargs)
    (cl::let ((args (cl::list (cl::if (cl::consp symbol)
    	     	    	         (cl::cadr symbol) symbol)
                      (cl::or package cl::*package*))))
      (cl::apply #'cl::export args)
      (cl::pushnew args *swig-export-list*))
    symbol))

(cl::defmacro swig-insert-id (name namespace &key (type :type) class)
  `(cl::let ((cl::*package* (cl::find-package ,(package-name-for-namespace namespace))))
    (id-convert-and-export ,name :type ,type :class ,class)))

(defswig2 swig-defconstant (string value)
  (cl::let ((symbol (id-convert-and-export string :type :constant)))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
       (cl::defconstant ,symbol ,value))))

(cl::defun maybe-reorder-args (funcname arglist)
  ;; in the foreign setter function the new value will be the last argument
  ;; in Lisp it needs to be the first
  (cl::if (cl::consp funcname)
      (cl::append (cl::last arglist) (cl::butlast arglist))
      arglist))

(cl::defun maybe-return-value (funcname arglist)
  ;; setf functions should return the new value
  (cl::when (cl::consp funcname)
    `(,(cl::if (cl::consp (cl::car arglist))
           (cl::caar arglist)
           (cl::car arglist)))))

(cl::defun swig-anyvarargs-p (arglist)
  (cl::member :SWIG__varargs_ arglist))

(defswig1 swig-defun ((name &optional (mangled-name name)
                            &key (type :operator) class arity)
                      arglist kwargs
		      &body body)
  (cl::let* ((symbol (id-convert-and-export name :type type
                          :arity arity :class class))
             (mangle (excl::if* (cl::string-equal name mangled-name)
                      then (id-convert-and-export 
				    (cl::cond
					  ((cl::eq type :setter) (cl::format nil "~A-set" name))
					  ((cl::eq type :getter) (cl::format nil "~A-get" name))
					  (t name))
				    :type :ff-operator :arity arity :class class)
                      else (cl::intern mangled-name)))
         (defun-args (maybe-reorder-args
                      symbol
		      (cl::mapcar #'cl::car (cl::and (cl::not (cl::equal arglist '(:void)))
					 (cl::loop as i in arglist
					       when (cl::eq (cl::car i) :p+)
					       collect (cl::cdr i))))))
	 (ffargs (cl::if (cl::equal arglist '(:void))
	 	      arglist
		    (cl::mapcar #'cl::cdr arglist)))
	 )
    (cl::when (swig-anyvarargs-p ffargs)
      (cl::setq ffargs '()))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
       (excl::compiler-let ((*record-xref-info* nil))
         (ff:def-foreign-call (,mangle ,mangled-name) ,ffargs ,@kwargs))
       (cl::macrolet ((swig-ff-call (&rest args)
                      (cl::cons ',mangle args)))
         (cl::defun ,symbol ,defun-args
           ,@body
           ,@(maybe-return-value symbol defun-args))))))

(defswig1 swig-defmethod ((name &optional (mangled-name name)
	  	                &key (type :operator) class arity)
                          ffargs kwargs
                          &body body)
  (cl::let* ((symbol (id-convert-and-export name :type type
                          :arity arity :class class))
         (mangle (cl::intern mangled-name))
         (defmethod-args (maybe-reorder-args
                          symbol
                          (cl::unless (cl::equal ffargs '(:void))
                            (cl::loop for (lisparg name dispatch) in ffargs
			    	  when (eq lisparg :p+)
                                  collect `(,name ,dispatch)))))
         (ffargs (cl::if (cl::equal ffargs '(:void))
                     ffargs
                     (cl::loop for (nil name nil . ffi) in ffargs
                           collect `(,name ,@ffi)))))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
       (excl::compiler-let ((*record-xref-info* nil))
         (ff:def-foreign-call (,mangle ,mangled-name) ,ffargs ,@kwargs))
       (cl::macrolet ((swig-ff-call (&rest args)
                      (cl::cons ',mangle args)))
         (cl::defmethod ,symbol ,defmethod-args
           ,@body
           ,@(maybe-return-value symbol defmethod-args))))))

(defswig1 swig-dispatcher ((name &key (type :operator) class arities))
  (cl::let ((symbol (id-convert-and-export name
                         :type type :class class)))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
       (cl::defun ,symbol (&rest args)
         (cl::case (cl::length args)
           ,@(cl::loop for arity in arities
                   for symbol-n = (id-convert-and-export name
                                           :type type :class class :arity arity)
                   collect `(,arity (cl::apply #',symbol-n args)))
	   (t (cl::error "No applicable wrapper-methods for foreign call ~a with args ~a of classes ~a" ',symbol args (cl::mapcar #'(cl::lambda (x) (cl::class-name (cl::class-of x))) args)))
	   )))))

(defswig2 swig-def-foreign-stub (name)
  (cl::let ((lsymbol (id-convert-and-export name :type :class))
	    (symbol (id-convert-and-export name :type :type)))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
	(ff:def-foreign-type ,symbol (:class ))
	(cl::defclass ,lsymbol (ff:foreign-pointer) ()))))

(defswig2 swig-def-foreign-class (name supers &rest rest)
  (cl::let ((lsymbol (id-convert-and-export name :type :class))
	    (symbol (id-convert-and-export name :type :type)))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
       (ff:def-foreign-type ,symbol ,@rest)
       (cl::defclass ,lsymbol ,supers
	 ((foreign-type :initform ',symbol :initarg :foreign-type
			:accessor foreign-pointer-type))))))

(defswig2 swig-def-foreign-type (name &rest rest)
  (cl::let ((symbol (id-convert-and-export name :type :type)))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
       (ff:def-foreign-type ,symbol ,@rest))))

(defswig2 swig-def-synonym-type (synonym of ff-synonym)
  `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
     (cl::setf (cl::find-class ',synonym) (cl::find-class ',of))
     (ff:def-foreign-type ,ff-synonym (:struct ))))

(cl::defun package-name-for-namespace (namespace)
  (excl::list-to-delimited-string
   (cl::cons *swig-module-name*
         (cl::mapcar #'(cl::lambda (name)
                     (cl::string
                      (cl::funcall *swig-identifier-converter*
                               name
                               :type :namespace)))
                 namespace))
   "."))

(cl::defmacro swig-defpackage (namespace)
  (cl::let* ((parent-namespaces (cl::maplist #'cl::reverse (cl::cdr (cl::reverse namespace))))
             (parent-strings (cl::mapcar #'package-name-for-namespace
                                 parent-namespaces))
             (string (package-name-for-namespace namespace)))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
      (cl::defpackage ,string
        (:use :swig :ff #+ignore '(:common-lisp :ff :excl)
              ,@parent-strings ,*swig-module-name*)
	(:import-from :cl :* :nil :t)))))

(cl::defmacro swig-in-package (namespace)
  `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
    (cl::in-package ,(package-name-for-namespace namespace))))

(defswig2 swig-defvar (name mangled-name &key type (ftype :unsigned-natural))
  (cl::let ((symbol (id-convert-and-export name :type type)))
    `(cl::eval-when (:compile-toplevel :load-toplevel :execute)
      (ff:def-foreign-variable (,symbol ,mangled-name) :type ,ftype))))

) ;; eval-when

(cl::eval-when (:compile-toplevel :execute)
  (cl::flet ((starts-with-p (str prefix)
              (cl::and (cl::>= (cl::length str) (cl::length prefix))
                (cl::string= str prefix :end1 (cl::length prefix)))))
    (cl::export (cl::loop for sym being each present-symbol of cl::*package*
                  when (cl::or (starts-with-p (cl::symbol-name sym) (cl::symbol-name :swig-))
                           (starts-with-p (cl::symbol-name sym) (cl::symbol-name :identifier-convert-)))
                  collect sym))))

%}

typedef void *__SWIGACL_FwdReference;

%{

#ifdef __cplusplus
#  define EXTERN   extern "C"
#else
#  define EXTERN   extern
#endif

#define EXPORT   EXTERN SWIGEXPORT

typedef void *__SWIGACL_FwdReference;

#include <string.h>
#include <stdlib.h>
%}
