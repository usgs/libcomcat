from distutils.core import setup

setup(name='libcomcat',
      version='0.1dev',
      description='USGS ComCat search API in Python',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='',
      packages=['libcomcat'],
      scripts=['bin/findid',
               'bin/getcsv',
               'bin/getimpact',
               'bin/getmags',
               'bin/getpager',
               'bin/getphases',
               'bin/getproduct'],
      )
