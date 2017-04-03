'encoders': {
    u'consumption':    {
        'fieldname': u'consumption',
        'resolution': 0.88,
        'seed': 1,
        'name': u'consumption',
        'type': 'RandomDistributedScalarEncoder',
        },

    'timestamp_timeOfDay': {   'fieldname': u'timestamp',
                               'name': u'timestamp_timeOfDay',
                               'timeOfDay': (21, 1),
                               'type': 'DateEncoder'},
    'timestamp_weekend': {   'fieldname': u'timestamp',
                             'name': u'timestamp_weekend',
                             'type': 'DateEncoder',
                             'weekend': 21}
}
