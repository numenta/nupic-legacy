%{
#include <gcj/cni.h>
%}

%include <gcj/javaprims.i>

extern jobject JvAllocObject (jclass cls);

extern jobject JvAllocObject (jclass cls, jsize sz);

extern void JvInitClass (jclass cls);

extern jstring JvAllocString (jsize sz);

extern jstring JvNewString (const jchar *chars, jsize len);

extern jstring JvNewStringLatin1 (const char *bytes, jsize len);

extern jstring JvNewStringLatin1 (const char *bytes);

extern jchar* JvGetStringChars (jstring str);

extern jsize JvGetStringUTFLength (jstring string);

extern jsize JvGetStringUTFRegion (jstring str, jsize start, jsize len, char *buf);

extern jstring JvNewStringUTF (const char *bytes);

extern void *JvMalloc (jsize size);

extern void JvFree (void *ptr);

extern jint JvCreateJavaVM (void* vm_args);

extern java::lang::Thread* JvAttachCurrentThread (jstring name, java::lang::ThreadGroup* group);

extern java::lang::Thread* JvAttachCurrentThreadAsDaemon (jstring name, java::lang::ThreadGroup* group);

extern jint JvDetachCurrentThread (void);


%include <gcj/cni.swg>

