/* Define a C preprocessor symbol that can be used in interface files
   to distinguish between the SWIG language modules. */ 

#define SWIG_UFFI

/* Typespecs for basic types. */

%typemap(ffitype) char ":char";
%typemap(ffitype) unsigned char ":unsigned-char";
%typemap(ffitype) signed char ":char";
%typemap(ffitype) short ":short";
%typemap(ffitype) signed short ":short";
%typemap(ffitype) unsigned short ":unsigned-short";
%typemap(ffitype) int ":int";
%typemap(ffitype) signed int ":int";
%typemap(ffitype) unsigned int ":unsigned-int";
%typemap(ffitype) long ":long";
%typemap(ffitype) signed long ":long";
%typemap(ffitype) unsigned long ":unsigned-long";
%typemap(ffitype) float ":float";
%typemap(ffitype) double ":double";
%typemap(ffitype) char * ":cstring";
%typemap(ffitype) void * ":pointer-void";
%typemap(ffitype) void ":void";

// FIXME: This is guesswork
typedef long size_t;

%wrapper %{
(eval-when (compile eval)

;;; You can define your own identifier converter if you want.
;;; Use the -identifier-converter command line argument to
;;; specify its name. 
  
(defun identifier-convert-null (id &key type)
  (declare (ignore type))
  (read-from-string id))

(defun identifier-convert-lispify (cname &key type)
  (assert (stringp cname))
  (if (eq type :constant)
      (setf cname (format nil "*~A*" cname)))
  (setf cname (replace-regexp cname "_" "-"))
  (let ((lastcase :other)
        newcase char res)
    (dotimes (n (length cname))
      (setf char (schar cname n))
      (if* (alpha-char-p char)
         then
              (setf newcase (if (upper-case-p char) :upper :lower))

              (when (or (and (eq lastcase :upper) (eq newcase :lower))
                        (and (eq lastcase :lower) (eq newcase :upper)))
                ;; case change... add a dash                                    
                (push #\- res)
                (setf newcase :other))

              (push (char-downcase char) res)

              (setf lastcase newcase)

         else
              (push char res)
              (setf lastcase :other)))
    (read-from-string (coerce (nreverse res) 'string))))

(defun identifier-convert-low-level (cname &key type)
  (assert (stringp cname))
  (if (eq type :constant)
    (setf cname (format nil "+~A+" cname)))
  (setf cname (substitute #\- #\_ cname))
  (if (eq type :operator)
    (setf cname (format nil "%~A" cname)))
  (if (eq type :constant-function)
    nil)
  (read-from-string cname))



(defmacro swig-defconstant (string value &key (export T))
  (let ((symbol (funcall *swig-identifier-converter* string :type :constant)))
    `(eval-when (compile load eval)
       (uffi:def-constant ,symbol ,value ,export))))

(defmacro swig-defun (name &rest rest)
  (let ((symbol (funcall *swig-identifier-converter* name :type :operator)))
    `(eval-when (compile load eval)
      (uffi:def-function (,name ,symbol) ,@rest)
      (export (quote ,symbol)))))

(defmacro swig-def-struct (name &rest fields)
  "Declare a struct object"
  (let ((symbol (funcall *swig-identifier-converter* name :type :type)))
    `(eval-when (compile load eval)
       (uffi:def-struct ,symbol ,@fields)
       (export (quote ,symbol)))))
 

) ;; eval-when
%}
