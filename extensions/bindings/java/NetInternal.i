%module net_internal
%{
#include <nta2/utils2/Log.hpp>
#include <nta2/utils2/LogItem.hpp>
#include <nta2/utils2/LoggingException.hpp>
#include <nta2/types/Types.hpp>
#include <nta2/types/Types.h>
#include <nta2/net/Network.hpp>
#include <nta2/net/Region.hpp>
#include <nta2/net/Node.hpp>
using namespace nupic;
%}

%include "Exception.i"

%include "std_string.i"
%include "std_vector.i"

%include <nta2/utils2/Log.hpp>
%include <nta2/utils2/LogItem.hpp>
%include <nta2/utils2/LoggingException.hpp>

%include <nupic/types/Types.h>
%include <nupic/types/Types.hpp>

%include <nta2/net/Network.hpp>
%include <nta2/net/Region.hpp>
%include <nta2/net/Node.hpp>
