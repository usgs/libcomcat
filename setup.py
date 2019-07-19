from distutils.core import setup
import os.path

setup(name='libcomcat',
      version='0.1dev',
      description='USGS ComCat search API in Python',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='',
      packages=['libcomcat'],
      package_data={
          'libcomcat':
          [os.path.join('data', 'ne_50m_admin_0_countries.prj'),
           os.path.join('data', 'ne_50m_admin_0_countries.dbf'),
           os.path.join('data', 'ne_50m_admin_0_countries.shp'),
           os.path.join('data', 'ne_50m_admin_0_countries.cpg'),
           os.path.join('data', 'ne_50m_admin_0_countries.shx'),
           ]
      },
      scripts=['bin/findid',
               'bin/getcsv',
               'bin/getimpact',
               'bin/getmags',
               'bin/getpager',
               'bin/getphases',
               'bin/geteventhist',
               'bin/getproduct'],
      )
