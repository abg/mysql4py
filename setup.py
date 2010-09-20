try:
        from setuptools import setup
except ImportError:
        from distutils.core import setup

version = '1.0'

setup(name='mysql4py',
      version=version,
      description="A pure python mysql driver",
      long_description="""\
      A Pure python MySQL Driver

      This is intended to be a clean implementation of the MySQL 4.1+
      protocol, supporting the PEP249 DBAPI and with backwards compatibility
      to python2.3.

      Additionally this software should run python3+ after patching by 2to3
      """,
      classifiers=[
        'Topic :: Database',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.3',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
      ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='MySQL dbapi',
      author='Andrew Garner',
      author_email='andrew.garner@rackspace.com',
      url='http://github.com/abg/mysql4py',
      license='BSD',
      packages=['mysql4py'],
)
