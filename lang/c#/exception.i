
%exception
%{
  try
  {
    $action
  }
  catch (const std::exception & e)
  {
    SWIG_CSharpSetPendingException(SWIG_CSharpApplicationException, e.what());
  }
  catch (...)
  {
    SWIG_CSharpSetPendingException(
      SWIG_CSharpApplicationException,
      "Unknown error from C++ library");
  }
%}


