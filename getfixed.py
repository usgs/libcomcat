#!/usr/bin/env python

#stdlib
import argparse
from datetime import datetime
from collections import OrderedDict
import os

#third party
from libcomcat.comcat import getPhaseData
from libcomcat import fixed

TIMEFMT = '%Y-%m-%dT%H:%M:%S'
DATEFMT = '%Y-%m-%d'

FMTDICT = OrderedDict()
FMTDICT['id'] = '%s'
FMTDICT['time'] = '%s'
FMTDICT['lat'] = '%.4f'
FMTDICT['lon'] = '%.4f'
FMTDICT['depth'] = '%.1f'
FMTDICT['mag'] = '%.1f'
FMTDICT['strike'] = '%.0f'
FMTDICT['dip'] = '%.0f'
FMTDICT['rake'] = '%.0f'
FMTDICT['mrr'] = '%g'
FMTDICT['mtt'] = '%g'
FMTDICT['mpp'] = '%g'
FMTDICT['mrt'] = '%g'
FMTDICT['mrp'] = '%g'
FMTDICT['mtp'] = '%g'
FMTDICT['type'] = '%s'

def getFormatTuple(event):
    tlist = []
    for key in FMTDICT.keys():
        if key not in event.keys():
            continue
        tlist.append(event[key])
    return tuple(tlist)

def getHeader(format,eventkeys):
    nuggets = []
    for key in FMTDICT.keys():
        if key not in eventkeys:
            continue
        nuggets.append(key)
    sep = ','
    if format == 'tab':
        sep = '\t'
    return sep.join(nuggets)

def getFormatString(format,keys):
    sep = ','
    if format == 'tab':
        sep = '\t'
    nuggets = []
    for key,value in FMTDICT.iteritems():
        if key in keys:
            nuggets.append(value)
    fmtstring = sep.join(nuggets)
    return fmtstring

def maketime(timestring):
    outtime = None
    try:
        outtime = datetime.strptime(timestring,TIMEFMT)
    except:
        try:
            outtime = datetime.strptime(timestring,DATEFMT)
        except:
            raise Exception,'Could not parse time or date from %s' % timestring
    return outtime

def makedict(dictstring):
    try:
        parts = dictstring.split(':')
        key = parts[0]
        value = parts[1]
        return {key:value}
    except:
        raise Exception,'Could not create a single key dictionary out of %s' % dictstring


if __name__ == '__main__':
    desc = '''Download earthquake information in a fixed-width (ISF or EHDF) format.

    Retrieving many events:

    getfixed.py isf -b -105.010 -104.090 37.049 37.475 -s 2014-01-01 -e 2014-01-24 > southern_colorado.isf

      
    This should print (to stderr) the ids of the events found in the search box, and then print (to stdout)
    the results in ISF format.

    Doing a radius search for multiple events (from 0 km to 30 km):
    
    getfixed.py isf -r 35.786 -97.475 0 30 -s 2014-01-01 -e 2014-02-18 > oklahoma.isf

    Retrieving a single event:

    getfixed.py isf -i usb000m4lb > usb000m4lb.isf

    To retrieve events using a search box that spans the -180/180 meridian, simply specify longitudes
    as you would if you were not crossing that meridian:

    getfixed.py isf -b 177.605 -175.83 49.86 53.593 -s 2014-01-01 -e 2014-01-24 > aleutians.isf

    You can repeat these procedures for the EHDF format.

    The ISF format is described here:
    http://www.isc.ac.uk/standards/isf/

    The EHDF format is described here:
    ftp://hazards.cr.usgs.gov/weekly/ehdf.txt
    '''
    parser = argparse.ArgumentParser(description=desc,formatter_class=argparse.RawDescriptionHelpFormatter)
    #optional arguments
    parser.add_argument('-b','--bounds', metavar=('lonmin','lonmax','latmin','latmax'),
                        dest='bounds', type=float, nargs=4,
                        help='Bounds to constrain event search [lonmin lonmax latmin latmax]')
    parser.add_argument('-r','--radius', dest='radius', metavar=('lat','lon','rmin','rmax'),type=float,
                        nargs=4,help='Min/max search radius in KM (use instead of bounding box)')
    parser.add_argument('-s','--start-time', dest='startTime', type=maketime,
                        help='Start time for search (defaults to ~30 days ago).  YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-e','--end-time', dest='endTime', type=maketime,
                        help='End time for search (defaults to current date/time).  YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-m','--mag-range', metavar=('minmag','maxmag'),dest='magRange', type=float,nargs=2,
                        help='Min/max magnitude to restrict search.')
    parser.add_argument('-c','--catalog', dest='catalog', 
                        help='Source catalog from which products derive (atlas, centennial, etc.)')
    parser.add_argument('-n','--contributor', dest='contributor', 
                        help='Source contributor (who loaded product) (us, nc, etc.)')
    parser.add_argument('format',choices=['isf','ehdf'],
                        help='Output data in ISF format')
    parser.add_argument('-i','--id', dest='eventid',
                        help='Output data in EHDF format')
    
    args = parser.parse_args()
    
    eventlist = getPhaseData(bounds=args.bounds,radius=args.radius,starttime=args.startTime,
                             endtime=args.endTime,magrange=args.magRange,catalog=args.catalog,
                             contributor=args.contributor,eventid=args.eventid)
    if not len(eventlist):
        sys.stderr.write('No events found.  Exiting.\n')
        sys.exit(0)
        
    for event in eventlist:
        if args.format == 'isf':
            text = event.renderISF()
        elif args.format == 'ehdf':
            text = event.renderEHDF()
        print text
        
