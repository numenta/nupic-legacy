%module net_internal
%{
#include <nta2/types/Types.hpp>
#include <nta2/types/Types.h>
#include <nta2/types/Exception.hpp>

#include <nta2/utils2/Log.hpp>
#include <nta2/utils2/LogItem.hpp>
#include <nta2/utils2/LoggingException.hpp>

#include <nta2/net/Network.hpp>
#include <nta2/net/Region.hpp>
#include <nta2/net/Node.hpp>
using namespace nupic;
%}

# 'lock' is a keyword in C# so rename it to 'lockObject'
%rename (lockObject) lock;

# Exception classhes with System.Exception
%rename (BaseException) Exception;


%include "Exception.i"

%include "std_string.i"
%include "std_vector.i"

%include <nupic/types/Types.h>
%include <nupic/types/Types.hpp>
%include <nta2/types/Exception.hpp>

%include <nta2/utils2/Log.hpp>
%include <nta2/utils2/LogItem.hpp>
%include <nta2/utils2/LoggingException.hpp>

%include <nta2/net/Network.hpp>
%include <nta2/net/Region.hpp>
%include <nta2/net/Node.hpp>
