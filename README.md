
[![codecov](https://codecov.io/gh/usgs/libcomcat/branch/master/graph/badge.svg)](https://codecov.io/gh/usgs/libcomcat)

<!--- Comment to test syncing -->

# Introduction


libcomcat is a project designed to provide a Python equivalent to the ANSS ComCat search
<a href="https://earthquake.usgs.gov/fdsnws/event/1/">API</a>.  This includes a Python library
that provides various classes and functions wrapping around the ComCat API, and a number of command
line programs that use those:

* `findid` Find the ID of an event closest to input parameters (time, latitude, longitude). Also can provide the authoritative ID if an event id is provided.
*  `getcsv` Generate csv or Excel files with basic earthquake information.
*  `geteventhist` Generate csv or Excel files with a history of product submission for an event.
 * `getmags` Download all available magnitudes from all sources.
  * `getpager` Download information that represents the PAGER exposure and loss results.
  * `getphases` Generate csv or Excel files with phase information.
 * `getproduct` Download ComCat product contents (shakemap grids, origin quakeml, etc.)




# Installation and Dependencies

## Mac, Windows, and Linux Users

We recommend using either the Anaconda (https://docs.anaconda.com/anaconda/) or
Miniconda (https://conda.io/miniconda.html) Python distributions.  These both use the
conda packaging tool, which makes installation of dependencies much simpler. To install
either of those packages, see the instructions on the web pages for each.

### Installing

libcomcat *should* work with Python 3.5 and higher versions. It will *not* work with Python
2.7.  Fortunately, it is easy to install a 3.X version of Python within Anaconda or Miniconda. 
On a Linux or OSX system, open a Terminal window. On Windows systems, open a Powershell terminal. 
You'll use these command line windows to type the following commands:

 - `conda create -n comcat --channel conda-forge python=3`
 - `conda activate comcat`
 - `conda config --add channels conda-forge`
 - `conda install libcomcat`

### Uninstalling and Updating

To uninstall:

`conda remove libcomcat`

To update:

`conda update libcomcat`

## Motivation

libcomcat is a python wrapper for the Comprehensive Catalog (ComCat), which has a [web page interface](https://earthquake.usgs.gov/earthquakes/map/) and [API](https://earthquake.usgs.gov/fdsnws/event/1/). ComCat contains information in **Events** which contain **Products**. Products contain **Contents** in the form of files, maps, etc.

The ComCat interface is very user friendly, but does not support automation. The API supports automation, but limits the number of events that can be returned to 20,000. libcomcat uses the API in a way that allows for:
- Searches returning more than 20,000 eventsource
- Automation of product file downloads
- Extraction of information in product content files

## Documentation

Documentation can be found in the docs folder:
- [API Documentation](https://github.com/usgs/libcomcat/blob/master/docs/api.md)
- [Command Line Interface Documentation](https://github.com/usgs/libcomcat/blob/master/docs/cli.md)

Example Jupyter notebooks show how the API can be used to get and manipulate information from ComCat:
- [Classes Notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/Classes.ipynb)
- [Dataframes Notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/Dataframes.ipynb)
- [Detailed Event Notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/DetailEvent.ipynb)
- [Event History Notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/EventHistory.ipynb)
- [Magnitude Comparison Notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/ComparingMagnitudes.ipynb)
- [Phase and Magnitude Notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/PhasesAndMagnitudes.ipynb)
- [Search Notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/Search.ipynb)
