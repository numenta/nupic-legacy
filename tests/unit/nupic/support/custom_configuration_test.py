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

from copy import copy
import os
import shutil
from StringIO import StringIO
import sys
import tempfile
import unittest2 as unittest
import uuid
from pkg_resources import resource_filename

from mock import Mock, patch
from pkg_resources import resource_filename
from xml.parsers.expat import ExpatError
# ParseError not present in xml module for python2.6
try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError

import nupic
import nupic.support.configuration_custom as configuration

import configuration_test



class ConfigurationCustomTest(unittest.TestCase):

  def setUp(self):

    if "NTA_DYNAMIC_CONF_DIR" in os.environ:
      # Remove it to make sure our in-proc tests won't accidentally
      # mess with actual files
      oldNtaDynamicConfDir = os.environ["NTA_DYNAMIC_CONF_DIR"]
      del os.environ["NTA_DYNAMIC_CONF_DIR"]
      self.addCleanup(os.environ.update,
                      dict(NTA_DYNAMIC_CONF_DIR=oldNtaDynamicConfDir))

    self.files = dict()

    tmpDir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, tmpDir)


    with open(os.path.join(tmpDir, 'nupic-default.xml-unittest'), 'w') as fp:
      with open(resource_filename(__name__, 'conf/nupic-default.xml')) as inp:
        fp.write(inp.read())
        self.files['nupic-default.xml'] = fp.name

    with open(os.path.join(tmpDir, 'nupic-site.xml-unittest'), 'w') as fp:
      with open(resource_filename(__name__, 'conf/nupic-site.xml')) as inp:
        fp.write(inp.read())
        self.files['nupic-site.xml'] = fp.name

    with open(os.path.join(tmpDir, 'nupic-custom.xml'), 'w') as fp:
      with open(resource_filename(__name__, 'conf/nupic-custom.xml')) as inp:
        fp.write(inp.read())
        self.files['nupic-custom.xml'] = fp.name

    self.customParam = 'nupic.custom.hello'
    self.customValue = 'world'

    configuration.Configuration.clear()



  ####################################################################
  # Custom Configuration Tests
  # Todo: Share tests between two configuration_test files
  ####################################################################

  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testCustomFileCreated(self, findConfigFile, environ):
    environ.__getitem__.side_effect = dict(
      NTA_DYNAMIC_CONF_DIR=os.path.dirname(self.files['nupic-custom.xml'])).get
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.setCustomProperty('param', 'val')
    self.assertTrue(os.path.exists(self.files['nupic-custom.xml']))

  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGet(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>'+self.customParam+'</name>',
          '    <value>'+self.customValue+'</value>',
          '  </property>',
          '</configuration>')))

    self.assertEqual(
      configuration.Configuration.get(self.customParam),
      self.customValue)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testSetCustomProperty(self, findConfigFile, environ):
    environ.__getitem__.side_effect = dict(
      NTA_DYNAMIC_CONF_DIR=os.path.dirname(self.files['nupic-custom.xml'])).get
    environ.get.return_value = None
    configuration.Configuration.clear()
    findConfigFile.side_effect = self.files.get
    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>' + self.customParam + '</name>',
          '    <value>' + self.customValue + '</value>',
          '  </property>',
          '</configuration>')))
    configuration.Configuration.setCustomProperty('PersistProp', 'PersistVal')
    self.assertEqual(
      configuration.Configuration.get('PersistProp'),'PersistVal')
    configuration.Configuration.clear()
    self.assertEqual(
      configuration.Configuration.get('PersistProp'),'PersistVal')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testSetCustomProperties(self, findConfigFile, environ):
    environ.__getitem__.side_effect = dict(
      NTA_DYNAMIC_CONF_DIR=os.path.dirname(self.files['nupic-custom.xml'])).get
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>' + self.customParam + '</name>',
          '    <value>' + self.customValue + '</value>',
          '  </property>',
          '</configuration>')))

    configuration.Configuration.clear()
    originalProps = copy(configuration.Configuration.dict())

    configuration.Configuration.setCustomProperties(
      {'PersistProp' : 'PersistVal', 'apple' : 'pear'})

    expectedProps = {'PersistProp' : 'PersistVal', 'apple' : 'pear'}
    expectedProps.update(originalProps)
    self.assertEqual(configuration.Configuration.dict(), expectedProps)
    configuration.Configuration.clear()
    self.assertEqual(configuration.Configuration.dict(), expectedProps)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testDictWithTemp(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>param</name>',
          '    <value>value</value>',
          '  </property>',
          '  <property>',
          '    <name>param2</name>',
          '    <value>value2</value>',
          '  </property>',
          '</configuration>')))

    customDict = configuration.Configuration.dict()
    self.assertTrue('param' in customDict)
    self.assertTrue('param2' in customDict)
    self.assertEqual(customDict['param'], 'value')
    self.assertEqual(customDict['param2'], 'value2')

  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testCustomConfigOverrides(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    paramNames = configuration.Configuration.dict().keys()
    customValue = 'NewValue'
    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>'+paramNames[0]+'</name>',
          '    <value>'+customValue+'</value>',
          '  </property>',
          '</configuration>')))

    configuration.Configuration.clear()

    self.assertEqual(configuration.Configuration.get(paramNames[0]), \
      customValue)

  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testCustomConfigDict(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>CustomParam</name>',
          '    <value>CustomValue</value>',
          '  </property>',
          '</configuration>')))

    configuration.Configuration.clear()

    self.assertEqual(configuration.Configuration.get('CustomParam'), \
      'CustomValue')

  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testClearInvalidFile(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<foo/>')))

    configuration.Configuration.clear()

    with patch('sys.stderr', new_callable=StringIO):
      self.assertRaises(RuntimeError, configuration.Configuration.get, 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testSetInvalidFile(self, findConfigFile, environ):
    environ.__getitem__.side_effect = dict(
      NTA_DYNAMIC_CONF_DIR=os.path.dirname(self.files['nupic-custom.xml'])).get
    configuration.Configuration.clear()

    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<foo/>')))

    with patch('sys.stderr', new_callable=StringIO):
      with self.assertRaises(RuntimeError) as cm:
        configuration.Configuration.setCustomProperty('foo', 'value')
      self.assertIn("Expected top-level element to be 'configuration'",
        cm.exception.args[0])

    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join(('')))

    with patch('sys.stderr', new_callable=StringIO):
      with self.assertRaises(RuntimeError) as cm:
        configuration.Configuration.setCustomProperty('foo', 'value')
      self.assertIn("File contents of custom configuration is corrupt.",
        cm.exception.args[0])

    # NTA_CONF_PATH is not being mocked out in this test, so we have to mock out
    # findConfigFile to return the right path to the config file.
    findConfigFile.return_value = self.files['nupic-custom.xml']

    configuration.Configuration.resetCustomConfig()
    configuration.Configuration.setCustomProperty('foo', 'value')
    self.assertEqual(configuration.Configuration.getCustomDict(), {'foo': 'value'})




  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetCustomDict(self, findConfigFile, environ):
    environ.__getitem__.side_effect = dict(
      NTA_DYNAMIC_CONF_DIR=os.path.dirname(self.files['nupic-custom.xml'])).get
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-custom.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>CustomParam</name>',
          '    <value>CustomValue</value>',
          '  </property>',
          '</configuration>')))

    self.assertEqual(configuration.Configuration.getCustomDict(),
      dict(CustomParam='CustomValue'))

  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetCustomDictNoFile(self, findConfigFile, environ):
    environ.__getitem__.side_effect = dict(
      NTA_DYNAMIC_CONF_DIR=os.path.dirname(self.files['nupic-custom.xml'])).get
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.resetCustomConfig()

    self.assertEqual(configuration.Configuration.getCustomDict(), dict())
    del self.files['nupic-custom.xml']

  ###############################################
  # Replicated Tests From configuration_test.py
  ###############################################

  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetStringMissingRaisesKeyError(self, findConfigFileMock, environMock):
    findConfigFileMock.side_effect = self.files.get
    environMock.get.return_value = None
    configuration.Configuration.clear()
    with self.assertRaises(KeyError):
      configuration.Configuration.getString(uuid.uuid1().hex)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetString(self, findConfigFileMock, environMock):
    environMock.get.return_value = None
    findConfigFileMock.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.set('foo', 'bar')
    result = configuration.Configuration.getString('foo')
    self.assertEqual(result, 'bar')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetBoolMissingRaisesKeyError(self, findConfigFileMock, environMock):
    findConfigFileMock.side_effect = self.files.get
    environMock.get.return_value = None
    configuration.Configuration.clear()
    with self.assertRaises(KeyError):
      configuration.Configuration.getBool(uuid.uuid1().hex)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetBoolOutOfRangeRaisesValueError(self, findConfigFileMock,
                                            environMock):
    environMock.get.return_value = None
    findConfigFileMock.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.set('foobool2', '2')
    with self.assertRaises(ValueError):
      configuration.Configuration.getBool('foobool2')

    configuration.Configuration.set('fooboolneg1', '-1')
    with self.assertRaises(ValueError):
      configuration.Configuration.getBool('fooboolneg1')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetBool(self, findConfigFileMock, environMock):
    environMock.get.return_value = None
    findConfigFileMock.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.set('foobool0', '0')
    result = configuration.Configuration.getBool('foobool0')
    self.assertEqual(result, False)

    configuration.Configuration.set('foobool1', '1')
    result = configuration.Configuration.getBool('foobool1')
    self.assertEqual(result, True)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetIntMissingRaisesKeyError(self, findConfigFileMock, environMock):
    findConfigFileMock.side_effect = self.files.get
    environMock.get.return_value = None
    configuration.Configuration.clear()
    with self.assertRaises(KeyError):
      configuration.Configuration.getInt(uuid.uuid1().hex)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetInt(self, findConfigFileMock, environMock):
    environMock.get.return_value = None
    findConfigFileMock.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.set('fooint', '-127')
    result = configuration.Configuration.getInt('fooint')
    self.assertEqual(result, -127)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetFloatMissingRaisesKeyError(self, findConfigFileMock, environMock):
    findConfigFileMock.side_effect = self.files.get
    environMock.get.return_value = None
    configuration.Configuration.clear()
    with self.assertRaises(KeyError):
      configuration.Configuration.getFloat(uuid.uuid1().hex)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetFloat(self, findConfigFileMock, environMock):
    environMock.get.return_value = None
    findConfigFileMock.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.set('foofloat', '-127.65')
    result = configuration.Configuration.getFloat('foofloat')
    self.assertEqual(result, -127.65)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetMissingReturnsNone(self, findConfigFile, environ):
    findConfigFile.side_effect = self.files.get
    environ.get.return_value = None
    configuration.Configuration.clear()
    result = configuration.Configuration.get(str(uuid.uuid4()))
    self.assertTrue(result is None)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testSetAndGet(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.set('foo', 'bar')
    result = configuration.Configuration.get('foo')
    self.assertTrue(result == 'bar')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testDict(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.set('foo', 'bar')
    configuration.Configuration.set('apple', 'banana')
    result = configuration.Configuration.dict()
    self.assertTrue(isinstance(result, dict))
    self.assertTrue('foo' in result)
    self.assertTrue(result['foo'] == 'bar')
    self.assertTrue('apple' in result)
    self.assertTrue(result['apple'] == 'banana')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testDictReadsFilesFirstTime(self, findConfigFile,
                                  environ):  # pylint: disable=W0613
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    result = configuration.Configuration.dict()
    self.assertTrue(isinstance(result, dict))
    self.assertTrue(len(result) == 1, result)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testDictReplacesKeysFromEnvironment(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    key = str(uuid.uuid4())
    env = {'NTA_CONF_PROP_' + key: 'foo'}
    environ.keys.side_effect = env.keys
    environ.__getitem__.side_effect = env.__getitem__
    result = configuration.Configuration.dict()
    self.assertTrue(key in result)
    self.assertTrue(result[key] == 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testClear(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    configuration.Configuration.set('foo', 'bar')
    configuration.Configuration.set('apple', 'banana')
    self.assertTrue(configuration.Configuration.get('foo') == 'bar')
    self.assertTrue(configuration.Configuration.get('apple') == 'banana')
    configuration.Configuration.clear()
    self.assertTrue(configuration.Configuration.get('foo') is None)
    self.assertTrue(configuration.Configuration.get('apple') is None)


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testGetFromEnvironment(self, findConfigFile, environ):
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    key = str(uuid.uuid4())
    environ.get.side_effect = {'NTA_CONF_PROP_' + key: 'foo'}.get
    self.assertTrue(configuration.Configuration.get(key) == 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileFromPath(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()
    prefix, _, filename = self.files['nupic-default.xml'].rpartition(os.sep)
    configuration.Configuration.readConfigFile(filename, prefix)
    self.assertTrue(configuration.Configuration.get('dummy') == 'dummy value')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileUnexpectedElementAtRoot(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-default.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<foo/>')))

    with patch('sys.stderr', new_callable=StringIO):
      self.assertRaises(RuntimeError, configuration.Configuration.get, 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileMissingDocumentRoot(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-default.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>')))

    with patch('sys.stderr', new_callable=StringIO):
      self.assertRaises((ExpatError, ParseError), configuration.Configuration.get, 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileMissingNonPropertyConfigurationChildren(
      self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-default.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <foo>bar<baz/></foo>',
          '</configuration>')))

    self.assertEqual(configuration.Configuration.dict(), \
      dict(dummy='dummy value'))


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileEmptyValue(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-default.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>foo</name>',
          '  </property>',
          '</configuration>')))

    with patch('sys.stderr', new_callable=StringIO):
      self.assertRaises(Exception, configuration.Configuration.get, 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileEmptyNameAndValue(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-default.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name></name>',
          '    <value></value>',
          '  </property>',
          '</configuration>')))

    with patch('sys.stderr', new_callable=StringIO):
      self.assertRaises(RuntimeError, configuration.Configuration.get, 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileMissingEnvVars(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-default.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>foo</name>',
          '    <value>${env.foo}</value>',
          '  </property>',
          '</configuration>')))

    with patch('sys.stderr', new_callable=StringIO):
      self.assertRaises(RuntimeError, configuration.Configuration.get, 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileMalformedEnvReference(self, findConfigFile,
                                              environ):  # pylint: disable=W0613
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-default.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>foo</name>',
          '    <value>${env.foo</value>',
          '  </property>',
          '</configuration>')))

    with patch('sys.stderr', new_callable=StringIO):
      self.assertRaises(RuntimeError, configuration.Configuration.get, 'foo')


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testReadConfigFileEnvironmentOverride(self, findConfigFile, environ):
    environ.get.return_value = None
    findConfigFile.side_effect = self.files.get
    configuration.Configuration.clear()

    with open(self.files['nupic-default.xml'], 'w') as fp:
      fp.write('\n'.join((
          '<?xml version="1.0"?>',
          '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>',
          '<configuration>',
          '  <property>',
          '    <name>foo</name>',
          '    <value>${env.NTA_CONF_PROP_foo}</value>',
          '  </property>',
          '</configuration>')))

    env = {'NTA_CONF_PROP_foo': 'bar'}
    environ.__getitem__.side_effect = env.__getitem__
    environ.get.side_effect = env.get
    environ.__contains__.side_effect = env.__contains__

    result = configuration.Configuration.get('foo')
    self.assertEqual(result, 'bar')


  @patch.object(configuration.Configuration, 'getConfigPaths',
                spec=configuration.Configuration.getConfigPaths)
  def testFindConfigFile(self, getConfigPaths):
    prefix, _, filename = self.files['nupic-default.xml'].rpartition(os.sep)
    def replacePaths(**_):
      return [prefix]
    getConfigPaths.side_effect = replacePaths
    configuration.Configuration.clear()
    result = configuration.Configuration.findConfigFile(filename)
    self.assertTrue(result == self.files['nupic-default.xml'])
    getConfigPaths.assert_called_with()


  @patch.object(configuration.Configuration, 'getConfigPaths',
                spec=configuration.Configuration.getConfigPaths)
  def testFindConfigFileReturnsNoneForMissingFile(self, getConfigPaths):
    prefix, _, _ = self.files['nupic-default.xml'].rpartition(os.sep)
    def replacePaths(**_):
      return [prefix]
    getConfigPaths.side_effect = replacePaths
    configuration.Configuration.clear()
    result = configuration.Configuration.findConfigFile(str(uuid.uuid4()))
    self.assertTrue(result is None)
    getConfigPaths.assert_called_with()


  @patch.object(configuration.Configuration, '_configPaths',
                spec=configuration.Configuration._configPaths)
  @patch.object(configuration.os, 'environ', spec=dict)
  def testGetConfigPaths(
    self, environ, configPaths):  # pylint: disable=W0613
    result = configuration.Configuration.getConfigPaths()
    self.assertEqual(result, configPaths)


  @unittest.skip('NUP-2081')
  @patch.object(configuration.Configuration, '_configPaths',
                spec=configuration.Configuration._configPaths)
  @patch.object(configuration.os, 'environ', spec=dict)
  def testGetConfigPathsForNone(
      self, environ, configPaths):  # pylint: disable=W0613
    configuration.Configuration._configPaths = None  # pylint: disable=W0212
    result = configuration.Configuration.getConfigPaths()
    self.assertTrue(isinstance(result, list))
    self.assertListEqual(result, [resource_filename("nupic", 
                        os.path.join("config", "default"))])

  @patch.object(configuration.Configuration, '_configPaths',
                spec=configuration.Configuration._configPaths)
  @patch.object(configuration.os, 'environ', spec=dict)
  def testGetConfigPathsForNoneWithNTA_CONF_PATHInEnv(
      self, environ, configPaths):  # pylint: disable=W0613
    configuration.Configuration._configPaths = None  # pylint: disable=W0212
    env = {'NTA_CONF_PATH': ''}
    environ.__getitem__.side_effect = env.__getitem__
    environ.get.side_effect = env.get
    environ.__contains__.side_effect = env.__contains__
    result = configuration.Configuration.getConfigPaths()
    self.assertTrue(isinstance(result, list))
    self.assertEqual(len(result), 1)
    self.assertEqual(result[0], env['NTA_CONF_PATH'])

  def testSetConfigPathsForNoneWithNTA_CONF_PATHInEnv(self):
    paths = [Mock()]
    configuration.Configuration.setConfigPaths(paths)
    self.assertEqual(
        paths,
        configuration.Configuration._configPaths)  # pylint: disable=W0212


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testEmptyGetCustomDict(self, findConfigFile, environMock):
    findConfigFile.side_effect = self.files.get
    environMock.__getitem__.side_effect = dict(
      NTA_DYNAMIC_CONF_DIR=os.path.dirname(self.files['nupic-custom.xml'])).get
    configuration.Configuration.resetCustomConfig()
    self.assertEqual(configuration.Configuration.getCustomDict(), dict())


  @patch.object(configuration.os, 'environ', spec=dict)
  @patch.object(configuration.Configuration, 'findConfigFile',
                spec=configuration.Configuration.findConfigFile)
  def testConfiguration(self, findConfigFile, environ):
    configuration.Configuration.clear()
    findConfigFile.side_effect = self.files.get
    with open(self.files['nupic-default.xml'], 'w') as fp:
      with open(resource_filename(__name__, 'conf/testFile1.xml')) as inp:
        fp.write(inp.read())
    with open(self.files['nupic-site.xml'], 'w') as fp:
      with open(resource_filename(__name__, 'conf/testFile2.xml')) as inp:
        fp.write(inp.read())

    env = {'USER': 'foo', 'HOME': 'bar'}
    environ.__getitem__.side_effect = env.__getitem__
    environ.get.side_effect = env.get
    environ.__contains__.side_effect = env.__contains__
    environ.keys.side_effect = env.keys

    # Test the resulting configuration
    self.assertEqual(configuration.Configuration.get('database.host'),
                     'TestHost')
    self.assertEqual(configuration.Configuration.get('database.password'),
                     'pass')
    self.assertEqual(configuration.Configuration.get('database.emptypassword'),
                     '')
    self.assertEqual(configuration.Configuration.get('database.missingfield'),
                     None)
    self.assertEqual(configuration.Configuration.get('database.user'), 'root')

    expectedValue = 'foo'
    actualValue = configuration.Configuration.get(
        'var.environment.standalone.user')
    self.assertTrue(actualValue == expectedValue,
                    "expected %r, but got %r" % (expectedValue, actualValue))

    expectedValue = "The user " + os.environ['USER'] + " rocks!"
    actualValue = configuration.Configuration.get(
        'var.environment.user.in.the.middle')
    self.assertTrue(actualValue == expectedValue,
                    "expected %r, but got %r" % (expectedValue, actualValue))

    expectedValue = ("User " + os.environ['USER'] + " and home " +
                     os.environ['HOME'] + " in the middle")
    actualValue = configuration.Configuration.get(
        'var.environment.user.and.home.in.the.middle')
    self.assertTrue(actualValue == expectedValue,
                    "expected %r, but got %r" % (expectedValue, actualValue))

    env['NTA_CONF_PROP_database_host'] = 'FooBar'

    self.assertEqual(configuration.Configuration.get('database.host'), 'FooBar')
    allProps = configuration.Configuration.dict()
    self.assertTrue(allProps['database.host'] == 'FooBar')
    del env['NTA_CONF_PROP_database_host']
    environ.__getitem__.side_effect = env.__getitem__
    environ.get.side_effect = env.get
    environ.__contains__.side_effect = env.__contains__

    # Change a property
    configuration.Configuration.set('database.host', 'matrix')
    self.assertEqual(configuration.Configuration.get('database.host'), 'matrix')


  @patch.object(configuration.os, 'environ', spec=dict)
  def testConfiguration2(self, environ):
    configuration.Configuration.clear()

    tmpDir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, tmpDir)

    with open(os.path.join(tmpDir, 'nupic-default.xml'), 'w') as fp:
      with open(resource_filename(__name__, 'conf/testFile1.xml')) as inp:
        fp.write(inp.read())
    with open(os.path.join(tmpDir, 'nupic-site.xml'), 'w') as fp:
      with open(resource_filename(__name__, 'conf/testFile2.xml')) as inp:
        fp.write(inp.read())

    env = {
      'USER': 'foo',
      'HOME': 'bar',
      'NTA_CONF_PATH': tmpDir
    }
    environ.__getitem__.side_effect = env.__getitem__
    environ.get.side_effect = env.get
    environ.__contains__.side_effect = env.__contains__
    environ.keys.side_effect = env.keys

    # Test the resulting configuration
    self.assertEqual(configuration.Configuration.get('database.host'),
                     'TestHost')
    self.assertEqual(configuration.Configuration.get('database.password'),
                     'pass')
    self.assertEqual(
        configuration.Configuration.get('database.emptypassword'), '')
    self.assertEqual(configuration.Configuration.get('database.missingfield'),
                     None)
    self.assertEqual(configuration.Configuration.get('database.user'), 'root')

    expectedValue = 'foo'
    actualValue = configuration.Configuration.get(
        'var.environment.standalone.user')
    self.assertEqual(actualValue, expectedValue,
                     "expected %r, but got %r" % (expectedValue, actualValue))

    expectedValue = "The user " + os.environ['USER'] + " rocks!"
    actualValue = configuration.Configuration.get(
        'var.environment.user.in.the.middle')
    self.assertEqual(actualValue, expectedValue,
                     "expected %r, but got %r" % (expectedValue, actualValue))

    expectedValue = ("User " + os.environ['USER'] + " and home " +
      os.environ['HOME'] + " in the middle")
    actualValue = configuration.Configuration.get(
        'var.environment.user.and.home.in.the.middle')
    self.assertEqual(actualValue, expectedValue,
                     "expected %r, but got %r" % (expectedValue, actualValue))

    env['NTA_CONF_PROP_database_host'] = 'FooBar'

    self.assertEqual(configuration.Configuration.get('database.host'),
                     'FooBar')
    allProps = configuration.Configuration.dict()
    self.assertEqual(allProps['database.host'], 'FooBar')
    del env['NTA_CONF_PROP_database_host']

    # Change a property
    configuration.Configuration.set('database.host', 'matrix')
    self.assertEqual(configuration.Configuration.get('database.host'),
                     'matrix')

    configuration.Configuration.clear()

    tmpDir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, tmpDir)

    with open(os.path.join(tmpDir, 'nupic-default.xml'), 'w') as fp:
      with open(resource_filename(__name__, 'conf/testFile1.xml')) as inp:
        fp.write(inp.read())
    with open(os.path.join(tmpDir, 'nupic-site.xml'), 'w') as fp:
      with open(resource_filename(__name__, 'conf/testFile2.xml')) as inp:
        fp.write(inp.read())

    tmpDir2 = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, tmpDir2)

    with open(os.path.join(tmpDir2, 'nupic-site.xml'), 'w') as fp:
      with open(resource_filename(__name__, 'conf/testFile3.xml')) as inp:
        fp.write(inp.read())

    env['NTA_CONF_PATH'] = os.pathsep.join([tmpDir, tmpDir2])

    # Test the resulting configuration
    self.assertEqual(configuration.Configuration.get('database.host'),
                     'TestHost')
    self.assertEqual(configuration.Configuration.get('database.password'),
                     'pass')
    self.assertEqual(
        configuration.Configuration.get('database.emptypassword'), '')
    self.assertEqual(configuration.Configuration.get('database.missingfield'),
                     None)
    self.assertEqual(configuration.Configuration.get('database.user'),
                     'root')

    # Change a property
    configuration.Configuration.set('database.host', 'matrix')
    self.assertEqual(configuration.Configuration.get('database.host'),
                     'matrix')



if __name__ == '__main__':
  unittest.main(argv=[sys.argv[0], "--verbose"] + sys.argv[1:])
