from distutils.core import setup
 
setup(
    name = 'nupic',
    packages = ['nupic'],
    version = '1.0.0',
    description = 'Numenta Platform for Intelligent Computing',
    author='Numenta',
    author_email='help@numenta.org',
    url='https://github.com/numenta/nupic',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence'
    ],
    long_description = """\
NuPIC is a library that provides the building blocks for online prediction systems. The library contains the Cortical Learning Algorithm (CLA), but also the Online Prediction Framework (OPF) that allows clients to build prediction systems out of encoders, models, and metrics.

For more information, see numenta.org or the NuPIC wiki (https://github.com/numenta/nupic/wiki).
"""
)
