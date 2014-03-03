Introduction
------------

libcomcat is a project designed to provide command line equivalents to the ANSS ComCat search 
<a href="http://comcat.cr.usgs.gov/fdsnws/event/1/">API</a>.  This code includes (so far):
 * Three scripts:
   * getcomcat.py A script to download ComCat product contents (shakemap grids, origin quakeml, etc.)
   * getcsv.py A script to generate csv or tab separated text files with basic earthquake information.
   * getfixed.py A script to generate text files in one of two fixed-width formats: ISF and EHDF.
 * Two code modules, libcomcat/comcat.py, and libcomcat/fixed.py, with functions supporting the above scripts.

Installation and Dependencies
-----------------------------

This package depends on numpy, the fundamental package for scientific computing with Python.
<a href="http://www.numpy.org/">http://www.numpy.org/</a>

and neicmap and neicio, part of an effort at the NEIC to create generally useful Python libraries from
the <a href="http://earthquake.usgs.gov/earthquakes/pager/">PAGER</a> source code.

The best way to install numpy is to use one of the Python distributions described here:

<a href="http://www.scipy.org/install.html">http://www.scipy.org/install.html</a>

Anaconda and Enthought distributions have been successfully tested with libcomcat.

Most of those distributions should include <em>pip</em>, a command line tool for installing and 
managing Python packages.  You will use pip to install the other dependencies and libcomcat itself.  
 
You may need to open a new terminal window to ensure that the newly installed versions of python and pip
are in your path.

To install neicmap and neicio:

pip install git+git://github.com/mhearne-usgs/neicmap.git

pip install git+git://github.com/mhearne-usgs/neicio.git

To install this package:

pip install git+git://github.com/usgs/libcomcat.git

The last command will install getcomcat.py, getcsv.py, and getfixed.py in your path.  The library code will be installed in 
<PATH_TO_PYTHON>/lib/pythonX.Y/site-packages/libcomcat/.  Developers should be able to use the functions in comcat.py and fixed.py by importing them:

>>from libcomcat import comcat
>>from libcomcat import fixed

Uninstalling and Updating
-------------------------

To uninstall:

pip uninstall libcomcat

To update:

pip install -U git+git://github.com/usgs/libcomcat.git


Usage for getcomcat.py
--------
<pre>
usage: getcomcat.py [-h] [-o OUTPUTFOLDER] [-b lonmin lonmax latmin latmax]
                    [-s STARTTIME] [-e ENDTIME] [-m minmag maxmag]
                    [-c CATALOG] [-n CONTRIBUTOR] [-i EVENTID]
                    [-p PRODUCTPROPERTIES] [-t EVENTPROPERTIES] [-l]
                    PRODUCT [CONTENTLIST [CONTENTLIST ...]]

Download product files from USGS ComCat. To download ShakeMap grid.xml files
for a box around New Zealand during 2013: getcomcat.py shakemap grid.xml -o
/home/user/newzealand -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e
2014-01-01 Note that when specifying a search box that crosses the -180/180
meridian, you simply specify longitudes as you would if you were not crossing
that meridian.

positional arguments:
  PRODUCT               The name of the desired product (shakemap, dyfi, etc.)
  CONTENTLIST           The names of the product contents (grid.xml,
                        stationlist.txt, etc.)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUTFOLDER, --output-folder OUTPUTFOLDER
                        Folder where output files should be written.
  -b lonmin lonmax latmin latmax, --bounds lonmin lonmax latmin latmax
                        Bounds to constrain event search [lonmin lonmax latmin
                        latmax]
  -s STARTTIME, --start-time STARTTIME
                        Start time for search (defaults to ~30 days ago).
                        YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS
  -e ENDTIME, --end-time ENDTIME
                        End time for search (defaults to current date/time).
                        YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS
  -m minmag maxmag, --mag-range minmag maxmag
                        Min/max magnitude to restrict search.
  -c CATALOG, --catalog CATALOG
                        Source catalog from which products derive (atlas,
                        centennial, etc.)
  -n CONTRIBUTOR, --contributor CONTRIBUTOR
                        Source contributor (who loaded product) (us, nc, etc.)
  -i EVENTID, --event-id EVENTID
                        Event ID from which to download product contents.
  -p PRODUCTPROPERTIES, --product-property PRODUCTPROPERTIES
                        Product property (reviewstatus:approved).
  -t EVENTPROPERTIES, --event-property EVENTPROPERTIES
                        Event property (alert:yellow, status:REVIEWED, etc.).
  -l, --list-url        Only list urls for contents in events that match
                        criteria.
</pre>
Usage for getcsv.py
--------
<pre>
usage: getcsv.py [-h] [-b lonmin lonmax latmin latmax] [-s STARTTIME]
                 [-e ENDTIME] [-m minmag maxmag] [-c CATALOG] [-n CONTRIBUTOR]
                 [-o] [-a] [-t] [-f {csv,tab}] [-v]

Download basic earthquake information in line format (csv, tab, etc.).

    To download basic event information (time,lat,lon,depth,magnitude) and moment tensor components for a box around New Zealand
    during 2013:

    getcsv.py -o -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 > nz.csv

    Events which do not have a value for a given field (moment tensor components, for example), will have the string "nan" instead.

    Note that when specifying a search box that crosses the -180/180 meridian, you simply specify longitudes
    as you would if you were not crossing that meridian.
    

optional arguments:
  -h, --help            show this help message and exit
  -b lonmin lonmax latmin latmax, --bounds lonmin lonmax latmin latmax
                        Bounds to constrain event search [lonmin lonmax latmin
                        latmax]
  -s STARTTIME, --start-time STARTTIME
                        Start time for search (defaults to ~30 days ago).
                        YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS
  -e ENDTIME, --end-time ENDTIME
                        End time for search (defaults to current date/time).
                        YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS
  -m minmag maxmag, --mag-range minmag maxmag
                        Min/max magnitude to restrict search.
  -c CATALOG, --catalog CATALOG
                        Source catalog from which products derive (atlas,
                        centennial, etc.)
  -n CONTRIBUTOR, --contributor CONTRIBUTOR
                        Source contributor (who loaded product) (us, nc, etc.)
  -o, --get-moment-components
                        Also extract moment-tensor components where available.
  -a, --get-focal-angles
                        Also extract focal-mechanism angles (strike,dip,rake)
                        where available.
  -t, --get-moment-type
                        Also extract moment type (Mww,Mwc, etc.) where
                        available
  -f {csv,tab}, --format {csv,tab}
                        Output format
  -v, --verbose         Print progress
</pre>

Usage for getfixed.py
--------
<pre>
usage: getfixed.py [-h] [-b lonmin lonmax latmin latmax]
                   [-r lat lon rmin rmax] [-s STARTTIME] [-e ENDTIME]
                   [-m minmag maxmag] [-c CATALOG] [-n CONTRIBUTOR]
                   [-i EVENTID]
                   {isf,ehdf}

Download earthquake information in a fixed-width (ISF or EHDF) format.

    Retrieving many events:

    getfixed.py isf -b -105.010 -104.090 37.049 37.475 -s 2014-01-01 -e 2014-01-24 > southern_colorado.isf

      
    This should print (to stderr) the ids of the events found in the search box, and then print (to stdout)
    the results in ISF format.

    Doing a radius search for multiple events:
    
    getfixed.py isf -r 35.786 -97.475 10 30 -s 2014-01-01 -e 2014-02-18 > oklahoma.isf

    Retrieving a single event:

    getfixed.py isf -i usb000m4lb > usb000m4lb.isf

    To retrieve events using a search box that spans the -180/180 meridian, simply specify longitudes
    as you would if you were not crossing that meridian:

    ./getfixed.py isf -b 177.605 -175.83 49.86 53.593 -s 2014-01-01 -e 2014-01-24 > aleutians.isf

    You can repeat these procedures for the EHDF format.

    The ISF format is described here:
    http://www.isc.ac.uk/standards/isf/

    The EHDF format is described here:
    ftp://hazards.cr.usgs.gov/weekly/ehdf.txt
    

positional arguments:
  {isf,ehdf}            Output data in ISF format

optional arguments:
  -h, --help            show this help message and exit
  -b lonmin lonmax latmin latmax, --bounds lonmin lonmax latmin latmax
                        Bounds to constrain event search [lonmin lonmax latmin
                        latmax]
  -r lat lon rmin rmax, --radius lat lon rmin rmax
                        Min/max search radius in KM (use instead of bounding
                        box)
  -s STARTTIME, --start-time STARTTIME
                        Start time for search (defaults to ~30 days ago).
                        YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS
  -e ENDTIME, --end-time ENDTIME
                        End time for search (defaults to current date/time).
                        YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS
  -m minmag maxmag, --mag-range minmag maxmag
                        Min/max magnitude to restrict search.
  -c CATALOG, --catalog CATALOG
                        Source catalog from which products derive (atlas,
                        centennial, etc.)
  -n CONTRIBUTOR, --contributor CONTRIBUTOR
                        Source contributor (who loaded product) (us, nc, etc.)
  -i EVENTID, --id EVENTID
                        Output data in EHDF format
</pre>

libcomcat API for Developers
----------------------------
The functions that are most likely of interest to developers are in 
<a href="html/index.html">libcomcat/comcat</a>

