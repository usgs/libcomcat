#!/usr/bin/env python

# stdlib imports
import argparse
import sys

# third party imports
import pandas as pd

# local imports
from libcomcat.classes import SummaryEvent, VersionOption
from libcomcat.utils import maketime
from libcomcat.dataframes import get_impact_data_frame
from libcomcat.search import search, count, get_event_by_id


def get_parser():
    desc = '''Download impact results in line format (csv, tab, etc.).

    To download basic impact information for events around New Zealand from 2010
    to the present in CSV format:

    %(prog)s  nz_impact.csv -f csv -s 2010-01-01 -m 5.5 9.9 -b 163.213 -178.945 -48.980 -32.324 --host "dev01-earthquake.cr.usgs.gov"

    To download the same information in Excel format:

    %(prog)s nz_impact.xlsx -f excel -s 2010-01-01 -m 5.5 9.9 -b 163.213 -178.945 -48.980 -32.324  --host "dev01-earthquake.cr.usgs.gov"

    NOTES:

    1) Any start or end time where only date is specified (YYYY-mm-dd) will
    be translated to the beginning of that day.  Thus, a start time of
    "2015-01-01" becomes "2015-01-01T:00:00:00" and an end time of "2015-01-02"
    becomes ""2015-01-02T:00:00:00".

    2) Some events may not include loss data. For those events, the user will be warned
    and that event will be skipped

    3) Note that when specifying a search box that crosses the -180/180 meridian,
    you simply specify longitudes as you would if you were not crossing that
    meridian (i.e., lonmin=179, lonmax=-179).  The program will resolve the
    discrepancy.

    4) The ComCat API has a returned event limit of 20,000.  Queries that
    exceed this ComCat limit ARE supported by this software if the --disable_limit
    flag is used.'''

    parser = argparse.ArgumentParser(
        description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    # positional arguments
    parser.add_argument('filename',
                        metavar='FILENAME', help='Output filename.')
    # optional arguments
    id = 'Retrieve information from a single PAGER event'
    parser.add_argument('-i', '--eventid', help=id,
                        metavar='EVENTID')
    helpstr = ('Bounds to constrain event search '
               '[lonmin lonmax latmin latmax]')
    parser.add_argument('-b', '--bounds',
                        metavar=('lonmin', 'lonmax', 'latmin', 'latmax'),
                        dest='bounds', type=float, nargs=4,
                        help=helpstr)
    helpstr = 'Search radius in KM (use instead of bounding box)'
    parser.add_argument('-r', '--radius', dest='radius',
                        metavar=('lat', 'lon', 'rmax'),
                        type=float, nargs=3,
                        help=helpstr)
    helpstr = ('Start time for search (defaults to ~30 days ago). '
               'YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s')
    parser.add_argument('-s', '--start-time', dest='startTime', type=maketime,
                        help=helpstr)
    helpstr = ('End time for search (defaults to current date/time). '
               'YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s')
    parser.add_argument('-e', '--end-time', dest='endTime', type=maketime,
                        help=helpstr)
    helpstr = 'Min/max (authoritative) magnitude to restrict search.'
    parser.add_argument('-m', '--mag-range', metavar=('minmag', 'maxmag'),
                        dest='magRange', type=float, nargs=2,
                        help=helpstr)
    helpstr = ('Limit to events after specified time. YYYY-mm-dd or '
               'YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('--after', dest='after', type=maketime,
                        help=helpstr)
    parser.add_argument('-f', '--format', dest='format',
                        choices=['csv', 'tab', 'excel'], default='csv',
                        metavar='FORMAT', help='Output format.')
    effect = 'Specify effect types.'
    parser.add_argument('-t', '--effect-types', dest='effect_types',
                        help=effect, nargs='*', default=None)
    loss_type = 'Specify loss types.'
    parser.add_argument('-l', '--loss-types', dest='loss_types',
                        help=loss_type, nargs='*', default=None)
    loss_extents = 'Specify loss extents.'
    parser.add_argument('-x', '--loss-extents', dest='loss_extents',
                        help=loss_extents, nargs='*', default=None)
    sources = 'Collect all sources not only the most recent, authoritative.'
    parser.add_argument('-a', '--all-sources',
                        help=sources, action='store_true', default=False)
    contributing = 'Include all contributing features.'
    parser.add_argument('-c', '--include-contributing', help=contributing,
                        action='store_true', default=False)
    versionhelp = 'Retrieve information from all versions of PAGER'
    parser.add_argument('-p', '--previous-versions', help=versionhelp, action='store_true',
                        default=False)
    source = ("Specify comcat product source network."
              "Any one of:\n"
              "        - 'preferred' Get version(s) of products from preferred source.\n"
              "        - 'all' Get version(s) of products from all sources.\n"
              "        - Any valid source network for this type of product ('us','ak',etc.)\n")
    parser.add_argument('--source', dest='source', help=source,
                        default='preferred')
    version = "Specify product version. (PREFERRED, FIRST, ALL)."
    parser.add_argument('-v', '--version', dest='version', help=version,
                        default='PREFERRED')
    helpstr = ('Specify a different comcat *search* host than '
               'earthquake.usgs.gov.')
    parser.add_argument('--host',
                        help=helpstr)
    helpstr = ('Segment search to exceede the 20,000 event limit.'
            ' This will slow down the search process.')
    parser.add_argument('--disable_limit',help=helpstr, action='store_false',
                        default=True)
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

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

    if args.bounds and args.radius:
        sys.stderr.write(
            'Please specify either a bounding box OR radius search.\n')
        sys.exit(1)

    if args.version.upper() not in ['PREFERRED', 'FIRST', 'ALL']:
        sys.stderr.write(
            "Not a valid product version. Must be one of ['PREFERRED', 'FIRST', 'ALL'].\n")
        sys.exit(1)
    elif args.version.upper() == 'PREFERRED':
        product_version = VersionOption.PREFERRED
    elif args.version.upper() == 'FIRST':
        product_version = VersionOption.FIRST
    elif args.version.upper() == 'ALL':
        product_version = VersionOption.ALL
    else:
        product_version = VersionOption.PREFERRED

    if args.eventid:
        event = get_event_by_id(args.eventid,
                                includesuperseded=args.previous_versions,
                                host=args.host)
        events = [event]
    else:
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
                        minmagnitude=minmag,
                        producttype='impact',
                        host=args.host,
                        enable_limit=args.disable_limit)

    if not len(events):
        sys.stderr.write(
            'No events found matching your search criteria. Exiting.\n')
        sys.exit(0)

    dataframe = None
    nevents = len(events)
    i = 1

    for event in events:
        i += 1
        sys.stderr.write('Checking event %s, %i of %i\n' %
                         (str(event), i, len(events)))
        if isinstance(event, SummaryEvent):
            try:
                detail = event.getDetailEvent(
                    includesuperseded=args.previous_versions)
            except Exception as e:
                sys.stderr.write('Error: "%s". Skipping.\n' % str(e))
                continue
        else:
            detail = event
        try:
            df = get_impact_data_frame(detail, effect_types=args.effect_types,
                                       loss_types=args.loss_types, loss_extents=args.loss_extents,
                                       all_sources=args.all_sources,
                                       include_contributing=args.include_contributing,
                                       source=args.source,
                                       version=product_version)
            if dataframe is None:
                dataframe = df
            else:
                dataframe = pd.concat([dataframe, df])
        except AttributeError as e:
            sys.stderr.write(str(e)+'\n')
            sys.stderr.write("Skipping this event.\n")

    if dataframe is not None:
        if args.format == 'csv':
            dataframe.to_csv(args.filename, index=False, chunksize=1000)
        elif args.format == 'tab':
            dataframe.to_csv(args.filename, sep='\t', index=False)
        else:
            dataframe.to_excel(args.filename, index=False)

        sys.stderr.write('%i rows saved to %s.\n' %
                         (len(dataframe), args.filename))
        sys.exit(0)
    else:
        sys.stderr.write('No valid impact products found.\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
