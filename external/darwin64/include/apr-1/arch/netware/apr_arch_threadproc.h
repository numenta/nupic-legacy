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

#include "apr.h"
#include "apr_thread_proc.h"
#include "apr_file_io.h"

#include <sys/wait.h>

#ifndef THREAD_PROC_H
#define THREAD_PROC_H

#define SHELL_PATH ""
#define APR_DEFAULT_STACK_SIZE 65536

struct apr_thread_t {
    apr_pool_t *pool;
    NXContext_t ctx;
    NXThreadId_t td;
    char *thread_name;
    apr_int32_t cancel;
    apr_int32_t cancel_how;
    void *data;
    apr_thread_start_t func;
    apr_status_t exitval;
};

struct apr_threadattr_t {
    apr_pool_t *pool;
    apr_size_t  stack_size;
    apr_int32_t detach;
    char *thread_name;
};

struct apr_threadkey_t {
    apr_pool_t *pool;
    NXKey_t key;
};

struct apr_procattr_t {
    apr_pool_t *pool;
    apr_file_t *parent_in;
    apr_file_t *child_in;
    apr_file_t *parent_out;
    apr_file_t *child_out;
    apr_file_t *parent_err;
    apr_file_t *child_err;
    char *currdir;
    apr_int32_t cmdtype;
    apr_int32_t detached;
    apr_int32_t addrspace;
};

struct apr_thread_once_t {
    unsigned long value;
};

/*
struct apr_proc_t {
    apr_pool_t *pool;
    pid_t pid;
    apr_procattr_t *attr;
};
*/

#endif  /* ! THREAD_PROC_H */

