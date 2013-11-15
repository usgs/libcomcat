Introduction
------------

libcomcat is a project provide command line equivalents to the NEIC ComCat search API.  This 
code includes (so far):
 * Two scripts:
   * getcomcat.py A script to download ComCat product contents (shakemap grids, origin quakeml, etc.)
   * getcsv.py A script to generate csv or tab separated text files with basic earthquake information.
 * One code module, libcomcat/comcat.py, with functions supporting the above scripts.

Usage for getcomcat.py
--------
<pre>
usage: getcomcat.py [-h] [-o OUTPUTFOLDER] [-b lonmin lonmax latmin latmax]
                    [-s STARTTIME] [-e ENDTIME] [-m minmag maxmag]
                    [-c CATALOG] [-n CONTRIBUTOR] [-v EVENTID]
                    [-p PRODUCTPROPERTIES] [-t EVENTPROPERTIES] [-l]
                    PRODUCT [CONTENTLIST [CONTENTLIST ...]]

Download product files from USGS ComCat.

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
  -v EVENTID, --event-id EVENTID
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