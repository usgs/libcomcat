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
    parser = argparse.ArgumentParser(description='Download earthquake information in a fixed-width format.')
    #optional arguments
    parser.add_argument('-b','--bounds', metavar=('lonmin','lonmax','latmin','latmax'),
                        dest='bounds', type=float, nargs=4,
                        help='Bounds to constrain event search [lonmin lonmax latmin latmax]')
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
    parser.add_argument('-d','--ehdf', dest='ehdf', action='store_true',
                        help='Output data in EHDF format')
    
    args = parser.parse_args()

    eventlist = getPhaseData(bounds=args.bounds,starttime=args.startTime,endtime=args.endTime,
                             magrange=args.magRange,catalog=args.catalog,contributor=args.contributor)
    
    for event in eventlist:
        if args.format == 'isf':
            text = fixed.renderISF(event)
        elif args.format == 'ehdf':
            text = fixed.renderEHDF(event)
        print text
        
