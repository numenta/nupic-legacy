/* Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef __pre_nw__
#define __pre_nw__

#include <stdint.h>

#ifndef __GNUC__
#pragma precompile_target "precomp.mch"
#endif

#define NETWARE

#define N_PLAT_NLM

#define FAR
#define far

/* no-op for Codewarrior C compiler; a functions are cdecl 
   by default */
#define cdecl

/* if we have wchar_t enabled in C++, predefine this type to avoid
   a conflict in Novell's header files */
#ifndef __GNUC__
#ifndef DOXYGEN
#if (__option(cplusplus) && __option(wchar_type))
#define _WCHAR_T
#endif
#endif
#endif

/* C9X defintion used by MSL C++ library */
#define DECIMAL_DIG 17

/* some code may want to use the MS convention for long long */
#ifndef __int64
#define __int64 long long
#endif

#endif



