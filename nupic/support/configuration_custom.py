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

from __future__ import with_statement

from copy import copy
import errno
import logging
import os
import sys
import traceback
from xml.etree import ElementTree

from nupic.support.fshelpers import makeDirectoryFromAbsolutePath
from nupic.support.configuration_base import Configuration as ConfigurationBase


def _getLogger():
  return logging.getLogger("com.numenta.nupic.tools.configuration_custom")



class Configuration(ConfigurationBase):
  """ This class extends the ConfigurationBase implementation with the ability
  to read and write custom, persistent parameters. The custom settings will be
  stored in the nupic-custom.xml file.

  If the environment variable 'NTA_CONF_PATH' is defined, then the configuration
  files are expected to be in the NTA_CONF_PATH search path, which is a ':'
  separated list of directories. If NTA_CONF_PATH is not defined, then it is
  assumed to be NTA/conf/default (typically ~/nupic/current/conf/default).
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
    cls.setCustomProperties({propertyName : value})


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
            "configuration file: %s", e.errno, cls.getPath())
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
      with open(configFilePath, 'rb') as fp:
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
      with open(configFilePath,'w') as fp:
        fp.write(ElementTree.tostring(elements))
    except Exception, e:
      _getLogger().exception("Error while saving custom configuration "
        "properties %s in %s.", properties, configFilePath)
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
