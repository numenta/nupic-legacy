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

#ifndef APR_DBG_WIN32_HANDLES_H
#define APR_DBG_WIN32_HANDLES_H

#ifdef __cplusplus
extern "C" {
#endif

/* USAGE:
 * 
 * Add the following include to apr_private.h for internal debugging,
 * or copy this header into apr/include add the include below to apr.h
 * for really global debugging;
 *
 *   #include "apr_dbg_win32_handles.h"
 *
 * apr_dbg_log is the crux of this function ... it uses Win32 API and
 * no apr calls itself to log all activity to a file named for the
 * executing application with a .pid suffix.  Ergo several instances
 * may be executing and logged at once.
 *
 * HANDLE apr_dbg_log(char* fn, HANDLE ha, char* fl, int ln, int nh 
 *                           [, HANDLE *hv, char *dsc...])
 *
 * returns: the handle passed in ha, which is cast back to the real return type.
 *
 * formats one line into the debug log file if nh is zero;
 * ha (hex) seq(hex) tid(hex) fn     fl         ln
 * xxxxxxxx xxxxxxxx xxxxxxxx func() sourcefile:lineno
 * The macro apr_dbg_rv makes this simple to implement for many APIs
 * that simply take args that don't interest us, and return a handle.
 *
 * formats multiple lines (nh) into the debug log file for each hv/dsc pair
 * (nh must correspond to the number of pairs);
 * hv (hex) seq(hex) tid(hex) fn   dsc  fl         ln
 * xxxxxxxx xxxxxxxx xxxxxxxx func(arg) sourcefile:lineno
 * In this later usage, hv is the still the return value but is not
 * treated as a handle.
 */

APR_DECLARE_NONSTD(HANDLE) apr_dbg_log(char* fn, HANDLE ha, char* fl, int ln, 
                                       int nh,/* HANDLE *hv, char *dsc */...);

#define apr_dbg_rv(fn, args) (apr_dbg_log(#fn,(fn) args,__FILE__,__LINE__,0))

#define CloseHandle(h) \
    ((BOOL)apr_dbg_log("CloseHandle", \
                       (HANDLE)(CloseHandle)(h), \
                       __FILE__,__LINE__,1, \
                       &(h),""))

#define CreateEventA(sd,b1,b2,nm) apr_dbg_rv(CreateEventA,(sd,b1,b2,nm))
#define CreateEventW(sd,b1,b2,nm) apr_dbg_rv(CreateEventW,(sd,b1,b2,nm))

#define CreateFileA(nm,d1,d2,sd,d3,d4,h) apr_dbg_rv(CreateFileA,(nm,d1,d2,sd,d3,d4,h))
#define CreateFileW(nm,d1,d2,sd,d3,d4,h) apr_dbg_rv(CreateFileW,(nm,d1,d2,sd,d3,d4,h))

#define CreateFileMappingA(fh,sd,d1,d2,d3,nm) apr_dbg_rv(CreateFileMappingA,(fh,sd,d1,d2,d3,nm))
#define CreateFileMappingW(fh,sd,d1,d2,d3,nm) apr_dbg_rv(CreateFileMappingW,(fh,sd,d1,d2,d3,nm))

#define CreateMutexA(sd,b,nm) apr_dbg_rv(CreateMutexA,(sd,b,nm))
#define CreateMutexW(sd,b,nm) apr_dbg_rv(CreateMutexW,(sd,b,nm))

#define CreateIoCompletionPort(h1,h2,pd1,d2) apr_dbg_rv(CreateIoCompletionPort,(h1,h2,pd1,d2))

#define CreateNamedPipeA(nm,d1,d2,d3,d4,d5,d6,sd) apr_dbg_rv(CreateNamedPipeA,(nm,d1,d2,d3,d4,d5,d6,sd))
#define CreateNamedPipeW(nm,d1,d2,d3,d4,d5,d6,sd) apr_dbg_rv(CreateNamedPipeW,(nm,d1,d2,d3,d4,d5,d6,sd))

#define CreatePipe(ph1,ph2,sd,d) \
    ((BOOL)apr_dbg_log("CreatePipe", \
                       (HANDLE)(CreatePipe)(ph1,ph2,sd,d), \
                       __FILE__,__LINE__,2, \
                       (ph1),"hRead", \
                       (ph2),"hWrite"))

#define CreateProcessA(s1,s2,sd1,sd2,b,d1,s3,s4,pd2,hr) \
    ((BOOL)apr_dbg_log("CreateProcessA", \
                       (HANDLE)(CreateProcessA)(s1,s2,sd1,sd2,b,d1,s3,s4,pd2,hr), \
                       __FILE__,__LINE__,2, \
                       &((hr)->hProcess),"hProcess", \
                       &((hr)->hThread),"hThread"))
#define CreateProcessW(s1,s2,sd1,sd2,b,d1,s3,s4,pd2,hr) \
    ((BOOL)apr_dbg_log("CreateProcessW", \
                       (HANDLE)(CreateProcessW)(s1,s2,sd1,sd2,b,d1,s3,s4,pd2,hr), \
                       __FILE__,__LINE__,2, \
                       &((hr)->hProcess),"hProcess", \
                       &((hr)->hThread),"hThread"))

#define CreateSemaphoreA(sd,d1,d2,nm) apr_dbg_rv(CreateSemaphoreA,(sd,d1,d2,nm))
#define CreateSemaphoreW(sd,d1,d2,nm) apr_dbg_rv(CreateSemaphoreW,(sd,d1,d2,nm))

#define CreateThread(sd,d1,fn,pv,d2,pd3) apr_dbg_rv(CreateThread,(sd,d1,fn,pv,d2,pd3))

#define DeregisterEventSource(h) \
    ((BOOL)apr_dbg_log("DeregisterEventSource", \
                       (HANDLE)(DeregisterEventSource)(h), \
                       __FILE__,__LINE__,1, \
                       &(h),""))

#define DuplicateHandle(h1,h2,h3,ph4,d1,b,d2) \
    ((BOOL)apr_dbg_log("DuplicateHandle", \
                       (HANDLE)(DuplicateHandle)(h1,h2,h3,ph4,d1,b,d2), \
                       __FILE__,__LINE__,2, \
                       (ph4),((h3)==GetCurrentProcess()) \
                                   ? "Target" : "EXTERN Target", \
                       &(h2),((h1)==GetCurrentProcess()) \
                                 ? "Source" : "EXTERN Source"))

#define GetCurrentProcess() \
    (apr_dbg_log("GetCurrentProcess", \
                 (GetCurrentProcess)(),__FILE__,__LINE__,0))

#define GetCurrentThread() \
    (apr_dbg_log("GetCurrentThread", \
                 (GetCurrentThread)(),__FILE__,__LINE__,0))

#define GetModuleHandleA(nm) apr_dbg_rv(GetModuleHandleA,(nm))
#define GetModuleHandleW(nm) apr_dbg_rv(GetModuleHandleW,(nm))

#define GetStdHandle(d) apr_dbg_rv(GetStdHandle,(d))

#define LoadLibraryA(nm) apr_dbg_rv(LoadLibraryA,(nm))
#define LoadLibraryW(nm) apr_dbg_rv(LoadLibraryW,(nm))

#define LoadLibraryExA(nm,h,d) apr_dbg_rv(LoadLibraryExA,(nm,h,d))
#define LoadLibraryExW(nm,h,d) apr_dbg_rv(LoadLibraryExW,(nm,h,d))

#define OpenEventA(d,b,nm) apr_dbg_rv(OpenEventA,(d,b,nm))
#define OpenEventW(d,b,nm) apr_dbg_rv(OpenEventW,(d,b,nm))

#define OpenFileMappingA(d,b,nm) apr_dbg_rv(OpenFileMappingA,(d,b,nm))
#define OpenFileMappingW(d,b,nm) apr_dbg_rv(OpenFileMappingW,(d,b,nm))

#define RegisterEventSourceA(s1,s2) apr_dbg_rv(RegisterEventSourceA,(s1,s2))
#define RegisterEventSourceW(s1,s2) apr_dbg_rv(RegisterEventSourceW,(s1,s2))

#define SetEvent(h) \
    ((BOOL)apr_dbg_log("SetEvent", \
                       (HANDLE)(SetEvent)(h), \
                       __FILE__,__LINE__,1, \
                       &(h),""))

#define SetStdHandle(d,h) \
    ((BOOL)apr_dbg_log("SetStdHandle", \
                       (HANDLE)(SetStdHandle)(d,h), \
                       __FILE__,__LINE__,1,&(h),""))

#define socket(i1,i2,i3) \
    ((SOCKET)apr_dbg_log("socket", \
                         (HANDLE)(socket)(i1,i2,i3), \
                       __FILE__,__LINE__,0))

#define WaitForSingleObject(h,d) \
    ((DWORD)apr_dbg_log("WaitForSingleObject", \
                        (HANDLE)(WaitForSingleObject)(h,d), \
                        __FILE__,__LINE__,1,&(h),"Signaled"))

#define WaitForSingleObjectEx(h,d,b) \
    ((DWORD)apr_dbg_log("WaitForSingleObjectEx", \
                        (HANDLE)(WaitForSingleObjectEx)(h,d,b), \
                        __FILE__,__LINE__,1,&(h),"Signaled"))

#define WaitForMultipleObjects(d1,ah,b,d2) \
    ((DWORD)apr_dbg_log("WaitForMultipleObjects", \
                        (HANDLE)(WaitForMultipleObjects)(d1,ah,b,d2), \
                        __FILE__,__LINE__,1,ah,"Signaled"))

#define WaitForMultipleObjectsEx(d1,ah,b1,d2,b2) \
    ((DWORD)apr_dbg_log("WaitForMultipleObjectsEx", \
                        (HANDLE)(WaitForMultipleObjectsEx)(d1,ah,b1,d2,b2), \
                        __FILE__,__LINE__,1,ah,"Signaled"))

#define WSASocketA(i1,i2,i3,pi,g,dw) \
    ((SOCKET)apr_dbg_log("WSASocketA", \
                         (HANDLE)(WSASocketA)(i1,i2,i3,pi,g,dw), \
                       __FILE__,__LINE__,0))

#define WSASocketW(i1,i2,i3,pi,g,dw) \
    ((SOCKET)apr_dbg_log("WSASocketW", \
                         (HANDLE)(WSASocketW)(i1,i2,i3,pi,g,dw), \
                       __FILE__,__LINE__,0))

#define closesocket(sh) \
    ((int)apr_dbg_log("closesocket", \
                      (HANDLE)(closesocket)(sh), \
                      __FILE__,__LINE__,1,&(sh),""))

#define _beginthread(fn,d,pv) \
    ((unsigned long)apr_dbg_log("_beginthread", \
                                (HANDLE)(_beginthread)(fn,d,pv), \
                                __FILE__,__LINE__,0))

#define _beginthreadex(sd,d1,fn,pv,d2,pd3) \
    ((unsigned long)apr_dbg_log("_beginthreadex", \
                                (HANDLE)(_beginthreadex)(sd,d1,fn,pv,d2,pd3), \
                                __FILE__,__LINE__,0))

#ifdef __cplusplus
}
#endif

#endif /* !defined(APR_DBG_WIN32_HANDLES_H) */
