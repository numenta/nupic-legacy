# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

MODEL_PARAMS = {'aggregationInfo': {'days': 0,
                     'fields': [(u'timestamp', 'first'),
                                (u'kw_energy_consumption', 'sum')],
                     'hours': 1,
                     'microseconds': 0,
                     'milliseconds': 0,
                     'minutes': 0,
                     'months': 0,
                     'seconds': 0,
                     'weeks': 0,
                     'years': 0},
 'model': 'CLA',
 'modelParams': {'anomalyParams': {u'anomalyCacheRecords': None,
                                   u'autoDetectThreshold': None,
                                   u'autoDetectWaitRecords': None},
                 'clParams': {'alpha': 0.009222857190847474,
                              'clVerbosity': 0,
                              'regionName': 'CLAClassifierRegion',
                              'steps': '1'},
                 'inferenceType': 'TemporalMultiStep',
                 'sensorParams': {'encoders': {'_classifierInput': {'classifierOnly': True,
                                                                    'clipInput': True,
                                                                    'fieldname': 'kw_energy_consumption',
                                                                    'maxval': 53.0,
                                                                    'minval': 0.0,
                                                                    'n': 51,
                                                                    'name': '_classifierInput',
                                                                    'type': 'ScalarEncoder',
                                                                    'w': 21},
                                               u'kw_energy_consumption': {'clipInput': True,
                                                                          'fieldname': 'kw_energy_consumption',
                                                                          'maxval': 53.0,
                                                                          'minval': 0.0,
                                                                          'n': 42,
                                                                          'name': 'kw_energy_consumption',
                                                                          'type': 'ScalarEncoder',
                                                                          'w': 21},
                                               u'timestamp_dayOfWeek': None,
                                               u'timestamp_timeOfDay': {'fieldname': 'timestamp',
                                                                        'name': 'timestamp',
                                                                        'timeOfDay': (21,
                                                                                      4.142787757213304),
                                                                        'type': 'DateEncoder'},
                                               u'timestamp_weekend': {'fieldname': 'timestamp',
                                                                      'name': 'timestamp',
                                                                      'type': 'DateEncoder',
                                                                      'weekend': (21,
                                                                                  1)}},
                                  'sensorAutoReset': None,
                                  'verbosity': 0},
                 'spEnable': True,
                 'spParams': {'coincInputPoolPct': 0.8,
                              'columnCount': 2048,
                              'globalInhibition': 1,
                              'inputWidth': 0,
                              'maxBoost': 2.0,
                              'numActivePerInhArea': 40,
                              'seed': 1956,
                              'spVerbosity': 0,
                              'spatialImp': 'cpp',
                              'synPermActiveInc': 0.05,
                              'synPermConnected': 0.1,
                              'synPermInactiveDec': 0.09521570908737692},
                 'tpEnable': True,
                 'tpParams': {'activationThreshold': 12,
                              'cellsPerColumn': 32,
                              'columnCount': 2048,
                              'globalDecay': 0.0,
                              'initialPerm': 0.21,
                              'inputWidth': 2048,
                              'maxAge': 0,
                              'maxSegmentsPerCell': 128,
                              'maxSynapsesPerSegment': 32,
                              'minThreshold': 9,
                              'newSynapseCount': 20,
                              'outputType': 'normal',
                              'pamLength': 1,
                              'permanenceDec': 0.1,
                              'permanenceInc': 0.1,
                              'seed': 1960,
                              'temporalImp': 'cpp',
                              'verbosity': 0},
                 'trainSPNetOnlyIfRequested': False},
 'predictAheadTime': None,
 'version': 1}