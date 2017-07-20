# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
This is the base Configuration implementation. It provides for reading
configuration parameters from ``nupic-site.xml`` and ``nupic-default.xml``.
"""


from __future__ import with_statement

import os
import logging
from xml.etree import ElementTree

from pkg_resources import resource_string

# Turn on additional print statements
DEBUG = False
DEFAULT_CONFIG = "nupic-default.xml"
USER_CONFIG = "nupic-site.xml"
CUSTOM_CONFIG = "nupic-custom.xml"


def _getLogger():
  logger = logging.getLogger("com.numenta.nupic.tools.configuration_base")
  if DEBUG:
    logger.setLevel(logging.DEBUG)
  return logger



class Configuration(object):
  """ This class can be used to fetch NuPic configuration settings which are
  stored in one or more XML files.

  If the environment variable ``NTA_CONF_PATH`` is defined, then the
  configuration files are expected to be in the ``NTA_CONF_PATH`` search path,
  which is a ':' separated list of directories (on Windows the separator is a
  ';'). If ``NTA_CONF_PATH`` is not defined, then it is loaded via
  pkg_resources.
  """

  # Once we read in the properties, they are stored in this dict
  _properties = None

  # This stores the paths we search for config files. It can be modified through
  # the setConfigPaths() method.
  _configPaths = None

  # Any environment variable prefixed with this string serves as an override
  #  to property defined in the current configuration
  envPropPrefix = 'NTA_CONF_PROP_'


  @classmethod
  def getString(cls, prop):
    """ Retrieve the requested property as a string. If property does not exist,
    then KeyError will be raised.

    :param prop: (string) name of the property
    :raises: KeyError
    :returns: (string) property value
    """
    if cls._properties is None:
      cls._readStdConfigFiles()

    # Allow configuration properties to be overridden via environment variables
    envValue = os.environ.get("%s%s" % (cls.envPropPrefix,
                                        prop.replace('.', '_')), None)
    if envValue is not None:
      return envValue

    return cls._properties[prop]


  @classmethod
  def getBool(cls, prop):
    """ Retrieve the requested property and return it as a bool. If property
    does not exist, then KeyError will be raised. If the property value is
    neither 0 nor 1, then ValueError will be raised

    :param prop: (string) name of the property
    :raises: KeyError, ValueError
    :returns: (bool) property value
    """

    value = cls.getInt(prop)

    if value not in (0, 1):
      raise ValueError("Expected 0 or 1, but got %r in config property %s" % (
        value, prop))

    return bool(value)


  @classmethod
  def getInt(cls, prop):
    """ Retrieve the requested property and return it as an int. If property
    does not exist, then KeyError will be raised.

    :param prop: (string) name of the property
    :returns: (int) property value
    """

    return int(cls.getString(prop))


  @classmethod
  def getFloat(cls, prop):
    """ Retrieve the requested property and return it as a float. If property
    does not exist, then KeyError will be raised.

    :param prop: (string) name of the property
    :returns: (float) property value
    """

    return float(cls.getString(prop))


  @classmethod
  def get(cls, prop, default=None):
    """ Get the value of the given configuration property as string. This
    returns a string which is the property value, or the value of "default" arg.
    If the property is not found, use :meth:`getString` instead.

    .. note:: it's atypical for our configuration properties to be missing - a
     missing configuration property is usually a very serious error. Because
     of this, it's preferable to use one of the :meth:`getString`,
     :meth:`getInt`, :meth:`getFloat`, etc. variants instead of :meth:`get`.
     Those variants will raise KeyError when an expected property is missing.

    :param prop: (string) name of the property
    :param default: default value to return if property does not exist
    :returns: (string) property value, or default if the property does not exist
    """

    try:
      return cls.getString(prop)
    except KeyError:
      return default


  @classmethod
  def set(cls, prop, value):
    """ Set the value of the given configuration property.

    :param prop: (string) name of the property
    :param value: (object) value to set
    """

    if cls._properties is None:
      cls._readStdConfigFiles()

    cls._properties[prop] = str(value)


  @classmethod
  def dict(cls):
    """ Return a dict containing all of the configuration properties

    :returns: (dict) containing all configuration properties.
    """

    if cls._properties is None:
      cls._readStdConfigFiles()

    # Make a copy so we can update any current values obtained from environment
    #  variables
    result = dict(cls._properties)
    keys = os.environ.keys()
    replaceKeys = filter(lambda x: x.startswith(cls.envPropPrefix),
                         keys)
    for envKey in replaceKeys:
      key = envKey[len(cls.envPropPrefix):]
      key = key.replace('_', '.')
      result[key] = os.environ[envKey]

    return result


  @classmethod
  def readConfigFile(cls, filename, path=None):
    """ Parse the given XML file and store all properties it describes.

    :param filename: (string) name of XML file to parse (no path)
    :param path: (string) path of the XML file. If None, then use the standard
                  configuration search path.
    """
    properties = cls._readConfigFile(filename, path)

    # Create properties dict if necessary
    if cls._properties is None:
      cls._properties = dict()

    for name in properties:
      if 'value' in properties[name]:
        cls._properties[name] = properties[name]['value']


  @classmethod
  def _readConfigFile(cls, filename, path=None):
    """ Parse the given XML file and return a dict describing the file.

    :param filename: (string) name of XML file to parse (no path)
    :param path: (string) path of the XML file. If None, then use the standard
           configuration search path.
    :returns: (dict) with each property as a key and a dict of all the
           property's attributes as value
    """

    outputProperties = dict()

    # Get the path to the config files.
    if path is None:
      filePath = cls.findConfigFile(filename)
    else:
      filePath = os.path.join(path, filename)


    # ------------------------------------------------------------------
    # Read in the config file
    try:
      if filePath is not None:
        try:
          # Use warn since console log level is set to warning
          _getLogger().debug("Loading config file: %s", filePath)
          with open(filePath, 'r') as inp:
            contents = inp.read()
        except Exception:
          raise RuntimeError("Expected configuration file at %s" % filePath)
      else:
        # If the file was not found in the normal search paths, which includes
        # checking the NTA_CONF_PATH, we'll try loading it from pkg_resources.
        try:
          contents = resource_string("nupic.support", filename)
        except Exception as resourceException:
          # We expect these to be read, and if they don't exist we'll just use
          # an empty configuration string.
          if filename in [USER_CONFIG, CUSTOM_CONFIG]:
            contents = '<configuration/>'
          else:
            raise resourceException

      elements = ElementTree.XML(contents)

      if elements.tag != 'configuration':
        raise RuntimeError("Expected top-level element to be 'configuration' "
                           "but got '%s'" % (elements.tag))

      # ------------------------------------------------------------------
      # Add in each property found
      propertyElements = elements.findall('./property')

      for propertyItem in propertyElements:

        propInfo = dict()

        # Parse this property element
        propertyAttributes = list(propertyItem)
        for propertyAttribute in propertyAttributes:
          propInfo[propertyAttribute.tag] = propertyAttribute.text

        # Get the name
        name = propInfo.get('name', None)

        # value is allowed to be empty string
        if 'value' in propInfo and propInfo['value'] is None:
          value = ''
        else:
          value = propInfo.get('value', None)

          if value is None:
            if 'novalue' in propInfo:
              # Placeholder "novalue" properties are intended to be overridden
              # via dynamic configuration or another configuration layer.
              continue
            else:
              raise RuntimeError("Missing 'value' element within the property "
                                 "element: => %s " % (str(propInfo)))

        # The value is allowed to contain substitution tags of the form
        # ${env.VARNAME}, which should be substituted with the corresponding
        # environment variable values
        restOfValue = value
        value = ''
        while True:
          # Find the beginning of substitution tag
          pos = restOfValue.find('${env.')
          if pos == -1:
            # No more environment variable substitutions
            value += restOfValue
            break

          # Append prefix to value accumulator
          value += restOfValue[0:pos]

          # Find the end of current substitution tag
          varTailPos = restOfValue.find('}', pos)
          if varTailPos == -1:
            raise RuntimeError("Trailing environment variable tag delimiter '}'"
                               " not found in %r" % (restOfValue))

          # Extract environment variable name from tag
          varname = restOfValue[pos+6:varTailPos]
          if varname not in os.environ:
            raise RuntimeError("Attempting to use the value of the environment"
                               " variable %r, which is not defined" % (varname))
          envVarValue = os.environ[varname]

          value += envVarValue

          restOfValue = restOfValue[varTailPos+1:]


        # Check for errors
        if name is None:
          raise RuntimeError("Missing 'name' element within following property "
                             "element:\n => %s " % (str(propInfo)))

        propInfo['value'] = value
        outputProperties[name] = propInfo

      return outputProperties
    except Exception:
      _getLogger().exception("Error while parsing configuration file: %s.",
        filePath)
      raise


  @classmethod
  def clear(cls):
    """ Clear out the entire configuration.
    """

    cls._properties = None
    cls._configPaths = None


  @classmethod
  def findConfigFile(cls, filename):
    """ Search the configuration path (specified via the NTA_CONF_PATH
    environment variable) for the given filename. If found, return the complete
    path to the file.

    :param filename: (string) name of file to locate
    """

    paths = cls.getConfigPaths()
    for p in paths:
      testPath = os.path.join(p, filename)
      if os.path.isfile(testPath):
        return os.path.join(p, filename)


  @classmethod
  def getConfigPaths(cls):
    """ Return the list of paths to search for configuration files.

    :returns: (list) of paths
    """
    configPaths = []
    if cls._configPaths is not None:
      return cls._configPaths

    else:
      if 'NTA_CONF_PATH' in os.environ:
        configVar = os.environ['NTA_CONF_PATH']
        # Return as a list of paths
        configPaths = configVar.split(os.pathsep)

      return configPaths


  @classmethod
  def setConfigPaths(cls, paths):
    """ Modify the paths we use to search for configuration files.

    :param paths: (list) of paths to search for config files.
    """

    cls._configPaths = list(paths)


  @classmethod
  def _readStdConfigFiles(cls):
    """ Read in all standard configuration files

    """

    # Default one first
    cls.readConfigFile(DEFAULT_CONFIG)

    # Site specific one can override properties defined in default
    cls.readConfigFile(USER_CONFIG)
