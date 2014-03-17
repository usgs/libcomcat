#!/usr/bin/env python

#stdlib
import argparse
from datetime import datetime,timedelta
from collections import OrderedDict
import os
import sys

#third party
from libcomcat.comcat import getEventData,getEventCount,getTimeSegments

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

def main(args):
    if args.getCount:
        nevents,maxevents = getEventCount(bounds=args.bounds,radius=args.radius,
                                          starttime=args.startTime,endtime=args.endTime,
                                          magrange=args.magRange,catalog=args.catalog,
                                          contributor=args.contributor)
        fmt = '%i %i'
        print fmt % (nevents,maxevents)
        sys.exit(0)

    #actually get the data - do a count first to make sure our request isn't too large.
    nevents,maxevents = getEventCount(bounds=args.bounds,radius=args.radius,starttime=args.startTime,endtime=args.endTime,
                                      magrange=args.magRange,catalog=args.catalog,contributor=args.contributor)
    
    if nevents > maxevents: #oops, too many events for one query
        segments = []
        segments = getTimeSegments(segments,args.bounds,args.radius,args.startTime,args.endTime,
                                   args.magRange,args.catalog,args.contributor)
        eventlist = []
        for stime,etime in segments:
            sys.stderr.write('%s - Getting data for %s => %s\n' % (datetime.now(),stime,etime))
            eventlist += getEventData(bounds=args.bounds,radius=args.radius,starttime=stime,endtime=etime,
                                 magrange=args.magRange,ecatalog=args.catalog,contributor=args.contributor)
    else:
        eventlist = getEventData(bounds=args.bounds,radius=args.radius,starttime=args.startTime,endtime=args.endTime,
                                 magrange=args.magRange,catalog=args.catalog,contributor=args.contributor)

    if not len(eventlist):
        sys.stderr.write('No events found.  Exiting.\n')
        sys.exit(0)
    fmt = getFormatString(args.format,eventlist[0].keys())
    print getHeader(args.format,eventlist[0].keys())
    for event in eventlist:
        tpl = getFormatTuple(event)
        try:
            print fmt % tpl
        except:
            pass

if __name__ == '__main__':
    desc = '''Download basic earthquake information in line format (csv, tab, etc.).

    To download basic event information (time,lat,lon,depth,magnitude) and moment tensor components for a box around New Zealand
    during 2013:

    getcsv.py -o -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 > nz.csv

    To print the number of events that would be returned from the above query, and the maximum number of events that
    can be returned from ANY query:

    getcsv.py -x -o -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01

    Events which do not have a value for a given field (moment tensor components, for example), will have the string "nan" instead.

    Note that when specifying a search box that crosses the -180/180 meridian, you simply specify longitudes
    as you would if you were not crossing that meridian.

    Also note:  Large queries, particularly those that return more than the maximum number of events (20,000 at the time of 
    this writing), can take a very long time to download.  It IS possible to return more events than the "maximum" allowed, 
    but this is accomplished by breaking the query up into smaller time segments.  The author has tested queries just over 
    20,000 events, and it can take ~90 minutes to complete.
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
    parser.add_argument('-o','--get-moment-components', dest='getComponents', action='store_true',
                        help='Also extract moment-tensor components where available.')
    parser.add_argument('-a','--get-focal-angles', dest='getAngles', action='store_true',
                        help='Also extract focal-mechanism angles (strike,dip,rake) where available.')
    parser.add_argument('-t','--get-moment-type', dest='getType', action='store_true',
                        help='Also extract moment type (Mww,Mwc, etc.) where available')
    parser.add_argument('-f','--format', dest='format', choices=['csv','tab'], default='csv',
                        help='Output format')
    parser.add_argument('-x','--count', dest='getCount', action='store_true',
                        help='Just return the number of events in search and maximum allowed.')
    parser.add_argument('-v','--verbose', dest='verbose', action='store_true',
                        help='Print progress')
    
    pargs = parser.parse_args()

    main(pargs)
    
    
        
