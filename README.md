[![codecov](https://codecov.io/gh/usgs/libcomcat/branch/master/graph/badge.svg)](https://codecov.io/gh/usgs/libcomcat)


# Introduction


libcomcat is a project designed to provide a Python equivalent to the ANSS ComCat search 
<a href="https://earthquake.usgs.gov/fdsnws/event/1/">API</a>.  This includes a Python library
that provides various classes and functions wrapping around the ComCat API, and a number of command
line programs that use those:

 * `getproduct` Download ComCat product contents (shakemap grids, origin quakeml, etc.)
 * `getcsv` Generate csv or Excel files with basic earthquake information.
 * `getphases` Generate csv or Excel files with phase information.
 * `findid` Find the ID of an event closest to input time/lat/lon parameters.


# Installation and Dependencies

We recommend using either the Anaconda (https://docs.anaconda.com/anaconda/) or
Miniconda (https://conda.io/miniconda.html) Python distributions.  These both use the
conda packaging tool, which makes installation of dependencies much simpler. To install
either of those packages, see the instructions on the web pages for each.

libcomcat has been tested most often with Python 3.5, but *should*
work with other Python 3.x versions. It will *not* work with Python
2.7!  For Anaconda (3.x) users, try the following:

- `conda install obspy`
- `pip install git+git://github.com/usgs/earthquake-impact-utils.git`
- `pip install git+git://github.com/usgs/libcomcat.git`

If you have Anaconda installed but your default environment is Python
2.7, you can create a new 3.x environment within the Anaconda
application to house libcomcat.

To create a conda virtual environment called "libcomcat" with
most of the necessary dependencies installed, do this:

 - `conda create -n comcat --channel conda-forge python=3.5 dateutil numpy openpyxl pandas xlrd xlsxwriter xlwt`
 - `source activate comcat`
 - `pip install git+git://github.com/usgs/earthquake-impact-utils.git`
 - `pip install git+git://github.com/usgs/libcomcat.git`

# Uninstalling and Updating

To uninstall:

`pip uninstall libcomcat`

To update:

`pip install -U git+git://github.com/usgs/libcomcat.git`

# Documentation

API and command line documentation can be found here:

http://usgs.github.io/libcomcat/

Sample API usage can be found in the notebook:

https://github.com/usgs/libcomcat/blob/master/notebooks/libcomcat_examples.ipynb

For consumers of phase data:
---------------------------

If you work in Python, you can use the read_phases() function that comes with libcomcat.

> from libcomcat.utils import read_phases

> event,phases = read_phases('us2000b3dm_phases.csv')

This function reads either CSV or Excel.

If you work in Matlab, we have provided a function, at the top level
of this repository, to read the CSV files.  To use it in your Matlab
environment, put the read_phases.m file in your Matlab path.  Below is
the help text for the function.

> read_phases  Read event and phase data from CSV files created by libcomcat getphases program.
> 
>   libcomcat is a set of tools available on GitHub for downloading various
>   types of data from the USGS earthquake Comprehensive Catalog, or ComCat.
>   getphases is one of those tools, and is documented here:
> 
>   http://usgs.github.io/libcomcat/programs/getphases.html
>  
>   (at command line) getphases . -i us2000b3dm --format=csv
>   [event,phases] = read_phases('./us2000b3dm_phases.csv') returns an
>   event structure, which consists of the following fields:
>    - id: USGS authoritative ComCat ID.
>    - time: Matlab datenum representing origin time.
>    - location: String describing location of the earthquake.
>    - latitude: Origin latitude.
>    - longitude: Origin longitude.
>    - depth: Origin depth.
>    - magnitude: Event magnitude.
>    - magtype: Magnitude type.
>    - url: ComCat URL where earthquake information can be found.
>    - Any remaining fields will contain moment tensor data, if available.
>      These fields will be preceded by moment tensor source and method.
>      For example, a moment tensor created by the NEIC using the W-phase
>      algorithm will have the following fields:
>      - us_Mww_mrr: Mrr moment tensor component.
>      - us_Mww_mtt: Mtt moment tensor component.
>      - us_Mww_mpp: Mpp moment tensor component.
>      - us_Mww_mrt: Mrt moment tensor component.
>      - us_Mww_mrp: Mrp moment tensor component.
>      - us_Mww_mtp: Mtp moment tensor component.
>      - us_Mww_np1_strike: Strike of the first nodal plane.
>      - us_Mww_np1_dip: Dip of the first nodal plane.
>      - us_Mww_np1_rake: Rake of the first nodal plane.
>      - us_Mww_np2_strike: Strike of the second nodal plane.
>      - us_Mww_np2_dip: Dip of the second nodal plane.
>      - us_Mww_np2_rake: Rake of the second nodal plane.
>  
>   and a Matlab table object, where rows consist of phase data
>   and columns are the following:
>    - Channel Network.Station.Channel.Location (NSCL) style station description.
>      ( '-'  indicates missing information)
>    - Distance Distance (kilometers) from epicenter to station.
>    - Azimuth Azimuth (degrees) from epicenter to station.
>    - Phase Name of the phase (Pn,Pg, etc.)
>    - ArrivalTime Pick arrival time (UTC).
>    - Status 'manual' or 'automatic'.
>    - Residual Arrival time residual.
>    - Weight Arrival weight.



