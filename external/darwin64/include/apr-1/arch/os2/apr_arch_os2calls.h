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

#include "apr_errno.h"
#include <sys/types.h>
#include <sys/socket.h>

extern int (*apr_os2_socket)(int, int, int);
extern int (*apr_os2_select)(int *, int, int, int, long);
extern int (*apr_os2_sock_errno)();
extern int (*apr_os2_accept)(int, struct sockaddr *, int *);
extern int (*apr_os2_bind)(int, struct sockaddr *, int);
extern int (*apr_os2_connect)(int, struct sockaddr *, int);
extern int (*apr_os2_getpeername)(int, struct sockaddr *, int *);
extern int (*apr_os2_getsockname)(int, struct sockaddr *, int *);
extern int (*apr_os2_getsockopt)(int, int, int, char *, int *);
extern int (*apr_os2_ioctl)(int, int, caddr_t, int);
extern int (*apr_os2_listen)(int, int);
extern int (*apr_os2_recv)(int, char *, int, int);
extern int (*apr_os2_send)(int, const char *, int, int);
extern int (*apr_os2_setsockopt)(int, int, int, char *, int);
extern int (*apr_os2_shutdown)(int, int);
extern int (*apr_os2_soclose)(int);
extern int (*apr_os2_writev)(int, struct iovec *, int);
extern int (*apr_os2_sendto)(int, const char *, int, int, const struct sockaddr *, int);
extern int (*apr_os2_recvfrom)(int, char *, int, int, struct sockaddr *, int *);

#define socket apr_os2_socket
#define select apr_os2_select
#define sock_errno apr_os2_sock_errno
#define accept apr_os2_accept
#define bind apr_os2_bind
#define connect apr_os2_connect
#define getpeername apr_os2_getpeername
#define getsockname apr_os2_getsockname
#define getsockopt apr_os2_getsockopt
#define ioctl apr_os2_ioctl
#define listen apr_os2_listen
#define recv apr_os2_recv
#define send apr_os2_send
#define setsockopt apr_os2_setsockopt
#define shutdown apr_os2_shutdown
#define soclose apr_os2_soclose
#define writev apr_os2_writev
#define sendto apr_os2_sendto
#define recvfrom apr_os2_recvfrom
