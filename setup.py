from distutils.core import setup

setup(name='libcomcat',
      version='0.1dev',
      description='USGS ComCat search API in Python',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='',
      packages=['libcomcat'],
      scripts = ['getcomcat.py','getcsv.py','getfixed.py','getellipse.py'],
)
