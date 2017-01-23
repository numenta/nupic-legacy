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

'''
A fault tolerant loop
'''
import time
import smtplib
import sys

from datetime import datetime, timedelta
from email.mime.text import MIMEText



def patientLoop(logger, maxWaitExponent, finalErrorString, acceptableError,
                acceptErrorString, callable, argumentList, email = False,
                noReturn = False):
  '''
  logger                Logging object
  maxWaitExponent       2 ** maxWaitExponent defines max wait time
  finalErrorString      Msg to log if wait time expires
  acceptableError       The expected error for the loop
  acceptErrorString     Msg to log when expected error is encountered
  callable              The method/function to attempt in the loop
  arguments             Arguments to the method/function
  email                 An address to send a failure message to.
  '''

  exponent = 0
  lastErrorTime = datetime(1970,1,1)
  # Exit only on success (return) or exceed wait time (sys.exit(1))
  while True:
    if exponent > maxWaitExponent:
      logger.error(finalErrorString)
      if email:
        msg = MIMEText(logger.name)
        msg['Subject'] = 'URGENT - %s' % finalErrorString
        me = 'patientloop@numenta.com'
        you = email
        msg['From'] = me
        msg['To'] = you
        s = smtplib.SMTP('localhost')
        s.sendmail(me, [you], msg.as_string())
        s.quit()
      sys.exit(1)
    timeout = 2 ** exponent
    try:
      if noReturn:
        callable(*argumentList)
        return
      else:
        rv = callable(*argumentList)
        return rv
    except acceptableError:
      logger.warn(acceptErrorString)
      # Store the time we encountered this error
      errorTime = datetime.utcnow()
      '''
      If the time between this error and the last one is larger than the max
      time we are willing to time out, then we know there was a re-connection
      in between the errors. Reset our counter
      '''
      if errorTime - lastErrorTime > timedelta(seconds=(2**maxWaitExponent)):
        exponent = 0
      logger.info('Sleeping for %d seconds before attempting again ...' \
                  % timeout )
      time.sleep(timeout)
      # Store our error time for checking next time around
      lastErrorTime = errorTime
      # Back off on the wait time
      exponent += 1
