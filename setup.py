from distutils.core import setup
import glob

setup(name='libcomcat',
      version='0.1dev',
      description='USGS ComCat search API in Python',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='',
      packages=['libcomcat'],
      package_data={
          'libcomcat':
          glob.glob('libcomcat/data/**', recursive=True)
      },
      scripts=['bin/findid',
               'bin/getcsv',
               'bin/getimpact',
               'bin/getmags',
               'bin/getpager',
               'bin/getphases',
               'bin/getproduct'],
      )
