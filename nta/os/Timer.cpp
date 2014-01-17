/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */


/** @file 
 * Generic OS Implementations for the OS class
 */

#include <nta/os/Timer.hpp>
#include <sstream>
using namespace nta;


// Define a couple of platform-specific helper functions

#if defined(NTA_PLATFORM_win32)

#include <windows.h>
static nta::UInt64 ticksPerSec_ = 0;
static nta::UInt64 initialTicks_ = 0;

// initTime is called by the constructor, so it will always
// have been called by the time we call getTicksPerSec or getCurrentTime
static inline void initTime()
{
  if (initialTicks_ == 0)
  {
    LARGE_INTEGER f;
    QueryPerformanceCounter(&f);
    initialTicks_ = (UInt64)(f.QuadPart);

    QueryPerformanceFrequency(&f);
    ticksPerSec_ = (UInt64)(f.QuadPart);
  }
}

static inline UInt64 getTicksPerSec()
{
  return ticksPerSec_;
}


static UInt64 getCurrentTime()
{
  LARGE_INTEGER v;
  QueryPerformanceCounter(&v);
  return (UInt64)(v.QuadPart) - initialTicks_;
}

#elif defined(NTA_PLATFORM_darwin)

// This include defines a UInt64 type that conflicts with the nta::UInt64 type. 
// Because of this, all UInt64 is explicitly qualified in the interface. 
#include <CoreServices/CoreServices.h>
#include <mach/mach.h>
#include <mach/mach_time.h>
#include <unistd.h>

// must be linked with -framework CoreServices

static uint64_t  initialTicks_ = 0;

static inline void initTime()
{
  if (initialT_ == 0)
    initialT_ = UnsignedWideToUint64(AbsoluteToNanoseconds(mach_absolute_time()));
}

static inline nta::UInt64 getCurrentTime()
{
  uint64_t t = mach_absolute_time();
  nta::UInt64 ticks = UnsignedWideToUInt64(AbsoluteToNanoseconds(t));
  return ticks - initialTicks_;
}

static inline nta::UInt64 getTicksPerSec()
{
  return (nta::UInt64)(1e9);
}


#else
// linux
#include <sys/time.h>

static nta::UInt64 initialTicks_ = 0;

static inline void initTime()
{
  if (initialTicks_ == 0)
  {
    struct timeval t;
    ::gettimeofday(&t, nullptr);
    initialTicks_ = nta::UInt64((t.tv_sec * 1e6) + t.tv_usec);
  }
}

static inline nta::UInt64 getCurrentTime()
{
  struct timeval t;
  ::gettimeofday(&t, nullptr);
  nta::UInt64 ticks = nta::UInt64((t.tv_sec * 1e6) + t.tv_usec);
  return ticks - initialTicks_;
}



static inline nta::UInt64 getTicksPerSec()
{
  return (nta::UInt64)(1e6);
}

#endif

Timer::Timer(bool startme)  
{
  initTime();
  reset();
  if (startme)
    start();
}


void Timer::start() 
{ 
  if (started_ == false) 
  {
    start_ = getCurrentTime();
    nstarts_++;
    started_ = true;
  }
}

/**
* Stop the stopwatch. When restarted, time will accumulate
*/

void Timer::stop() 
{  // stop the stopwatch
  if (started_ == true) 
  {
    prevElapsed_ += (getCurrentTime() - start_);
    start_ = 0;
    started_ = false;
  }
}

Real64 Timer::getElapsed() const
{   
  nta::UInt64 elapsed = prevElapsed_;
  if (started_) 
  {
    elapsed += (getCurrentTime() - start_);
  }   

  return (Real64)(elapsed) / (Real64)getTicksPerSec();
}

void Timer::reset() 
{
  prevElapsed_ = 0;
  start_ = 0;
  nstarts_ = 0;
  started_ = false;
}

UInt64 Timer::getStartCount() const
{ 
  return nstarts_; 
}

bool Timer::isStarted() const
{ 
  return started_; 
}


std::string Timer::toString() const
{
  std::stringstream ss;
  ss << "[Elapsed: " << getElapsed() << " Starts: " << getStartCount();
  if (isStarted())
    ss << " (running)";
  ss << "]";
  return ss.str();
}

