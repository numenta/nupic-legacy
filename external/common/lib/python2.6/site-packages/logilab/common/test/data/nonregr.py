try:
    enumerate = enumerate
except NameError:

    def enumerate(iterable):
        """emulates the python2.3 enumerate() function"""
        i = 0
        for val in iterable:
            yield i, val
            i += 1

def toto(value):
    for k, v in value:
        print v.get('yo')
