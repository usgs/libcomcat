#!/usr/bin/env python

#stdlib
import argparse
from datetime import datetime
import os

#third party
from libcomcat.comcat import getContents

TIMEFMT = '%Y-%m-%dT%H:%M:%S'
DATEFMT = '%Y-%m-%d'
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
    desc = '''Download product files from USGS ComCat.

    To download ShakeMap grid.xml files for a box around New Zealand during 2013:

    getcomcat.py shakemap grid.xml -o /home/user/newzealand -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01

    Note that when specifying a search box that crosses the -180/180 meridian, you simply specify longitudes
    as you would if you were not crossing that meridian.
    '''
    parser = argparse.ArgumentParser(description=desc,formatter_class=argparse.RawDescriptionHelpFormatter)
    #positional arguments
    parser.add_argument('product', metavar='PRODUCT', 
                        help='The name of the desired product (shakemap, dyfi, etc.)')
    parser.add_argument('contents', metavar='CONTENTLIST', nargs='*',
                        help='The names of the product contents (grid.xml, stationlist.txt, etc.) ')
    #optional arguments
    parser.add_argument('-o','--output-folder', dest='outputFolder', default=os.getcwd(),
                        help='Folder where output files should be written.')
    parser.add_argument('-b','--bounds', metavar=('lonmin','lonmax','latmin','latmax'),
                        dest='bounds', type=float, nargs=4,
                        help='Bounds to constrain event search [lonmin lonmax latmin latmax]')
    parser.add_argument('-s','--start-time', dest='startTime', type=maketime,
                        help='Start time for search (defaults to ~30 days ago). YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-e','--end-time', dest='endTime', type=maketime,
                        help='End time for search (defaults to current date/time). YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-a','--after', dest='after', type=maketime,
                        help='Limit to events after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-m','--mag-range', metavar=('minmag','maxmag'),dest='magRange', type=float,nargs=2,
                        help='Min/max magnitude to restrict search.')
    parser.add_argument('-c','--catalog', dest='catalog', 
                        help='Source catalog from which products derive (atlas, centennial, etc.)')
    parser.add_argument('-n','--contributor', dest='contributor', 
                        help='Source contributor (who loaded product) (us, nc, etc.)')
    parser.add_argument('-i','--event-id', dest='eventid', 
                        help='Event ID from which to download product contents.')
    parser.add_argument('-p','--product-property', dest='productProperties', type=makedict,
                        help='Product property (reviewstatus:approved).')
    parser.add_argument('-t','--event-property', dest='eventProperties', 
                        help='Event property (alert:yellow, status:REVIEWED, etc.).',type=makedict)
    parser.add_argument('-l','--list-url', dest='listURL', action='store_true',
                        help='Only list urls for contents in events that match criteria.')
    
    args = parser.parse_args()

    files = getContents(args.product,args.contents,outfolder=args.outputFolder,bounds=args.bounds,
                        starttime=args.startTime,endtime=args.endTime,magrange=args.magRange,
                        catalog=args.catalog,contributor=args.contributor,eventid=args.eventid,
                        listURL=args.listURL,eventProperties=args.eventProperties,
                        productProperties=args.productProperties,since=args.after)
    print
    print '%i files were downloaded to %s' % (len(files),args.outputFolder)
