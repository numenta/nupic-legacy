/* -----------------------------------------------------------------------------
 * error manipulation
 * ----------------------------------------------------------------------------- */

SWIGINTERN const char*
SWIG_Perl_ErrorType(int code) {
  const char* type = 0;
  switch(code) {
  case SWIG_MemoryError:
    type = "MemoryError";
    break;
  case SWIG_IOError:
    type = "IOError";
    break;
  case SWIG_RuntimeError:
    type = "RuntimeError";
    break;
  case SWIG_IndexError:
    type = "IndexError";
    break;
  case SWIG_TypeError:
    type = "TypeError";
    break;
  case SWIG_DivisionByZero:
    type = "ZeroDivisionError";
    break;
  case SWIG_OverflowError:
    type = "OverflowError";
    break;
  case SWIG_SyntaxError:
    type = "SyntaxError";
    break;
  case SWIG_ValueError:
    type = "ValueError";
    break;
  case SWIG_SystemError:
    type = "SystemError";
    break;
  case SWIG_AttributeError:
    type = "AttributeError";
    break;
  default:
    type = "RuntimeError";
  }
  return type;
}



