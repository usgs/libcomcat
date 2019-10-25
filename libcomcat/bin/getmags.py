#!/usr/bin/env python
import argparse
import sys
import logging

# Third party imports
import libcomcat
from libcomcat.search import search, count, get_authoritative_info
from libcomcat.utils import (maketime,
                             CombinedFormatter)

import pandas as pd
from libcomcat.logging import setup_logger


def get_parser():
    desc = '''Download epicenter and all contributed magnitudes in line format (csv, tab, etc.).

    %(prog)s nz.csv -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f csv

    To download events with fractional days, use the ISO 8601 combined date
    time format (YYYY-mm-ddTHH:MM:SS, YYYY-mm-ddTHH:MM:SS.s): %(prog)s -s
    2015-01-01T00:00:00 -e 2015-01-01T01:15:00

    NOTES:

    Any start or end time where only date is specified (YYYY-mm-dd) will
    be translated to the beginning of that day.  Thus, a start time of
    "2015-01-01" becomes "2015-01-01T:00:00:00" and an end time of "2015-01-02"
    becomes ""2015-01-02T:00:00:00".

    Events which do not have a value for a given magnitude will be empty.

    Note that when specifying a search box that crosses the -180/180 meridian,
    you simply specify longitudes as you would if you were not crossing that
    meridian (i.e., lonmin=179, lonmax=-179).  The program will resolve the
    discrepancy.

    The ComCat API has a returned event limit of 20,000.  Queries
    that exceed this ComCat limit ARE supported by this software,
    by breaking up one large request into a number of smaller
    ones.  However, large queries can take a very long time to
    download. This delay is caused by the fact that when this
    program has to retrieve ALL magnitudes for an event, it must
    open a URL for EACH event and parse potentially multiple XML
    files.

    '''
    parser = argparse.ArgumentParser(
        description=desc, formatter_class=CombinedFormatter)
    # positional arguments
    parser.add_argument('filename',
                        metavar='FILENAME', help='Output file name.')
    # optional arguments
    parser.add_argument('-b', '--bounds', metavar=('lonmin', 'lonmax', 'latmin', 'latmax'),
                        dest='bounds', type=float, nargs=4,
                        help='Bounds to constrain event search [lonmin lonmax latmin latmax]')
    parser.add_argument('-e', '--end-time', dest='endTime', type=maketime,
                        help='End time for search (defaults to current date/time).  YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.')
    parser.add_argument('-f', '--format', dest='format', choices=['csv', 'tab', 'excel'], default='csv',
                        help="Output format (csv, tab, or excel). Default is ‘csv’")
    loghelp = '''Send debugging, informational, warning and error messages to a file.
    '''
    parser.add_argument('--logfile', default='stderr', help=loghelp)
    levelhelp = '''Set the minimum logging level. The logging levels are (low to high):

     - debug: Debugging message will be printed, most likely for developers.
              Most verbose.
     - info: Only informational messages, warnings, and errors will be printed.
     - warning: Only warnings (i.e., could not retrieve information for a
                single event out of many) and errors will be printed.
     - error: Only errors will be printed, after which program will stop.
              Least verbose.
    '''
    parser.add_argument('--loglevel', default='info',
                        choices=['debug', 'info', 'warning', 'error'],
                        help=levelhelp)
    parser.add_argument('-m', '--mag-range', metavar=('minmag', 'maxmag'), dest='magRange', type=float, nargs=2,
                        help='Minimum and maximum (authoritative) magnitude to restrict search.')
    parser.add_argument('-r', '--radius', dest='radius', metavar=('lat', 'lon', 'rmax'), type=float,
                        nargs=3, help=('Search radius in kilometers (radius and bounding options '
                                       'are mutually exclusive). The latitude and longitude for the search should be '
                                       'specified before the radius (example: -r -48.980 -178.945 10).'))
    parser.add_argument('-s', '--start-time', dest='startTime', type=maketime,
                        help='Start time for search (defaults to ~30 days ago).  YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.')
    parser.add_argument('-t', '--time-after', dest='after', type=maketime,
                        help='Limit to events after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS.')
    parser.add_argument('--version', action='version',
                        version=libcomcat.__version__, help='Version of libcomcat.')
    parser.add_argument('-x', '--count', dest='getCount', action='store_true',
                        help='Just return the number of events in search and maximum allowed.')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    setup_logger(args.logfile, args.loglevel)

    latitude = None
    longitude = None
    radiuskm = None
    lonmin = latmin = lonmax = latmax = None
    if args.radius:
        latitude = args.radius[0]
        longitude = args.radius[1]
        radiuskm = args.radius[2]

    if args.bounds:
        lonmin, lonmax, latmin, latmax = args.bounds
        # fix longitude bounds when crossing dateline
        if lonmin > lonmax and lonmax >= -180:
            lonmin -= 360
    else:
        lonmin, lonmax, latmin, latmax = None, None, None, None

    minmag = 0.0
    maxmag = 9.9
    if args.magRange:
        minmag = args.magRange[0]
        maxmag = args.magRange[1]

    if args.getCount:
        nevents = count(starttime=args.startTime,
                        endtime=args.endTime,
                        updatedafter=args.after,
                        minlatitude=latmin,
                        maxlatitude=latmax,
                        minlongitude=lonmin,
                        maxlongitude=lonmax,
                        latitude=latitude,
                        longitude=longitude,
                        maxradiuskm=radiuskm,
                        maxmagnitude=maxmag,
                        minmagnitude=minmag)
        print('There are %i events matching input criteria.' % nevents)
        sys.exit(0)

    if args.bounds and args.radius:
        print('Please specify either a bounding box OR radius search.')
        sys.exit(1)

    events = search(starttime=args.startTime,
                    endtime=args.endTime,
                    updatedafter=args.after,
                    minlatitude=latmin,
                    maxlatitude=latmax,
                    minlongitude=lonmin,
                    maxlongitude=lonmax,
                    latitude=latitude,
                    longitude=longitude,
                    maxradiuskm=radiuskm,
                    maxmagnitude=maxmag,
                    minmagnitude=minmag)

    if not len(events):
        print('No events found matching your search criteria. Exiting.')
        sys.exit(0)

    # create a dataframe with these columns - we'll add more later
    df = pd.DataFrame(columns=['id', 'time', 'lat', 'lon', 'depth',
                               'location', 'url', 'hypo_src'])
    ievent = 1

    for event in events:
        id_list = event['ids'].split(',')[1:-1]
        source = event.id.replace(event['code'], '')
        row = pd.Series(data={'id': event.id,
                              'time': event.time,
                              'lat': event.latitude,
                              'lon': event.longitude,
                              'depth': event.depth,
                              'location': event.location,
                              'url': event.url,
                              'hypo_src': source})

        imag = 1
        tpl = (event.id, ievent, len(events), len(id_list))
        logging.debug('Parsing event %s (%i of %i) - %i origins' % tpl)
        ievent += 1
        errors = []
        mags = {}
        for eid in id_list:
            magtypes, loctypes, msg = get_authoritative_info(eid)
            if len(msg):
                logging.info(msg)
            mags.update(magtypes)
            imag += 1
        row = pd.concat([row, pd.Series(mags)])
        df = df.append(row, ignore_index=True)

    if len(errors):
        print('Some events could not be retrieved:')
        for error in errors:
            print('\t%s' % error)

    if args.format == 'excel':
        df.to_excel(args.filename, index=False)
    elif args.format == 'tab':
        df.to_csv(args.filename, sep='\t', index=False)
    else:
        df.to_csv(args.filename, index=False)
    print('%i records saved to %s.' % (len(df), args.filename))
    sys.exit(0)


if __name__ == '__main__':
    main()
