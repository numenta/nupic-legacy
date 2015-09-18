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

import logging
import platform
import traceback

from DBUtils import SteadyDB
from DBUtils.PooledDB import PooledDB

import pymysql
from nupic.support.configuration import Configuration


_MODULE_NAME = "nupic.database.Connection"


g_max_concurrency = None
g_max_concurrency_raise_exception = False
""" This flag controls a diagnostic feature for debugging unexpected concurrency
in acquiring ConnectionWrapper instances.

The value None (default) disables this feature.

enableConcurrencyChecks() and disableConcurrencyChecks() are the public API
functions for controlling this diagnostic feature.

When g_max_concurrency is exceeded, this module will log useful info (backtraces
of concurrent connection acquisitions). If g_max_concurrency_raise_exception is
true, it will also raise ConcurrencyExceededError with helpful information.
"""



class ConcurrencyExceededError(Exception):
  """ This exception is raised when g_max_concurrency is exceeded """
  pass



def enableConcurrencyChecks(maxConcurrency, raiseException=True):
  """ Enable the diagnostic feature for debugging unexpected concurrency in
  acquiring ConnectionWrapper instances.

  NOTE: This MUST be done early in your application's execution, BEFORE any
  accesses to ConnectionFactory or connection policies from your application
  (including imports and sub-imports of your app).

  Parameters:
  ----------------------------------------------------------------
  maxConcurrency:   A non-negative integer that represents the maximum expected
                      number of outstanding connections.  When this value is
                      exceeded, useful information will be logged and, depending
                      on the value of the raiseException arg,
                      ConcurrencyExceededError may be raised.
  raiseException:   If true, ConcurrencyExceededError will be raised when
                      maxConcurrency is exceeded.
  """
  global g_max_concurrency, g_max_concurrency_raise_exception

  assert maxConcurrency >= 0

  g_max_concurrency = maxConcurrency
  g_max_concurrency_raise_exception = raiseException
  return



def disableConcurrencyChecks():
  global g_max_concurrency, g_max_concurrency_raise_exception

  g_max_concurrency = None
  g_max_concurrency_raise_exception = False
  return



class ConnectionFactory(object):
  """ Database connection factory.

  WARNING: Minimize the scope of connection ownership to cover
    only the execution of SQL statements in order to avoid creating multiple
    outstanding SQL connections in gevent-based apps (e.g.,
    ProductionWorker) when polling code that calls timer.sleep()
    executes in the scope of an outstanding SQL connection, allowing a
    context switch to another greenlet that may also acquire an SQL connection.
    This is highly undesirable because SQL/RDS servers allow a limited number
    of connections. So, release connections before calling into any other code.
    Since connections are pooled by default, the overhead of calling
    ConnectionFactory.get() is insignificant.


  Usage Examples:

  # Add Context Manager (with ...) support for Jython/Python 2.5.x, if needed
  from __future__ import with_statement

  example1 (preferred):
      with ConnectionFactory.get() as conn:
        conn.cursor.execute("SELECT ...")

  example2 (if 'with' statement can't be used for some reason):
      conn = ConnectionFactory.get()
      try:
        conn.cursor.execute("SELECT ...")
      finally:
        conn.release()
  """


  @classmethod
  def get(cls):
    """ Acquire a ConnectionWrapper instance that represents a connection
    to the SQL server per nupic.cluster.database.* configuration settings.

    NOTE: caller is responsible for calling the ConnectionWrapper instance's
    release() method after using the connection in order to release resources.
    Better yet, use the returned ConnectionWrapper instance in a Context Manager
    statement for automatic invocation of release():
    Example:
        # If using Jython 2.5.x, first import with_statement at the very top of
        your script (don't need this import for Jython/Python 2.6.x and later):
        from __future__ import with_statement
        # Then:
        from nupic.database.Connection import ConnectionFactory
        # Then use it like this
        with ConnectionFactory.get() as conn:
          conn.cursor.execute("SELECT ...")
          conn.cursor.fetchall()
          conn.cursor.execute("INSERT ...")

    WARNING: DO NOT close the underlying connection or cursor as it may be
    shared by other modules in your process.  ConnectionWrapper's release()
    method will do the right thing.

    Parameters:
    ----------------------------------------------------------------
    retval:       A ConnectionWrapper instance. NOTE: Caller is responsible
                    for releasing resources as described above.
    """
    if cls._connectionPolicy is None:
      logger = _getLogger(cls)
      logger.info("Creating db connection policy via provider %r",
                  cls._connectionPolicyInstanceProvider)
      cls._connectionPolicy = cls._connectionPolicyInstanceProvider()

      logger.debug("Created connection policy: %r", cls._connectionPolicy)

    return cls._connectionPolicy.acquireConnection()


  @classmethod
  def close(cls):
    """ Close ConnectionFactory's connection policy. Typically, there is no need
    to call this method as the system will automatically close the connections
    when the process exits.

    NOTE: This method should be used with CAUTION. It is designed to be
    called ONLY by the code responsible for startup and shutdown of the process
    since it closes the connection(s) used by ALL clients in this process.
    """
    if cls._connectionPolicy is not None:
      cls._connectionPolicy.close()
      cls._connectionPolicy = None

    return


  @classmethod
  def setConnectionPolicyProvider(cls, provider):
    """ Set the method for ConnectionFactory to use when it needs to
    instantiate its database connection policy.

    NOTE: This method should be used with CAUTION. ConnectionFactory's default
    behavior should be adequate for all NuPIC code, and this method is provided
    primarily for diagnostics. It is designed to only be called by the code
    responsible for startup of the process since the provider method has no
    impact after ConnectionFactory's connection policy instance is instantiated.

    See ConnectionFactory._createDefaultPolicy

    Parameters:
    ----------------------------------------------------------------
    provider:     The method that instantiates the singleton database
                  connection policy to be used by ConnectionFactory class.
                  The method must be compatible with the following signature:
                    <DatabaseConnectionPolicyIface subclass instance> provider()
    """
    cls._connectionPolicyInstanceProvider = provider
    return


  @classmethod
  def _createDefaultPolicy(cls):
    """ [private] Create the default database connection policy instance

    Parameters:
    ----------------------------------------------------------------
    retval:            The default database connection policy instance
    """
    logger = _getLogger(cls)

    logger.debug(
      "Creating database connection policy: platform=%r; pymysql.VERSION=%r",
      platform.system(), pymysql.VERSION)

    if platform.system() == "Java":
      # NOTE: PooledDB doesn't seem to work under Jython
      # NOTE: not appropriate for multi-threaded applications.
      # TODO: this was fixed in Webware DBUtils r8228, so once
      #       we pick up a realease with this fix, we should use
      #       PooledConnectionPolicy for both Jython and Python.
      policy = SingleSharedConnectionPolicy()
    else:
      policy = PooledConnectionPolicy()

    return policy


  _connectionPolicy = None
  """ Our singleton database connection policy instance """

  _connectionPolicyInstanceProvider = _createDefaultPolicy
  """ This class variable holds the method that DatabaseConnectionPolicy uses
  to create the singleton database connection policy instance
  """
  # <-- End of class ConnectionFactory



class ConnectionWrapper(object):
  """ An instance of this class is returned by
  acquireConnection() methods of our database connection policy classes.
  """

  _clsNumOutstanding = 0
  """ For tracking the count of outstanding instances """

  _clsOutstandingInstances = set()
  """ tracks outstanding instances of this class while g_max_concurrency is
  enabled
  """

  def __init__(self, dbConn, cursor, releaser, logger):
    """
    Parameters:
    ----------------------------------------------------------------
    dbConn:         the underlying database connection instance
    cursor:         database cursor
    releaser:       a method to call to release the connection and cursor;
                      method signature:
                        None dbConnReleaser(dbConn, cursor)
    """

    global g_max_concurrency

    try:
      self._logger = logger

      self.dbConn = dbConn
      """ database connection instance """

      self.cursor = cursor
      """ Public cursor instance. Don't close it directly:  Connection.release()
      will do the right thing.
      """

      self._releaser = releaser

      self._addedToInstanceSet = False
      """ True if we added self to _clsOutstandingInstances """

      self._creationTracebackString = None
      """ Instance creation traceback string (if g_max_concurrency is enabled) """


      if g_max_concurrency is not None:
        # NOTE: must be called *before* _clsNumOutstanding is incremented
        self._trackInstanceAndCheckForConcurrencyViolation()


      logger.debug("Acquired: %r; numOutstanding=%s",
                   self, self._clsNumOutstanding)

    except:
      logger.exception("Exception while instantiating %r;", self)
      # Clean up and re-raise
      if self._addedToInstanceSet:
        self._clsOutstandingInstances.remove(self)
      releaser(dbConn=dbConn, cursor=cursor)
      raise
    else:
      self.__class__._clsNumOutstanding += 1

    return


  def __repr__(self):
    return "%s<dbConn=%r, dbConnImpl=%r, cursor=%r, creationTraceback=%r>" % (
      self.__class__.__name__, self.dbConn,
      getattr(self.dbConn, "_con", "unknown"),
      self.cursor, self._creationTracebackString,)


  def __enter__(self):
    """ [Context Manager protocol method] Permit a ConnectionWrapper instance
    to be used in a context manager expression (with ... as:) to facilitate
    robust release of resources (instead of try:/finally:/release()).  See
    examples in ConnectionFactory docstring.
    """
    return self


  def __exit__(self, exc_type, exc_val, exc_tb):
    """ [Context Manager protocol method] Release resources. """
    self.release()

    # Return False to allow propagation of exception, if any
    return False


  def release(self):
    """ Release the database connection and cursor

    The receiver of the Connection instance MUST call this method in order
    to reclaim resources
    """

    self._logger.debug("Releasing: %r", self)

    # Discard self from set of outstanding instances
    if self._addedToInstanceSet:
      try:
        self._clsOutstandingInstances.remove(self)
      except:
        self._logger.exception(
          "Failed to remove self from _clsOutstandingInstances: %r;", self)
        raise

    self._releaser(dbConn=self.dbConn, cursor=self.cursor)

    self.__class__._clsNumOutstanding -= 1
    assert self._clsNumOutstanding >= 0,  \
           "_clsNumOutstanding=%r" % (self._clsNumOutstanding,)

    self._releaser = None
    self.cursor = None
    self.dbConn = None
    self._creationTracebackString = None
    self._addedToInstanceSet = False
    self._logger = None
    return


  def _trackInstanceAndCheckForConcurrencyViolation(self):
    """ Check for concurrency violation and add self to
    _clsOutstandingInstances.

    ASSUMPTION: Called from constructor BEFORE _clsNumOutstanding is
    incremented
    """
    global g_max_concurrency, g_max_concurrency_raise_exception

    assert g_max_concurrency is not None
    assert self not in self._clsOutstandingInstances, repr(self)

    # Populate diagnostic info
    self._creationTracebackString = traceback.format_stack()

    # Check for concurrency violation
    if self._clsNumOutstanding >= g_max_concurrency:
      # NOTE: It's possible for _clsNumOutstanding to be greater than
      #  len(_clsOutstandingInstances) if concurrency check was enabled after
      #  unrelease allocations.
      errorMsg = ("With numOutstanding=%r, exceeded concurrency limit=%r "
                  "when requesting %r. OTHER TRACKED UNRELEASED "
                  "INSTANCES (%s): %r") % (
        self._clsNumOutstanding, g_max_concurrency, self,
        len(self._clsOutstandingInstances), self._clsOutstandingInstances,)

      self._logger.error(errorMsg)

      if g_max_concurrency_raise_exception:
        raise ConcurrencyExceededError(errorMsg)


    # Add self to tracked instance set
    self._clsOutstandingInstances.add(self)
    self._addedToInstanceSet = True

    return




class DatabaseConnectionPolicyIface(object):
  """ Database connection policy base class/interface.

  NOTE: We can't use the abc (abstract base class) module because
  Jython 2.5.x does not support abc
  """

  def close(self):
    """ Close the policy instance and its shared database connection. """
    raise NotImplementedError()


  def acquireConnection(self):
    """ Get a Connection instance.

    Parameters:
    ----------------------------------------------------------------
    retval:       A ConnectionWrapper instance.
                    Caller is responsible for calling the  ConnectionWrapper
                    instance's release() method to release resources.

    """
    raise NotImplementedError()



class SingleSharedConnectionPolicy(DatabaseConnectionPolicyIface):
  """ This connection policy maintains a single shared database connection.
  NOTE: this type of connection policy is not appropriate for muti-threaded
  applications."""


  def __init__(self):
    """ Consruct an instance. The instance's open() method must be
    called to make it ready for acquireConnection() calls.
    """
    self._logger = _getLogger(self.__class__)

    self._conn = SteadyDB.connect(** _getCommonSteadyDBArgsDict())

    self._logger.debug("Created %s", self.__class__.__name__)
    return


  def close(self):
    """ Close the policy instance and its shared database connection. """
    self._logger.info("Closing")
    if self._conn is not None:
      self._conn.close()
      self._conn = None
    else:
      self._logger.warning(
        "close() called, but connection policy was alredy closed")
    return


  def acquireConnection(self):
    """ Get a Connection instance.

    Parameters:
    ----------------------------------------------------------------
    retval:       A ConnectionWrapper instance. NOTE: Caller
                    is responsible for calling the  ConnectionWrapper
                    instance's release() method or use it in a context manager
                    expression (with ... as:) to release resources.
    """
    self._logger.debug("Acquiring connection")

    # Check connection and attempt to re-establish it if it died (this is
    #   what PooledDB does)
    self._conn._ping_check()
    connWrap = ConnectionWrapper(dbConn=self._conn,
                                 cursor=self._conn.cursor(),
                                 releaser=self._releaseConnection,
                                 logger=self._logger)
    return connWrap


  def _releaseConnection(self, dbConn, cursor):
    """ Release database connection and cursor; passed as a callback to
    ConnectionWrapper
    """
    self._logger.debug("Releasing connection")

    # Close the cursor
    cursor.close()

    # NOTE: we don't release the connection, since this connection policy is
    # sharing a single connection instance
    return



class PooledConnectionPolicy(DatabaseConnectionPolicyIface):
  """This connection policy maintains a pool of connections that are doled out
  as needed for each transaction.  NOTE: Appropriate for multi-threaded
  applications. NOTE: The connections are NOT shared concurrently between
  threads.
  """
  
  
  def __init__(self):
    """ Consruct an instance. The instance's open() method must be
    called to make it ready for acquireConnection() calls.
    """
    self._logger = _getLogger(self.__class__)

    self._logger.debug("Opening")
    self._pool = PooledDB(**_getCommonSteadyDBArgsDict())

    self._logger.info("Created %s", self.__class__.__name__)
    return


  def close(self):
    """ Close the policy instance and its database connection pool. """
    self._logger.info("Closing")

    if self._pool is not None:
      self._pool.close()
      self._pool = None
    else:
      self._logger.warning(
        "close() called, but connection policy was alredy closed")
    return


  def acquireConnection(self):
    """ Get a connection from the pool.

    Parameters:
    ----------------------------------------------------------------
    retval:       A ConnectionWrapper instance. NOTE: Caller
                    is responsible for calling the  ConnectionWrapper
                    instance's release() method or use it in a context manager
                    expression (with ... as:) to release resources.
    """
    self._logger.debug("Acquiring connection")

    dbConn = self._pool.connection(shareable=False)
    connWrap = ConnectionWrapper(dbConn=dbConn,
                                 cursor=dbConn.cursor(),
                                 releaser=self._releaseConnection,
                                 logger=self._logger)
    return connWrap


  def _releaseConnection(self, dbConn, cursor):
    """ Release database connection and cursor; passed as a callback to
    ConnectionWrapper
    """
    self._logger.debug("Releasing connection")

    # Close the cursor
    cursor.close()

    # ... then return db connection back to the pool
    dbConn.close()
    return



class PerTransactionConnectionPolicy(DatabaseConnectionPolicyIface):
  """This connection policy establishes/breaks a new connection for every
  high-level transaction (i.e., API call).

  NOTE: this policy is intended for debugging, as it is generally not performant
  to establish and tear down db connections for every API call.
  """
  
  
  def __init__(self):
    """ Consruct an instance. The instance's open() method must be
    called to make it ready for acquireConnection() calls.
    """
    self._logger = _getLogger(self.__class__)
    self._opened = True
    self._logger.info("Created %s", self.__class__.__name__)
    return


  def close(self):
    """ Close the policy instance. """
    self._logger.info("Closing")

    if self._opened:
      self._opened = False
    else:
      self._logger.warning(
        "close() called, but connection policy was alredy closed")

    return


  def acquireConnection(self):
    """ Create a Connection instance.

    Parameters:
    ----------------------------------------------------------------
    retval:       A ConnectionWrapper instance. NOTE: Caller
                    is responsible for calling the  ConnectionWrapper
                    instance's release() method or use it in a context manager
                    expression (with ... as:) to release resources.
    """
    self._logger.debug("Acquiring connection")

    dbConn = SteadyDB.connect(** _getCommonSteadyDBArgsDict())
    connWrap = ConnectionWrapper(dbConn=dbConn,
                                 cursor=dbConn.cursor(),
                                 releaser=self._releaseConnection,
                                 logger=self._logger)
    return connWrap


  def _releaseConnection(self, dbConn, cursor):
    """ Release database connection and cursor; passed as a callback to
    ConnectionWrapper
    """
    self._logger.debug("Releasing connection")

    # Close the cursor
    cursor.close()

    # ... then close the database connection
    dbConn.close()
    return



def _getCommonSteadyDBArgsDict():
  """ Returns a dictionary of arguments for DBUtils.SteadyDB.SteadyDBConnection
  constructor.
  """

  return dict(
      creator = pymysql,
      host = Configuration.get('nupic.cluster.database.host'),
      port = int(Configuration.get('nupic.cluster.database.port')),
      user = Configuration.get('nupic.cluster.database.user'),
      passwd = Configuration.get('nupic.cluster.database.passwd'),
      charset = 'utf8',
      use_unicode = True,
      setsession = ['SET AUTOCOMMIT = 1'])



def _getLogger(cls, logLevel=None):
  """ Gets a logger for the given class in this module
  """
  logger = logging.getLogger(
    ".".join(['com.numenta', _MODULE_NAME, cls.__name__]))

  if logLevel is not None:
    logger.setLevel(logLevel)

  return logger
