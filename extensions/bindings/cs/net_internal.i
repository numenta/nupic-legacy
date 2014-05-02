%module net_internal
%{
#include <nta2/types/types.hpp>
#include <nta2/types/types.h>
#include <nta2/types/Exception.hpp>

#include <nta2/utils2/Log.hpp>
#include <nta2/utils2/LogItem.hpp>
#include <nta2/utils2/LoggingException.hpp>

#include <nta2/net/Network.hpp>
#include <nta2/net/Region.hpp>
#include <nta2/net/Node.hpp>
using namespace nta;
%}

# 'lock' is a keyword in C# so rename it to 'lockObject'
%rename (lockObject) lock;

# Exception classhes with System.Exception
%rename (BaseException) Exception;


%include "exception.i"

%include "std_string.i"
%include "std_vector.i"

%include <nta/types/types.h>
%include <nta/types/types.hpp>
%include <nta2/types/Exception.hpp>

%include <nta2/utils2/Log.hpp>
%include <nta2/utils2/LogItem.hpp>
%include <nta2/utils2/LoggingException.hpp>

%include <nta2/net/Network.hpp>
%include <nta2/net/Region.hpp>
%include <nta2/net/Node.hpp>
