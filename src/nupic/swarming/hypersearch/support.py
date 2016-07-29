# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
This files contains support code for the hypersearch library.
Most of it is temporarily copied from nupic.support.
"""

from __future__ import with_statement

from copy import copy
import errno
import logging
import os
import sys
import traceback
from xml.etree import ElementTree
from pkg_resources import resource_string
import re
import keyword
import functools


### Enum

__IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
def __isidentifier(s):
  if s in keyword.kwlist:
      return False
  return __IDENTIFIER_PATTERN.match(s) is not None

def Enum(*args, **kwargs):
  """
  Utility function for creating enumerations in python

  Example Usage:
    >> Color = Enum("Red", "Green", "Blue", "Magenta")
    >> print Color.Red
    >> 0
    >> print Color.Green
    >> 1
    >> print Color.Blue
    >> 2
    >> print Color.Magenta
    >> 3
    >> Color.Violet
    >> 'violet'
    >> Color.getLabel(Color.Red)
    >> 'Red'
    >> Color.getLabel(2)
    >> 'Blue'
  """

  def getLabel(cls, val):
    """ Get a string label for the current value of the enum """
    return cls.__labels[val]

  def validate(cls, val):
    """ Returns True if val is a valid value for the enumeration """
    return val in cls.__values

  def getValues(cls):
    """ Returns a list of all the possible values for this enum """
    return list(cls.__values)

  def getLabels(cls):
    """ Returns a list of all possible labels for this enum """
    return list(cls.__labels.values())

  def getValue(cls, label):
    """ Returns value given a label """
    return cls.__labels[label]


  for arg in list(args)+kwargs.keys():
    if type(arg) is not str:
      raise TypeError("Enum arg {0} must be a string".format(arg))

    if not __isidentifier(arg):
      raise ValueError("Invalid enum value '{0}'. "\
                       "'{0}' is not a valid identifier".format(arg))

  #kwargs.update(zip(args, range(len(args))))
  kwargs.update(zip(args, args))
  newType = type("Enum", (object,), kwargs)

  newType.__labels = dict( (v,k) for k,v in kwargs.iteritems())
  newType.__values = set(newType.__labels.keys())
  newType.getLabel = functools.partial(getLabel, newType)
  newType.validate = functools.partial(validate, newType)
  newType.getValues = functools.partial(getValues, newType)
  newType.getLabels = functools.partial(getLabels, newType)
  newType.getValue = functools.partial(getValue, newType)

  return newType



def makeDirectoryFromAbsolutePath(absDirPath):
  """ Makes directory for the given directory path with default permissions.
  If the directory already exists, it is treated as success.

  absDirPath:   absolute path of the directory to create.

  Returns:      absDirPath arg

  Exceptions:         OSError if directory creation fails
  """

  assert os.path.isabs(absDirPath)

  try:
    os.makedirs(absDirPath)
  except OSError, e:
    if e.errno != os.errno.EEXIST:
      raise

  return absDirPath



# Turn on additional print statements
DEBUG = False
DEFAULT_CONFIG = "nupic-default.xml"
USER_CONFIG = "nupic-site.xml"
CUSTOM_CONFIG = "nupic-custom.xml"



def _getLoggerBase():
  logger = logging.getLogger("com.numenta.nupic.tools.configuration_base")
  if DEBUG:
    logger.setLevel(logging.DEBUG)
  return logger



class ConfigurationBase(object):
  """ This class can be used to fetch NuPic configuration settings which are
  stored in one or more XML files.

  If the environment variable 'NTA_CONF_PATH' is defined, then the configuration
  files are expected to be in the NTA_CONF_PATH search path, which is a ':'
  separated list of directories (on Windows the seperator is a ';').
  If NTA_CONF_PATH is not defined, then it is loaded via pkg_resources.

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

    Parameters:
    ----------------------------------------------------------------
    prop:        name of the property
    retval:      property value as a string
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

    Parameters:
    ----------------------------------------------------------------
    prop:        name of the property
    retval:      property value as bool
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

    Parameters:
    ----------------------------------------------------------------
    prop:        name of the property
    retval:      property value as int
    """

    return int(cls.getString(prop))

  @classmethod
  def getFloat(cls, prop):
    """ Retrieve the requested property and return it as a float. If property
    does not exist, then KeyError will be raised.

    Parameters:
    ----------------------------------------------------------------
    prop:        name of the property
    retval:      property value as float
    """

    return float(cls.getString(prop))

  @classmethod
  def get(cls, prop, default=None):
    """ Get the value of the given configuration property as string. This
    returns a string which is the property value, or the value of "default" arg
    if the property is not found. Use Configuration.getString() instead.

    NOTE: it's atypical for our configuration properties to be missing - a
     missing configuration property is usually a very serious error. Because
     of this, it's preferable to use one of the getString, getInt, getFloat,
     etc. variants instead of get(). Those variants will raise KeyError when
     an expected property is missing.

    Parameters:
    ----------------------------------------------------------------
    prop:        name of the property
    default:     default value to return if property does not exist
    retval:      property value (as a string), or default if the property does
                  not exist.
    """

    try:
      return cls.getString(prop)
    except KeyError:
      return default

  @classmethod
  def set(cls, prop, value):
    """ Set the value of the given configuration property.

    Parameters:
    ----------------------------------------------------------------
    prop:        name of the property
    value:       value to set
    """

    if cls._properties is None:
      cls._readStdConfigFiles()

    cls._properties[prop] = str(value)

  @classmethod
  def dict(cls):
    """ Return a dict containing all of the configuration properties

    Parameters:
    ----------------------------------------------------------------
    retval:      dict containing all configuration properties.
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

    Parameters:
    ----------------------------------------------------------------
    filename:  name of XML file to parse (no path)
    path:      path of the XML file. If None, then use the standard
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

    Parameters:
    ----------------------------------------------------------------
    filename:  name of XML file to parse (no path)
    path:      path of the XML file. If None, then use the standard
                  configuration search path.
    retval:    returns a dict with each property as a key and a dict of all
               the property's attributes as value
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
          _getLoggerBase().debug("Loading config file: %s", filePath)
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
            raise RuntimeError(
              "Trailing environment variable tag delimiter '}'"
              " not found in %r" % (restOfValue))

          # Extract environment variable name from tag
          varname = restOfValue[pos + 6:varTailPos]
          if varname not in os.environ:
            raise RuntimeError("Attempting to use the value of the environment"
                               " variable %r, which is not defined" % (
                               varname))
          envVarValue = os.environ[varname]

          value += envVarValue

          restOfValue = restOfValue[varTailPos + 1:]

        # Check for errors
        if name is None:
          raise RuntimeError(
            "Missing 'name' element within following property "
            "element:\n => %s " % (str(propInfo)))

        propInfo['value'] = value
        outputProperties[name] = propInfo

      return outputProperties
    except Exception:
      _getLoggerBase().exception("Error while parsing configuration file: %s.",
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

    Parameters:
    ----------------------------------------------------------------
    filename:  name of file to locate
    """

    paths = cls.getConfigPaths()
    for p in paths:
      testPath = os.path.join(p, filename)
      if os.path.isfile(testPath):
        return os.path.join(p, filename)

  @classmethod
  def getConfigPaths(cls):
    """ Return the list of paths to search for configuration files.

    Parameters:
    ----------------------------------------------------------------
    retval:    list of paths.
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

    Parameters:
    ----------------------------------------------------------------
    paths:   list of paths to search for config files.
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



def _getLogger():
  return logging.getLogger("com.numenta.nupic.tools.configuration_custom")



class Configuration(ConfigurationBase):
  """ This class extends the ConfigurationBase implementation with the ability
  to read and write custom, persistent parameters. The custom settings will be
  stored in the nupic-custom.xml file.

  If the environment variable 'NTA_CONF_PATH' is defined, then the configuration
  files are expected to be in the NTA_CONF_PATH search path, which is a ':'
  separated list of directories (on Windows the seperator is a ';').
  If NTA_CONF_PATH is not defined, then it is assumed to be NTA/conf/default
  (typically ~/nupic/current/conf/default).
  """

  @classmethod
  def getCustomDict(cls):
    """ Return a dict containing all custom configuration properties

    Parameters:
    ----------------------------------------------------------------
    retval:      dict containing all custom configuration properties.
    """
    return _CustomConfigurationFileWrapper.getCustomDict()

  @classmethod
  def setCustomProperty(cls, propertyName, value):
    """ Set a single custom setting and persist it to the custom
    configuration store.

    Parameters:
    ----------------------------------------------------------------
    propertyName: string containing the name of the property to get
    value: value to set the property to
    """
    cls.setCustomProperties({propertyName: value})

  @classmethod
  def setCustomProperties(cls, properties):
    """ Set multiple custom properties and persist them to the custom
    configuration store.

    Parameters:
    ----------------------------------------------------------------
    properties: a dict of property name/value pairs to set
    """
    _getLogger().info("Setting custom configuration properties=%r; caller=%r",
                      properties, traceback.format_stack())

    _CustomConfigurationFileWrapper.edit(properties)

    for propertyName, value in properties.iteritems():
      cls.set(propertyName, value)

  @classmethod
  def clear(cls):
    """ Clear all configuration properties from in-memory cache, but do NOT
    alter the custom configuration file. Used in unit-testing.
    """
    # Clear the in-memory settings cache, forcing reload upon subsequent "get"
    # request.
    super(Configuration, cls).clear()

    # Reset in-memory custom configuration info.
    _CustomConfigurationFileWrapper.clear(persistent=False)

  @classmethod
  def resetCustomConfig(cls):
    """ Clear all custom configuration settings and delete the persistent
    custom configuration store.
    """
    _getLogger().info("Resetting all custom configuration properties; "
                      "caller=%r", traceback.format_stack())

    # Clear the in-memory settings cache, forcing reload upon subsequent "get"
    # request.
    super(Configuration, cls).clear()

    # Delete the persistent custom configuration store and reset in-memory
    # custom configuration info
    _CustomConfigurationFileWrapper.clear(persistent=True)

  @classmethod
  def loadCustomConfig(cls):
    """ Loads custom configuration settings from their persistent storage.
    DO NOT CALL THIS: It's typically not necessary to call this method
    directly - see NOTE below.

    NOTE: this method exists *solely* for the benefit of prepare_conf.py, which
    needs to load configuration files selectively.
    """
    cls.readConfigFile(_CustomConfigurationFileWrapper.customFileName)

  @classmethod
  def _readStdConfigFiles(cls):
    """ Intercept the _readStdConfigFiles call from our base config class to
    read in base and custom configuration settings.
    """
    super(Configuration, cls)._readStdConfigFiles()

    cls.loadCustomConfig()


class _CustomConfigurationFileWrapper(object):
  """
  Private class to handle creation, deletion and editing of the custom
  configuration file used by this implementation of Configuration.

  Supports persistent changes to nupic-custom.xml configuration file.

  This class only applies changes to the local instance.
  For cluster wide changes see nupic-services.py or nupic.cluster.NupicServices
  """
  # Name of the custom xml file to be created
  customFileName = 'nupic-custom.xml'

  # Stores the path to the file
  # If none, findConfigFile is used to find path to file; defaults to
  # NTA_CONF_PATH[0]
  _path = None

  @classmethod
  def clear(cls, persistent=False):
    """ If persistent is True, delete the temporary file

    Parameters:
    ----------------------------------------------------------------
    persistent: if True, custom configuration file is deleted
    """
    if persistent:
      try:
        os.unlink(cls.getPath())
      except OSError, e:
        if e.errno != errno.ENOENT:
          _getLogger().exception("Error %s while trying to remove dynamic " \
                                 "configuration file: %s", e.errno,
                                 cls.getPath())
          raise
    cls._path = None

  @classmethod
  def getCustomDict(cls):
    """ Returns a dict of all temporary values in custom configuration file

    """
    if not os.path.exists(cls.getPath()):
      return dict()

    properties = Configuration._readConfigFile(os.path.basename(
      cls.getPath()), os.path.dirname(cls.getPath()))

    values = dict()
    for propName in properties:
      if 'value' in properties[propName]:
        values[propName] = properties[propName]['value']

    return values

  @classmethod
  def edit(cls, properties):
    """ Edits the XML configuration file with the parameters specified by
    properties

    Parameters:
    ----------------------------------------------------------------
    properties: dict of settings to be applied to the custom configuration store
                 (key is property name, value is value)
    """
    copyOfProperties = copy(properties)

    configFilePath = cls.getPath()

    try:
      with open(configFilePath, 'r') as fp:
        contents = fp.read()
    except IOError, e:
      if e.errno != errno.ENOENT:
        _getLogger().exception("Error %s reading custom configuration store "
                               "from %s, while editing properties %s.",
                               e.errno, configFilePath, properties)
        raise
      contents = '<configuration/>'

    try:
      elements = ElementTree.XML(contents)
      ElementTree.tostring(elements)
    except Exception, e:
      # Raising error as RuntimeError with custom message since ElementTree
      # exceptions aren't clear.
      msg = "File contents of custom configuration is corrupt.  File " \
            "location: %s; Contents: '%s'. Original Error (%s): %s." % \
            (configFilePath, contents, type(e), e)
      _getLogger().exception(msg)
      raise RuntimeError(msg), None, sys.exc_info()[2]

    if elements.tag != 'configuration':
      e = "Expected top-level element to be 'configuration' but got '%s'" % \
          (elements.tag)
      _getLogger().error(e)
      raise RuntimeError(e)

    # Apply new properties to matching settings in the custom config store;
    # pop matching properties from our copy of the properties dict
    for propertyItem in elements.findall('./property'):
      propInfo = dict((attr.tag, attr.text) for attr in propertyItem)
      name = propInfo['name']
      if name in copyOfProperties:
        foundValues = propertyItem.findall('./value')
        if len(foundValues) > 0:
          foundValues[0].text = str(copyOfProperties.pop(name))
          if not copyOfProperties:
            break
        else:
          e = "Property %s missing value tag." % (name,)
          _getLogger().error(e)
          raise RuntimeError(e)

    # Add unmatched remaining properties to custom config store
    for propertyName, value in copyOfProperties.iteritems():
      newProp = ElementTree.Element('property')
      nameTag = ElementTree.Element('name')
      nameTag.text = propertyName
      newProp.append(nameTag)

      valueTag = ElementTree.Element('value')
      valueTag.text = str(value)
      newProp.append(valueTag)

      elements.append(newProp)

    try:
      makeDirectoryFromAbsolutePath(os.path.dirname(configFilePath))
      with open(configFilePath, 'w') as fp:
        fp.write(ElementTree.tostring(elements))
    except Exception, e:
      _getLogger().exception("Error while saving custom configuration "
                             "properties %s in %s.", properties,
                             configFilePath)
      raise

  @classmethod
  def _setPath(cls):
    """ Sets the path of the custom configuration file
    """
    cls._path = os.path.join(os.environ['NTA_DYNAMIC_CONF_DIR'],
                             cls.customFileName)

  @classmethod
  def getPath(cls):
    """ Get the path of the custom configuration file
    """
    if cls._path is None:
      cls._setPath()
    return cls._path
