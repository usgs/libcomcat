[![codecov](https://codecov.io/gh/usgs/libcomcat/branch/master/graph/badge.svg)](https://codecov.io/gh/usgs/libcomcat)


Introduction
------------

libcomcat is a project designed to provide a Python equivalent to the ANSS ComCat search 
<a href="http://comcat.cr.usgs.gov/fdsnws/event/1/">API</a>.  This includes a Python library
that provides various classes and functions wrapping around the ComCat API, and a number of command
line programs that use those:

 * `getproduct` Download ComCat product contents (shakemap grids, origin quakeml, etc.)
 * `getcsv` Generate csv or Excel files with basic earthquake information.
 * `getphases` Generate csv or Excel files with phase information.
 * `findid` Find the ID of an event closest to input time/lat/lon parameters.


Installation and Dependencies
-----------------------------

We recommend using either the Anaconda (https://docs.anaconda.com/anaconda/) or
Miniconda (https://conda.io/miniconda.html) Python distributions.  These both use the
conda packaging tool, which makes installation of dependencies much simpler. To install
either of those packages, see the instructions on the web pages for each.

libcomcat uses Python 3.6, so you will need a conda virtual environment with that
version of Python installed.  To create a conda virtual environment called "libcomcat"
with most of the necessary dependencies installed, do this:

`conda create -n libcomcat --channel conda-forge python=3.6 numpy obspy pandas xlrd xlwt openpyxl xlsxwriter`

Then to "activate" that environment, do:

`source activate libcomcat`

Then do:

`pip install git+git://github.com/usgs/earthquake-impact-utils.git`

`pip install git+git://github.com/usgs/libcomcat.git`

Uninstalling and Updating
-------------------------

To uninstall:

`pip uninstall libcomcat`

To update:

`pip install -U git+git://github.com/usgs/libcomcat.git`

Documentation
-------------

API and command line documentation can be found here:

http://usgs.github.io/libcomcat/

Sample usage can be found in the notebook:

https://github.com/usgs/libcomcat/blob/master/notebooks/libcomcat_examples.ipynb

