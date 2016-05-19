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
 
You will also need to install *git*, a source code management tool, for your platform.

http://git-scm.com/downloads

You may need to open a new terminal window to ensure that the newly installed versions of python, pip and git
are in your path.

To install neicmap and neicio:

pip install git+git://github.com/usgs/neicmap.git

pip install git+git://github.com/usgs/neicio.git

To install this package:

pip install git+git://github.com/usgs/libcomcat.git

The last command will install getcomcat.py, getcsv.py, and getfixed.py in your path.  

Uninstalling and Updating
-------------------------

To uninstall:

pip uninstall libcomcat

To update:

pip install -U git+git://github.com/usgs/libcomcat.git

Application Programming Interface (API) Usage
----------------------------------------------------- 

The library code will be installed in
<PATH_TO_PYTHON>/lib/pythonX.Y/site-packages/libcomcat/.  Developers
should be able to use the functions in comcat.py and fixed.py by
importing them:

>>from libcomcat import comcat

>>from libcomcat import fixed

You can browse the API documentation for these two modules here:

<a href="http://usgs.github.io/libcomcat/">http://usgs.github.io/libcomcat/</a>.

Usage for getcomcat.py
--------
<pre>
usage: getcomcat.py [-h] [-o OUTPUTFOLDER] [-b lonmin lonmax latmin latmax]
                    [-s STARTTIME] [-e ENDTIME] [-a AFTER] [-m minmag maxmag]
                    [-c CATALOG] [-n CONTRIBUTOR] [-i EVENTID]
                    [-p PRODUCTPROPERTIES] [-t EVENTPROPERTIES] [-l] [-g]
                    PRODUCT [CONTENTLIST [CONTENTLIST ...]]

Download product content files from USGS ComCat.

    To download ShakeMap grid.xml files for a box around New Zealand during 2013:

    getcomcat.py shakemap grid.xml -o /home/user/newzealand -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01

    Note that when specifying a search box that crosses the -180/180 meridian, you simply specify longitudes
    as you would if you were not crossing that meridian.

    Note: Some product content files do not always have the same name, usually because they incorporate the event ID
    into the file name, such as with most of the files associated with the finite-fault product.  To download these files,
    you will need to input a unique fragment of the file name that can be matched in a search.

    For example, to retrieve all of the coulomb input files for the finite-fault product, you would construct your
    search like this:
    getcomcat.py finite-fault _coulomb.inp -o ~/tmp/chile -b -76.509 -49.804  -67.72 -17.427 -s 2007-01-01 -e 2016-05-01 -m 6.5 9.9

    To retrieve the moment rate function files, do this:
    getcomcat.py finite-fault .mr -o ~/tmp/chile -b -76.509 -49.804  -67.72 -17.427 -s 2007-01-01 -e 2016-05-01 -m 6.5 9.9


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
  -a AFTER, --after AFTER
                        Limit to events after specified time. YYYY-mm-dd or
                        YYYY-mm-ddTHH:MM:SS
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
  -g, --get-all-versions
                        Get products for every version of every event.
</pre>
Usage for getcsv.py
--------
<pre>
usage: getcsv.py [-h] [-b lonmin lonmax latmin latmax] [-r lat lon rmax]
                 [-s STARTTIME] [-e ENDTIME] [-m minmag maxmag] [-c CATALOG]
                 [-n CONTRIBUTOR] [-o]
                 [-l {usmww,usmwb,usmwc,usmwr,gcmtmwc,cimwr,ncmwr}] [-a] [-g]
                 [-f {csv,tab}] [-x] [-v] [-d]

Download basic earthquake information in line format (csv, tab, etc.).

    To download basic event information (time,lat,lon,depth,magnitude) and moment tensor components for a box around New Zealand
    during 2013:

    getcsv.py -o -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 > nz.csv

    To limit that search to only those events with a US Mww moment tensor solution:

    getcsv.py -o -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -l usmww > nz.csv

    To include all magnitudes (including source and type) for that same search, add the -g flag:

    getcsv.py -o -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -l usmww -g > nz.csv

    To print the number of events that would be returned from the above query, and the maximum number of events supported
    by ONE ComCat query*:

    getcsv.py -x -o -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01

    To download events with fractional days, use the ISO 8601 combined date time format (YYYY-mm-ddTHH:MM:SS, YYYY-mm-ddTHH:MM:SS.s):
    getcsv.py -s 2015-01-01T00:00:00 -e 2015-01-01T01:15:00

    NOTE: Any start or end time where only date is specified (YYYY-mm-dd) will be translated to the beginning of that day.
    Thus, a start time of "2015-01-01" becomes "2015-01-01T:00:00:00" and an end time of "2015-01-02"
    becomes ""2015-01-02T:00:00:00".

    Events which do not have a value for a given field (moment tensor components, for example), will have the string "nan" instead.

    Note that when specifying a search box that crosses the -180/180 meridian, you simply specify longitudes
    as you would if you were not crossing that meridian (i.e., lonmin=179, lonmax=-179).  The program will resolve the
    discrepancy.


    *Queries that exceed this ComCat limit ARE supported by this software, by breaking up one large request into a number of
    smaller ones.  However, large queries, when also configured to retrieve moment tensor parameters, nodal plane angles, or
    moment tensor type can take a very long time to download.  The author has tested queries just over 20,000 events, and it
    can take ~90 minutes to complete.  This delay is caused by the fact that when this program has to retrieve moment tensor
    parameters, nodal plane angles, or moment tensor type, it must open a URL for EACH event and parse the data it finds.
    If these parameters are not requested, then the same request will return in much less time (~10 minutes or less for a
    20,000 event query).


optional arguments:
  -h, --help            show this help message and exit
  -b lonmin lonmax latmin latmax, --bounds lonmin lonmax latmin latmax
                        Bounds to constrain event search [lonmin lonmax latmin
                        latmax]
  -r lat lon rmax, --radius lat lon rmax
                        Search radius in KM (use instead of bounding box)
  -s STARTTIME, --start-time STARTTIME
                        Start time for search (defaults to ~30 days ago).
                        YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-
                        ddTHH:MM:SS.s
  -e ENDTIME, --end-time ENDTIME
                        End time for search (defaults to current date/time).
                        YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-
                        ddTHH:MM:SS.s
  -m minmag maxmag, --mag-range minmag maxmag
                        Min/max (authoritative) magnitude to restrict search.
  -c CATALOG, --catalog CATALOG
                        Source catalog from which products derive (atlas,
                        centennial, etc.)
  -n CONTRIBUTOR, --contributor CONTRIBUTOR
                        Source contributor (who loaded product) (us, nc, etc.)
  -o, --get-moment-components
                        Also extract moment-tensor components (including type
                        and derived hypocenter) where available.
  -l {usmww,usmwb,usmwc,usmwr,gcmtmwc,cimwr,ncmwr}, --limit-type {usmww,usmwb,usmwc,usmwr,gcmtmwc,cimwr,ncmwr}
                        Only extract moment-tensor components from given type.
  -a, --get-focal-angles
                        Also extract focal-mechanism angles (strike,dip,rake)
                        where available.
  -g, --get-all-magnitudes
                        Extract all magnitudes (with sources),authoritative
                        listed first.
  -f {csv,tab}, --format {csv,tab}
                        Output format
  -x, --count           Just return the number of events in search and maximum
                        allowed.
  -v, --verbose         Print progress
  -d, --debug           Check the USGS development server (only valid inside
                        USGS network).
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

Usage for findid.py:
<pre>
usage: findid.py [-h] [-p time lat lon] [-r RADIUS] [-w WINDOW] [-f FILE] [-a]
                 [-u] [-v]

Find the id(s) of the closest earthquake to input parameters. 

    To print the authoritative id of the event closest in time and space inside a 100 km, 16 second window to "2015-03-29T23:48:31,-4.763,152.561":

    findid.py -p 2015-03-29T23:48:31 -4.763 152.561

    To repeat that query but with a custom distance/time window of 50km and 5 seconds:

    findid.py -r 50 -w 5 -p 2015-03-29T23:48:31 -4.763 152.561

    To print the authoritative id of the event closest in time and space to "2015-03-29T23:48:31,-4.763,152.561" AND
    the url of said event:

    findid.py -u -p 2015-03-29T23:48:31 -4.763 152.561

    To print all of the ids associated with the event closest to above:

    findid.py -a -p 2015-03-29T23:48:31 -4.763 152.561

    To print the id(s), time/distance deltas, and azimuth from input to nearest event:

    findid.py -v -p 2015-03-29T23:48:31 -4.763 152.561

    To find the ids for events found in a CSV file (time,lat,lon,...):
    (Create a file by doing the following: getcsv.py -s 2015-04-07 -e 2015-04-08T15:00:00 -m 4.0 5.5 | cut -f2,3,4,5,6,7 -d',' > eventlist.csv)
    ./findid.py -f eventlist.csv
    Output will be the input CSV data, with id added as the first column.

    If -u option is supplied, the url will be the second column.

    Notes:
     - The time format at the command line must be of the form "YYYY-MM-DDTHH:MM:SS".  The time format in an input csv file
     can be either :YYYY-MM-DDTHH:MM:SS" OR "YYYY-MM-DD HH:MM:SS".  This is because on the command line the argument parser 
     would be confused by the space between the date and the time, whereas in the csv file the input files are being split
     by commas.
     - Supplying the -a option with the -f option has no effect.
    

optional arguments:
  -h, --help            show this help message and exit
  -p time lat lon, --params time lat lon
                        Input time, lat and lon to use for search.
  -r RADIUS, --radius RADIUS
                        Change search radius from default of 100 km.
  -w WINDOW, --window WINDOW
                        Change time window of 16 seconds.
  -f FILE, --file FILE  Parse time,lat,lon from input csv file, which can have
                        a header row but must have time,lat,lon as first three
                        columns. Time format can be either YYYY-MM-DDTHH:MM:SS
                        OR YYYY-MM-DD HH:MM:SS. Output will have an "id"
                        column prepended, and a "url" column second (if -u
                        option selected), followed by the input columns of
                        data.
  -a, --all             Print all ids associated with event.
  -u, --url             Print URL associated with event.
  -v, --verbose         Print time/distance deltas, and azimuth from input
                        parameters to event.
</pre>

Usage for getellipse.py:
<pre>
usage: getellipse.py [-h] [-t alen blen clen azimuth plunge rotation]
                     [-r AAzim APlunge ALen BAzim BPlunge BLen CAzim CPlunge CLen]
                     [-q alen blen clen azimuth plunge rotation ndef stderr isfixed]
                     [-m AAzim APlunge ALen BAzim BPlunge BLen CAzim CPlunge CLen ndef stderr isfixed]

Convert between various representation of earthquake error ellipse.

    Tait-Bryan (QuakeML) representation to 3x3 matrix representation:

    getellipse.py -t 16.0 6.1 10.9 139.0 6.0 88.9075

    --------------------------------------------------------------
    SemiMajorAxis       : Azimuth 139.0 Plunge   6.0 Length  16.0
    SemiMinorAxis       : Azimuth 308.7 Plunge  83.9 Length   6.1
    SemiIntermediateAxis: Azimuth  48.9 Plunge   1.1 Length  10.9 
    -------------------------------------------------------------- 

    Tait-Bryan (QuakeML) representation to surface projection:

    getellipse.py -q 16.0 6.1 10.9 139.0 6.0 88.9075 95 0.76 0

    -------------------------------------------------------
    Surface Ellipse: Major:  13.7 Minor   9.4 Azimuth 319.1  
    -------------------------------------------------------

    3x3 Matrix representation to surface projection:

    getellipse.py -m 139.0 6.0 16.0 308.7 83.9 6.1 48.9 1.1 10.9 95 0.76 0

    -------------------------------------------------------
    Surface Ellipse: Major:  13.7 Minor   9.4 Azimuth 319.1
    -------------------------------------------------------
    
    3x3 matrix representation to Tait-Bryan (QuakeML) representation:

    getellipse.py -r 139.0 6.0 16.0 308.7 83.9 6.1 48.9 1.1 10.9

    -----------------------------------------------------------------------------
    SemiMajor Axis       : Azimuth 139.0 Plunge   6.0 Rotation  88.9 Length  16.0
    SemiMinor Axis       : Azimuth   nan Plunge   nan Rotation   nan Length   6.1
    SemiIntermediate Axis: Azimuth   nan Plunge   nan Rotation   nan Length  10.9
    -----------------------------------------------------------------------------
    

optional arguments:
  -h, --help            show this help message and exit
  -t alen blen clen azimuth plunge rotation, --tait2matrix alen blen clen azimuth plunge rotation
                        Convert Tait-Bryan error ellipse to 3x3 matrix
  -r AAzim APlunge ALen BAzim BPlunge BLen CAzim CPlunge CLen, --matrix2tait AAzim APlunge ALen BAzim BPlunge BLen CAzim CPlunge CLen
                        Convert 3x3 matrix error ellipse to Tait-Bryan
                        representation
  -q alen blen clen azimuth plunge rotation ndef stderr isfixed, --tait2surface alen blen clen azimuth plunge rotation ndef stderr isfixed
                        Project Tait-Bryan error ellipse to surface
  -m AAzim APlunge ALen BAzim BPlunge BLen CAzim CPlunge CLen ndef stderr isfixed, --matrix2surface AAzim APlunge ALen BAzim BPlunge BLen CAzim CPlunge CLen ndef stderr isfixed
                        Project 3x3 matrix error ellipse to surface
</pre>

Usage for getimpact.py:

<pre>
usage: getimpact.py [-h] eventID

Return the eventid,origin time,lat,lon,depth,magnitude,impact text for a given
input event ID. If no impact-text product is found, then the text returned
will be an empty string "". getimpact.py eventid Example: getimpact.py
us10003vki Returns: us10003vki,2015-11-07
17:37:49,8.5000,-71.5000,5.0,4.9,"Felt (V) at Ejido."

positional arguments:
  eventID     Event ID (i.e., us10003vki).

optional arguments:
  -h, --help  show this help message and exit
</pre>

libcomcat API for Developers
----------------------------
The functions that are most likely of interest to developers are in 
<a href="html/index.html">libcomcat/comcat</a>

