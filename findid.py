#!/usr/bin/env python

#stdlib
import argparse
from datetime import datetime,timedelta
import os
import sys
import urllib
import urllib2
import json

#third party
from libcomcat import comcat
from neicmap import distance
import numpy as np

TIMEFMT = '%Y-%m-%dT%H:%M:%S'
FILETIMEFMT = '%Y-%m-%d %H:%M:%S'
RADIUS = 100
TIME = 16 #seconds
        
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

def getClosest(elat,elon,etime,eventlist):
    dmin = 9999999
    tmin = 9999999
    azmin = 9999999
    imin = -1    
    for i in range(0,len(eventlist)):
        event = eventlist[i]
        lon,lat,depth = event['geometry']['coordinates']
        time = datetime.utcfromtimestamp(event['properties']['time']/1000)
        dd = distance.sdist(elat,elon,lat,lon)/1000.0
        azim = distance.getAzimuth(elat,elon,lat,lon)
        if time > etime:
            dt = (time - etime).seconds
        else:
            dt = (etime - time).seconds
        if dd < dmin and dt < dmin:
            dmin = dd
            tmin = dt
            azmin = azim
            imin = i
    event = eventlist[imin]
    idlist = event['properties']['ids'].split(',')[1:-1]
    eurl = event['properties']['url']
    authid = event['id']
    idlist.remove(authid)
    idlist.append(authid)
    idlist = idlist[::-1]
    return (idlist,eurl,dmin,tmin,azmin)

def getTime(timestr):
    t = None
    try:
        t = datetime.strptime(timestr,TIMEFMT)
    except:
        try:
            t = datetime.strptime(timestr,FILETIMEFMT)
        except:
            pass
    return t

def getInputParams(params):
    time = None
    lat = None
    lon = None
    try:
        time = datetime.strptime(params[0],TIMEFMT)
        lat = float(params[1])
        lon = float(params[2])
    except:
        pass
    return (time,lat,lon)

def getEventInfo(time,lat,lon,twindow,radius):
    url = comcat.URLBASE
    params = {'format':'geojson'}
    #set time thresholds
    starttime = time - timedelta(seconds=twindow/2.0)
    endtime = time + timedelta(seconds=twindow/2.0)
    params['starttime'] = starttime.strftime(TIMEFMT)
    params['endtime'] = endtime.strftime(TIMEFMT)
    params['latitude'] = lat
    params['longitude'] = lon
    params['maxradiuskm'] = radius
    
    urlparams = urllib.urlencode(params)
    url = comcat.URLBASE % urlparams
    data = None
    try:
        fh = comcat.getURLHandle(url)
        data = fh.read()
        fh.close()
    except urllib2.URLError,msg:
        raise Exception('Could not open search url %s.  "%s"' % (url,str(msg)))
        
    jdict = json.loads(data)
    if len(jdict['features']):
        eventids,url,dmin,tmin,azim = getClosest(lat,lon,time,jdict['features'])
    else:
        eventids = ['NA']
        url = 'NA'
        dmin = np.nan
        tmin = np.nan
    return (eventids,url,dmin,tmin,azim)
    
def main(args):
    if not args.params and not args.file:
        print 'You must supply either a file input with -f or time,lat,lon values with -p.  Exiting.'
        sys.exit(1)
    twindow = TIME
    if args.window:
        twindow = args.window
    #set distance thresholds
    radius = RADIUS
    if args.radius:
        radius = args.radius
    if args.params:
        time,lat,lon = getInputParams(args.params)
        if time is None or lat is None or lon is None:
            fmt = '''Could not parse input parameters "%s" as time,lat,lon.  
            Make sure that times are specified as %s and lat/lon values are 
            integers or floats.  Exiting.'''
            print fmt % (' '.join(args.params),TIMEFMT)
            sys.exit(1)
        eventids,url,dmin,tmin,azim = getEventInfo(time,lat,lon,radius,twindow)
        if args.printAll:
            print ' '.join(eventids)
        else:
            print eventids[0]
        if args.verbose:
            print '%.1f km, %.1f seconds,%.1f degrees' % (dmin,tmin,azim)
        if args.printURL:
            print url
        sys.exit(0)

    if args.file:
        newlines = []
        hasheader = False
        f = open(args.file,'rt')
        line = f.readline().strip()
        parts = line.split(',')
        t = None
        header = None
        t = getTime(parts[0])
        if t is None:
            hashheader = True
            header = parts
        else:
            f.seek(0)
        if header is not None:
            if args.printURL:
                header = ['id','url'] + header
            else:
                header = ['id'] + header
            newlines.append(','.join(header))
        for line in f.readlines():
            parts = line.strip().split(',')
            time = getTime(parts[0])
            lat = float(parts[1])
            lon = float(parts[2])
            eid,url,dmin,tmin,azim = getEventInfo(time,lat,lon,twindow,radius)
            if args.printURL:
                newline = ','.join([eid[0],url] + parts)
            else:
                newline = ','.join([eid[0]] + parts)
            newlines.append(newline)
        f.close()
        for newline in newlines:
            print newline
        sys.exit(0)

if __name__ == '__main__':
    desc = '''Find the id(s) of the closest earthquake to input parameters. 

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
    '''

    filehelp = """Parse time,lat,lon from input csv file, which can have a header row but must have time,lat,lon as first
    three columns.  Time format can be either YYYY-MM-DDTHH:MM:SS OR YYYY-MM-DD HH:MM:SS.  Output will have an "id" column prepended,
    and a "url" column second (if -u option selected), followed by the input columns of data.
    """
    
    parser = argparse.ArgumentParser(description=desc,formatter_class=argparse.RawDescriptionHelpFormatter)
    #positional arguments
    parser.add_argument('-p','--params', metavar=('time','lat','lon'), nargs=3, 
                        help='Input time, lat and lon to use for search.')
    #optional arguments
    parser.add_argument('-r','--radius',type=float,
                        help='Change search radius from default of %.0f km.' % RADIUS)
    parser.add_argument('-w','--window',type=float,
                        help='Change time window of %.0f seconds.' % TIME)
    parser.add_argument('-f','--file',
                        help=filehelp)
    parser.add_argument('-a','--all', dest='printAll',action='store_true',
                        help='Print all ids associated with event.')
    parser.add_argument('-u','--url', dest='printURL',action='store_true',
                        help='Print URL associated with event.')
    parser.add_argument('-v','--verbose',action='store_true',
                        help='Print time/distance deltas, and azimuth from input parameters to event.')
    
    pargs = parser.parse_args()

    main(pargs)
    
    
        
