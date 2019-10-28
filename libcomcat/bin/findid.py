#!/usr/bin/env python

# stdlib
import argparse
import sys
import logging
from datetime import datetime

# third party
import pandas as pd

# local imports
import libcomcat
from libcomcat.dataframes import find_nearby_events
from libcomcat.search import get_event_by_id
from libcomcat.logging import setup_logger

# constants
TIMEFMT = '%Y-%m-%dT%H:%M:%S'
DATEFMT = '%Y-%m-%d'
FILETIMEFMT = '%Y-%m-%d %H:%M:%S'
SEARCH_RADIUS = 100
TIME_WINDOW = 16  # seconds

pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 100)


def get_parser():
    desc = '''Find the id(s) of the closest earthquake to input parameters.

    To print the authoritative id of the event closest in time and space
    inside a 100 km, 16 second window to
    "2019-07-15T10:39:32 35.932 -117.715":

    %(prog)s  -e 2019-07-15T10:39:32 35.932 -117.715

    To print the ComCat url of that nearest event:

    %(prog)s  -e 2019-07-15T10:39:32 35.932 -117.715 -u

    To print all of the events that are within expanded distance/time windows:

    %(prog)s  -e 2019-07-15T10:39:32 35.932 -117.715 -a -r 200 -w 120

    To find the authoritative and contributing ids:

    %(prog)s  -i ci38572791 -a -r 200 -w 120

    To write the output from the last command into a csv spreadsheet:

    %(prog)s  -e 2019-07-15T10:39:32 35.932 -117.715 -a -r 200 -w 120 -o temp.csv

    To write the output from the last command into an excel spreadsheet:

    %(prog)s  -e 2019-07-15T10:39:32 35.932 -117.715 -a -r 200 -w 120 -o temp.xls -f excel
    '''

    parser = argparse.ArgumentParser(
        description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)

    # optional arguments
    parser.add_argument('-a', '--all', dest='print_all', action='store_true',
                        help='Print all IDs associated with event.',
                        default=False)
    ehelp = ('Specify event information (TIME LAT LON). '
             'Specify event information (TIME LAT LON). '
             'The time should be formatted as YYYY-mm-dd '
             'or YYYY-mm-ddTHH:MM:SS. Latitude and longitude '
             'should be in decimal degrees.')
    parser.add_argument('-e', '--eventinfo', nargs=3,
                        metavar=('TIME', 'LAT', 'LON'),
                        type=str, help=ehelp)
    parser.add_argument('-f', '--format', dest='format',
                        choices=['csv', 'tab', 'excel'], default='csv',
                        metavar='FORMAT', help=("Output format. Options include "
                                                "csv', 'tab', and 'excel'. Default is 'csv'."))
    parser.add_argument('-i', '--eventid',
                        metavar='EVENTID',
                        type=str, help='Specify an event ID')
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
    ohelp = ("If the '-a' argument is used, send the output to a file. "
             "Denote the format using '-f'.")
    parser.add_argument('-o', '--outfile',
                        help=ohelp)
    rhelp = 'Change the search radius (km) around the specified latitude and longitude. Default is %.0f km.' % SEARCH_RADIUS
    parser.add_argument('-r', '--radius', type=float,
                        help=rhelp)
    parser.add_argument('-u', '--url', dest='print_url', action='store_true',
                        help='Print the URL associated with event.', default=False)
    vstr = ('Print time and distance deltas, and azimuth from input '
            'parameters to event.')
    parser.add_argument('-v', '--verbose', dest='print_verbose',
                        action='store_true', help=vstr, default=False)
    parser.add_argument('--version', action='version',
                        version=libcomcat.__version__, help='Version of libcomcat.')
    whelp = 'Change the window (sec) around the specified time. Default is %.0f seconds.' % TIME_WINDOW
    parser.add_argument('-w', '--window', type=float,
                        help=whelp)
    return parser


def main():
    # set the display width such that table output is not truncated
    pd.set_option('display.max_columns', 10000)
    pd.set_option("display.max_colwidth", 10000)
    pd.set_option("display.expand_frame_repr", False)

    parser = get_parser()

    args = parser.parse_args()

    # make sure either args.eventinfo or args.eventid is specified
    if args.eventinfo is None and args.eventid is None:
        print('Please select --eventinfo or -i option. Exiting.')
        sys.exit(1)

    if args.eventinfo is None:
        detail = get_event_by_id(args.eventid)
        idlist = detail['ids'].split(',')[1:-1]
        idlist.remove(detail.id)
        print('Authoritative ID: %s\n' % detail.id)
        print('Contributing IDs:')
        for eid in idlist:
            print('  ' + eid)
        sys.exit(0)
    else:
        try:
            timestr = args.eventinfo[0]
            latstr = args.eventinfo[1]
            lonstr = args.eventinfo[2]
            try:
                time = datetime.strptime(timestr, TIMEFMT)
            except ValueError:
                time = datetime.strptime(timestr, DATEFMT)

            lat = float(latstr)
            lon = float(lonstr)
        except ValueError as ve:
            print('Error parsing event info:\n%s' % str(ve))
            sys.exit(1)

    # trap for mutually exclusive options a, u and v
    argsum = (args.print_all + args.print_url + args.print_verbose)
    if argsum > 1:
        msg = ('The -a, -v, and -u options are mutually exclusive. '
               'Choose one of these options. Exiting.')
        print(msg)
        sys.exit(1)

    # if -o option you must have specified -a option also
    if args.outfile is not None and not args.print_all:
        print('You must select -a and -o together. Exiting')
        sys.exit(1)

    setup_logger(args.logfile, args.loglevel)

    twindow = TIME_WINDOW
    if args.window:
        twindow = args.window
    # set distance thresholds
    radius = SEARCH_RADIUS
    if args.radius:
        radius = args.radius

    event_df = find_nearby_events(time, lat,
                                  lon, twindow, radius)

    if event_df is None:
        logging.error(
            'No events found matching your search criteria. Exiting.')
        sys.exit(0)

    nearest = event_df.iloc[0]

    if args.print_all:
        if not args.outfile:
            print(event_df)
        else:
            if args.format == 'excel':
                event_df.to_excel(args.outfile, index=False)
            elif args.format == 'tab':
                event_df.to_csv(args.outfile, sep='\t', index=False)
            else:
                event_df.to_csv(args.outfile, index=False)

            print('Wrote %i records to %s' % (len(event_df), args.outfile))
        sys.exit(0)

    if args.print_verbose:
        print('Event %s' % nearest['id'])
        cols = nearest.index.to_list()
        cols.remove('id')
        for col in cols:
            print('  %s : %s' % (col, nearest[col]))
        sys.exit(0)

    if args.print_url:
        print(nearest['url'])
        sys.exit(0)

    print(nearest['id'])


if __name__ == '__main__':
    main()
