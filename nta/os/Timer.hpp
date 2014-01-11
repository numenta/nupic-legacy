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
 * Timer interface
 */

#ifndef NTA_TIMER2_HPP
#define NTA_TIMER2_HPP

#include <string>
#include <nta/types/types.hpp>

namespace nta 
{

  /**
   * @Responsibility
   * Simple stopwatch services
   * 
   * @Description
   * A timer object is a stopwatch. You can start it, stop it, read the
   * elapsed time, and reset it. It is very convenient for performance
   * measurements. 
   * 
   * Uses the most precise and lowest overhead timer available on a given system.
   *
   */
  class Timer 
  {
  public:

    /**
     * Create a stopwatch
     * 
     * @param startme  If true, the timer is started when created
     */
    Timer(bool startme = false);


    /**
     * Start the stopwatch
     */
    void
    start();


    /**
     * Stop the stopwatch. When restarted, time will accumulate
     */
    void
    stop();


    /**
     * If stopped, return total elapsed time. 
     * If started, return current elapsed time but don't stop the clock
     * return the value in seconds;
     */
    Real64
    getElapsed() const;

    /**
     * Reset the stopwatch, setting accumulated time to zero. 
     */
    void
    reset();

    /**Train
     * Return the number of time the stopwatch has been started.
     */
    UInt64
    getStartCount() const;

    /**
     * Returns true is the stopwatch is currently running
     */
    bool
    isStarted() const;
    
    std::string
    toString() const;

  private:
    // internally times are stored as ticks
    UInt64 prevElapsed_;   // total time as of last stop() (in ticks)
    UInt64 start_;         // time that start() was called (in ticks)
    UInt64 nstarts_;       // number of times start() was called
    bool started_;         // true if was started

  }; // class Timer  
  
} // namespace nta

#endif // NTA_TIMER2_HPP

