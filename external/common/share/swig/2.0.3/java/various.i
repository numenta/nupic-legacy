/* -----------------------------------------------------------------------------
 * various.i
 *
 * SWIG Typemap library for Java.
 * Various useful typemaps.
 * ----------------------------------------------------------------------------- */

/* 
 * char **STRING_ARRAY typemaps. 
 * These typemaps are for C String arrays which are NULL terminated.
 *   char *values[] = { "one", "two", "three", NULL }; // note NULL
 * char ** is mapped to a Java String[].
 *
 * Example usage wrapping:
 *   %apply char **STRING_ARRAY { char **input };
 *   char ** foo(char **input);
 *  
 * Java usage:
 *   String numbers[] = { "one", "two", "three" };
 *   String[] ret = modulename.foo( numbers };
 */
%typemap(jni) char **STRING_ARRAY "jobjectArray"
%typemap(jtype) char **STRING_ARRAY "String[]"
%typemap(jstype) char **STRING_ARRAY "String[]"
%typemap(in) char **STRING_ARRAY (jint size) {
    int i = 0;
    size = JCALL1(GetArrayLength, jenv, $input);
#ifdef __cplusplus
    $1 = new char*[size+1];
#else
    $1 = (char **)calloc(size+1, sizeof(char *));
#endif
    for (i = 0; i<size; i++) {
        jstring j_string = (jstring)JCALL2(GetObjectArrayElement, jenv, $input, i);
        const char *c_string = JCALL2(GetStringUTFChars, jenv, j_string, 0);
#ifdef __cplusplus
        $1[i] = new char [strlen(c_string)+1];
#else
        $1[i] = (char *)calloc(strlen(c_string)+1, sizeof(const char *));
#endif
        strcpy($1[i], c_string);
        JCALL2(ReleaseStringUTFChars, jenv, j_string, c_string);
        JCALL1(DeleteLocalRef, jenv, j_string);
    }
    $1[i] = 0;
}

%typemap(freearg) char **STRING_ARRAY {
    int i;
    for (i=0; i<size$argnum-1; i++)
#ifdef __cplusplus
      delete[] $1[i];
    delete[] $1;
#else
      free($1[i]);
    free($1);
#endif
}

%typemap(out) char **STRING_ARRAY {
    int i;
    int len=0;
    jstring temp_string;
    const jclass clazz = JCALL1(FindClass, jenv, "java/lang/String");

    while ($1[len]) len++;    
    jresult = JCALL3(NewObjectArray, jenv, len, clazz, NULL);
    /* exception checking omitted */

    for (i=0; i<len; i++) {
      temp_string = JCALL1(NewStringUTF, jenv, *result++);
      JCALL3(SetObjectArrayElement, jenv, jresult, i, temp_string);
      JCALL1(DeleteLocalRef, jenv, temp_string);
    }
}

%typemap(javain) char **STRING_ARRAY "$javainput"
%typemap(javaout) char **STRING_ARRAY  {
    return $jnicall;
  }

/* 
 * char **STRING_OUT typemaps. 
 * These are typemaps for returning strings when using a C char ** parameter type.
 * The returned string appears in the 1st element of the passed in Java String array.
 *
 * Example usage wrapping:
 *   void foo(char **string_out);
 *  
 * Java usage:
 *   String stringOutArray[] = { "" };
 *   modulename.foo(stringOutArray);
 *   System.out.println( stringOutArray[0] );
 */
%typemap(jni) char **STRING_OUT "jobjectArray"
%typemap(jtype) char **STRING_OUT "String[]"
%typemap(jstype) char **STRING_OUT "String[]"
%typemap(javain) char **STRING_OUT "$javainput"

%typemap(in) char **STRING_OUT($*1_ltype temp) {
  if (!$input) {
    SWIG_JavaThrowException(jenv, SWIG_JavaNullPointerException, "array null");
    return $null;
  }
  if (JCALL1(GetArrayLength, jenv, $input) == 0) {
    SWIG_JavaThrowException(jenv, SWIG_JavaIndexOutOfBoundsException, "Array must contain at least 1 element");
    return $null;
  }
  $1 = &temp; 
}

%typemap(argout) char **STRING_OUT {
  jstring jnewstring = NULL;
  if($1) {
     jnewstring = JCALL1(NewStringUTF, jenv, *$1);
  }
  JCALL3(SetObjectArrayElement, jenv, $input, 0, jnewstring); 
}

/* 
 * char *BYTE typemaps. 
 * These are input typemaps for mapping a Java byte[] array to a C char array.
 * Note that as a Java array is used and thus passeed by reference, the C routine 
 * can return data to Java via the parameter.
 *
 * Example usage wrapping:
 *   void foo(char *array);
 *  
 * Java usage:
 *   byte b[] = new byte[20];
 *   modulename.foo(b);
 */
%typemap(jni) char *BYTE "jbyteArray"
%typemap(jtype) char *BYTE "byte[]"
%typemap(jstype) char *BYTE "byte[]"
%typemap(in) char *BYTE {
    $1 = (char *) JCALL2(GetByteArrayElements, jenv, $input, 0); 
}

%typemap(argout) char *BYTE {
    JCALL3(ReleaseByteArrayElements, jenv, $input, (jbyte *) $1, 0); 
}

%typemap(javain) char *BYTE "$javainput"

/* Prevent default freearg typemap from being used */
%typemap(freearg) char *BYTE ""

