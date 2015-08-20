#!/usr/bin/env python

#stdlib
import argparse
from datetime import datetime,timedelta
from collections import OrderedDict
import os
import sys
import re

#third party
from libcomcat import comcat

TIMEFMT = '%Y-%m-%d %H:%M:%S.%f'
DATEFMT = '%Y-%m-%d'

def getNewEvent(event,maxmags):
    ibigmag = -1
    bigmag = 0
    for key in event.keys():
        if re.search('mag[0-9]*-type',key):
            ibigmag = event.keys().index(key)
            bigmag = int(re.findall('\d+',key)[0])
    #we can only get away with this because this is an ordereddict
    keys = event.keys()
    values = event.values()
    idx = ibigmag + 1
    for i in range(bigmag+1,maxmags+1):
        magkey = 'mag%i' % i
        srckey = 'mag%i-source' % i
        typekey = 'mag%i-type' % i
        keys.insert(idx,magkey)
        keys.insert(idx+1,srckey)
        keys.insert(idx+2,typekey)
        values.insert(idx,(float('nan'),'%.1f'))
        values.insert(idx+1,('NA','%s'))
        values.insert(idx+2,('NA','%s'))
        idx += 3
    
    newevent = OrderedDict(zip(keys,values))
    return newevent

def maketime(timestring):
    outtime = None
    try:
        outtime = comcat.ShakeDateTime.strptime(timestring,TIMEFMT)
    except:
        try:
            outtime = comcat.ShakeDateTime.strptime(timestring,DATEFMT)
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
    if args.limitType and not args.getComponents:
        print 'To limit your search to specific moment tensor types, specify both -o and -l options.'
        sys.exit(1)
    if args.getCount:
        nevents,maxevents = comcat.getEventCount(bounds=args.bounds,radius=args.radius,
                                          starttime=args.startTime,endtime=args.endTime,
                                          magrange=args.magRange,catalog=args.catalog,
                                          contributor=args.contributor)
        fmt = '%i %i'
        print fmt % (nevents,maxevents)
        sys.exit(0)

    stime = comcat.ShakeDateTime(1900,1,1)
    etime = comcat.ShakeDateTime.utcnow()
    if args.startTime:
        stime = args.startTime
    if args.endTime:
        etime = args.endTime

    if stime >= etime:
        print 'End time must be greater than start time.  Your inputs: Start %s End %s' % (stime,etime)
        sys.exit(1)

    #we used to do a count of how many events would be returned, 
    #but it turns out that doing the count takes almost as much time 
    #as a query that actually returns the data.  So, here we're just 
    #going to split the time segment up into one-week chunks and assume
    #that no individual segment will return more than the 20,000 event limit.
    segments = comcat.getTimeSegments2(stime,etime)
    eventlist = []
    maxmags = 0
    sys.stderr.write('Breaking request into %i segments.\n' % len(segments))
    for stime,etime in segments:
        #sys.stderr.write('%s - Getting data for %s => %s\n' % (comcat.ShakeDateTime.now(),stime,etime))
        teventlist,tmaxmags = comcat.getEventData(bounds=args.bounds,radius=args.radius,starttime=stime,endtime=etime,
                                                  magrange=args.magRange,catalog=args.catalog,
                                                  contributor=args.contributor,getComponents=args.getComponents,
                                                  getAngles=args.getAngles,limitType=args.limitType,getAllMags=args.getAllMags)
        eventlist += teventlist
        if tmaxmags > maxmags:
            maxmags = tmaxmags

    if not len(eventlist):
        sys.stderr.write('No events found.  Exiting.\n')
        sys.exit(0)

    #eventlist is a list of ordereddict objects
    #the dict keys collectively provide the header
    #the dict values contain (value,fmt) where value is magnitude, latitude, etc. and fmt is the formatting string
    #print the header
    tmpevent = getNewEvent(eventlist[0],maxmags)
    hdrlist = tmpevent.keys()
    print ','.join(hdrlist)
    #get the formatting string for each line
    fnuggets = [v[1] for v in tmpevent.values()]
    fmt = ','.join(fnuggets)
    for event in eventlist:
        if args.limitType is not None and event['type'][0].lower() != args.limitType:
            continue
        event['time'][0] = event['time'][0].strftime(TIMEFMT)[0:-3]
        newevent = getNewEvent(event,maxmags)
        tpl = tuple([v[0] for v in newevent.values()])
        try:
            print fmt % tpl
        except:
            sys.stderr.write('Could not write event %s\n' % event['id'])
            for i in range(0,len(fnuggets)):
                print fnuggets[i],tpl[i]
            break
            

if __name__ == '__main__':
    desc = '''Download basic earthquake information in line format (csv, tab, etc.).

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
                        help='Min/max (authoritative) magnitude to restrict search.')
    parser.add_argument('-c','--catalog', dest='catalog', 
                        help='Source catalog from which products derive (atlas, centennial, etc.)')
    parser.add_argument('-n','--contributor', dest='contributor', 
                        help='Source contributor (who loaded product) (us, nc, etc.)')
    parser.add_argument('-o','--get-moment-components', dest='getComponents', action='store_true',
                        help='Also extract moment-tensor components (including type and derived hypocenter) where available.')
    parser.add_argument('-l','--limit-type', dest='limitType', default=None,
                        choices=comcat.MTYPES, type=str,
                        help='Only extract moment-tensor components from given type.')
    parser.add_argument('-a','--get-focal-angles', dest='getAngles', action='store_true',
                        help='Also extract focal-mechanism angles (strike,dip,rake) where available.')
    parser.add_argument('-g','--get-all-magnitudes', dest='getAllMags', action='store_true',
                        help='Extract all magnitudes (with sources),authoritative listed first.')
    parser.add_argument('-f','--format', dest='format', choices=['csv','tab'], default='csv',
                        help='Output format')
    parser.add_argument('-x','--count', dest='getCount', action='store_true',
                        help='Just return the number of events in search and maximum allowed.')
    parser.add_argument('-v','--verbose', dest='verbose', action='store_true',
                        help='Print progress')
    
    pargs = parser.parse_args()

    main(pargs)
    
    
        
