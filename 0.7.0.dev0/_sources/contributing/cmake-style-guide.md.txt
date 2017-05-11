# CMake Style Guide

## Naming

**Functions**: _lower_case_ name. Ex:
`do_something(...)`

**Local variables**: _lower_case_ name. Local variables are used exclusively inside the file that contained them, and their values were simply passed as parameters to CMake functions. Ex:
`set(some_variable "...")`

**Global variables**: _UPPER_CASE_ name. Global variables(can also be called "export variables") are intended for exporting up/down-stream via the environment variable mechanism. Ex:
`set(SOME_VARIABLE "...")`

**Control statements**: _lower_case_ name without repeat the condition in the closing brackets. Ex:

```
if(condition)
  ...
else() # not repeat condition
  ...
endif() # not repeat condition
```

**Operators**: _UPPER_CASE_ name. Ex:
`if(condition STREQUAL "")`

**Directives and/or extra options**:  _UPPER_CASE_ name. Ex:
`do_something(... USE_THIS)`

## Examples

An real-world example:

```
function(set_platform system_name)
  if(${system_name} MATCHES "Darwin")
    set(PLATFORM "darwin")
  elseif(${system_name} MATCHES "Linux")
    set(PLATFORM "linux")
  else()
    set(PLATFORM "")
  endif()
endfunction()

cmake_minimum_required(VERSION 3.0)
set_platform(${CMAKE_SYSTEM_NAME})
```
