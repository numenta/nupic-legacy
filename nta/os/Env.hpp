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
Environment Interface
*/

#ifndef NTA_ENV_HPP
#define NTA_ENV_HPP

#include <string>

namespace nta {

  class Env {
  public:

    /**
     * get the named environment variable from the environment. 
     * @param name Name of environment variable
     * @param value Value of environment variable. Set only if variable is found
     * @retval true if variable was found; false if not found. 
     * If false, then value parameter is not set
     **/
    static bool get(const std::string& name, std::string& value);
    
    /**
     * Set the named environment variable. 
     * @param name Name of environment variable
     * @param value Value to which environment variable is set
     */
    static void set(const std::string& name, const std::string& value);

    /**
     * Unset the named environment variable
     * @param name Name of environment variable to unset
     * If variable is not previously set, no error is returned. 
     */
    static void unset(const std::string& name);

    /**
     * Get the environment as an array of strings
     */
    static char** getenv();

    /**
     * An "option" is an environment variable of the form NTA_XXX.
     * The canonical form for an option name is all uppercase characters. 
     * These are convenience routines for using options. They canonicalize
     * the name and search the environment. 
     */
    static bool isOptionSet(const std::string& optionName);
    
    /**
     * Get the value of the NTA_XXX environment variable. 
     */
    static std::string getOption(const std::string& optionName, std::string defaultValue="");


  private:
    static char** environ_;
  };
  
}

#endif // NTA_ENV_HPP

