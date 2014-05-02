%exception
{
  try
  {
    $action
  }
  catch(std::bad_alloc &)
  {
    const jclass clazz = JCALL1(FindClass, jenv, "java/lang/OutOfMemoryError");
    JCALL2(ThrowNew, jenv, clazz, "Not enough memory");
    return $null;
  }
  catch(std::exception &e)
  {
    const jclass clazz = JCALL1(FindClass, jenv, "java/lang/Exception");
    JCALL2(ThrowNew, jenv, clazz, e.what());
    return $null;
  }
  catch(...)
  {
    const jclass clazz = JCALL1(FindClass, jenv, "java/lang/Exception");
    JCALL2(ThrowNew, jenv, clazz, "Unknown error.");
    return $null;
  }
} // End of exception handling.
