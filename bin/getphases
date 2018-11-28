#!/usr/bin/env python

# stdlib imports
from datetime import datetime
import sys
import argparse
import os.path


# third party imports
import pandas as pd

# local imports
from libcomcat.utils import maketime
from libcomcat.dataframes import get_phase_dataframe
from libcomcat.search import search, get_event_by_id

TIMEOUT = 60  # how many seconds to wait to fetch a url?

HDR_DOC = ['This file contains information about either a preferred',
           'solution for a given earthquake, or a solution from ',
           'a particular catalog/network.',
           'The header information will consist of the following fields:',
           '--------------------------------------------------------------',
           'id: The ID for the event from the preferred or specific network.',
           'time: The time of the event, always in UTC.',
           'location: A string describing the earthquake location.',
           'latitude: Earthquake latitude in decimal degrees.',
           'longitude: Earthquake longitude in decimal degrees.',
           'depth: Earthquake depth in kilometers.',
           'magnitude: Earthquake magnitude',
           'magtype: Magnitude type (mw,mww,mb,etc.)',
           'url:  The ComCat URL where all of the data for this earthquake can be found.',
           '*_mrr,mtt,mpp,mrt,mrp,mtp: Moment tensor components (if available) from preferred source (N m).',
           '*_np1_strike,dip,rake: Two sets of nodal plane angles for focal mechanism.',
           '--------------------------------------------------------------',
           'The remaining rows/columns contain the phase data for the event,',
           'with the following columns:',
           '--------------------------------------------------------------',
           'Channel: Network.Station.Channel.Location (NSCL) style station description.',
           '         ("--" indicates missing information)',
           'Distance: Distance (kilometers) from epicenter to station.',
           'Azimuth: Azimuth (degrees) from epicenter to station.',
           'Phase: Name of the phase (Pn,Pg, etc.)',
           'Arrival Time: Pick arrival time (UTC).',
           'Status: "manual" or "automatic".',
           'Residual: Arrival time residual.',
           'Weight: Arrival weight.',
           '--------------------------------------------------------------']


def get_parser():
    desc = '''Download phase data for matching events into CSV or Excel format.

    The resulting files will contain a "header" consisting of basic earthquake information
    (Id,Time,Latitude,Longitude,Depth,Magnitude, etc.) at the top of the file. In the Excel
    format, this information takes the first several rows and two columns. In CSV format, the
    values are the first lines of the file, prepended with a "#" (comment) character.

    To download phase data to Excel format for a small rectangle in Oklahoma in 2017:
    %(prog)s ~/tmp/phase_data -b -97.573 -97.460 36.247 36.329 -s 2017-08-26 -e 2017-09-15 -f excel

    To download phase data for the 2017 7.1 Mexico City event:
    %(prog)s ~/tmp/phase_data -i us2000ar20 -f excel
    '''
    parser = argparse.ArgumentParser(
        description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    # positional arguments
    parser.add_argument('directory',
                        metavar='DIRECTORY', help='Output directory.')
    # optional arguments
    parser.add_argument('-b', '--bounds', metavar=('lonmin', 'lonmax', 'latmin', 'latmax'),
                        dest='bounds', type=float, nargs=4,
                        help='Bounds to constrain event search [lonmin lonmax latmin latmax]')
    parser.add_argument('-r', '--radius', dest='radius', metavar=('lat', 'lon', 'rmax'), type=float,
                        nargs=3, help='Search radius in KM (use instead of bounding box)')
    parser.add_argument('-s', '--start-time', dest='startTime', type=maketime,
                        help='Start time for search (defaults to ~30 days ago).  YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s')
    parser.add_argument('-e', '--end-time', dest='endTime', type=maketime,
                        help='End time for search (defaults to current date/time).  YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s')
    parser.add_argument('-i', '--event-id', dest='eventid',
                        help='Extract phase data for a single event, using ComCat event ID.')
    parser.add_argument('-t', '--time-after', dest='after', type=maketime,
                        help='Limit to events after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-m', '--mag-range', metavar=('minmag', 'maxmag'), dest='magRange', type=float, nargs=2,
                        help='Min/max (authoritative) magnitude to restrict search.')
    parser.add_argument('-c', '--catalog', dest='catalog',
                        help='Source catalog from which products derive (atlas, centennial, etc.)')
    parser.add_argument('-n', '--contributor', dest='contributor',
                        help='Source contributor (who loaded product) (us, nc, etc.)')
    parser.add_argument('-f', '--format', dest='format', choices=['csv', 'tab', 'excel'], default='csv',
                        metavar='FORMAT', help='Output format.')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    if args.eventid:
        detail = get_event_by_id(args.eventid, catalog=args.catalog)
        df = get_phase_dataframe(detail, args.catalog)
        filename = save_dataframe(
            df, args.directory, detail, args.format, catalog=args.catalog)
        print('Saved phase data for %s to %s' % (detail.id, filename))
        sys.exit(0)

    if args.bounds and args.radius:
        print('Please specify either a bounding box OR radius search.')
        sys.exit(1)

    if not os.path.isdir(args.directory):
        os.makedirs(args.directory)

    latitude = None
    longitude = None
    radiuskm = None
    lonmin = latmin = lonmax = latmax = None
    starttime = endtime = None
    if args.radius:
        latitude = args.radius[0]
        longitude = args.radius[1]
        radiuskm = args.radius[2]

    if args.bounds:
        lonmin, lonmax, latmin, latmax = args.bounds
        # fix longitude bounds when crossing dateline
        if lonmin > lonmax and lonmax >= -180:
            lonmin -= 360

    minmag = 0.0
    maxmag = 9.9
    if args.magRange:
        minmag = args.magRange[0]
        maxmag = args.magRange[1]

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
                    catalog=args.catalog,
                    contributor=args.contributor,
                    maxmagnitude=maxmag,
                    minmagnitude=minmag)

    if not len(events):
        print('No events found matching your search criteria. Exiting.')
        sys.exit(0)

    for event in events:
        if not event.hasProduct('phase-data'):
            continue
        try:
            detail = event.getDetailEvent()
            df = get_phase_dataframe(detail, args.catalog)
            filename = save_dataframe(
                df, args.directory, detail, args.format, catalog=args.catalog)

            print('Saved phase data for %s to %s' % (event.id, filename))
        except Exception as e:
            print('Failed to retrieve phase data for event %s.  Error "%s"... continuing.' % (
                event.id, str(e)))
            continue


def save_dataframe(df, directory, event, file_format, catalog=None):
    edict = event.toDict(catalog=catalog)
    if file_format == 'excel':
        ext = 'xlsx'
        filename = os.path.join(directory, '%s_phases.%s' % (edict['id'], ext))
        writer = pd.ExcelWriter(
            filename, engine='xlsxwriter', datetime_format='yyyy-mm-dd hh:mm:ss.000')
        df.to_excel(writer, index=False, startrow=len(
            edict) + len(HDR_DOC), startcol=0)
        workbook = writer.book
        ws = writer.sheets['Sheet1']
        date_format = workbook.add_format(
            {'num_format': 'yyyy-mm-dd hh:mm:ss.000'})
        rowidx = 1
        for docline in HDR_DOC:
            cellidx = 'A%i' % rowidx
            # ws[cellidx] = '#'+docline
            ws.write(cellidx, '#' + docline)
            rowidx += 1
        for key, value in edict.items():
            keyidx = 'A%i' % rowidx
            validx = 'B%i' % rowidx
            #ws[keyidx] = key
            #ws[validx] = value
            ws.write(keyidx, key)
            if key == 'time':
                if value.tzinfo is not None:
                    # Excel doesn't support timezone information
                    # so this should strip that off
                    value = datetime(value.year, value.month, value.day,
                                     value.hour, value.minute, value.second,
                                     value.microsecond)
                ws.write_datetime(validx, value, date_format)
            else:
                ws.write(validx, value)
            rowidx += 1
        workbook.close()
    else:
        ext = 'csv'
        filename = os.path.join(directory, '%s_phases.%s' % (edict['id'], ext))
        f = open(filename, 'wt')
        typedict = {'latitude': '%.4f',
                    'longitude': '%.4f',
                    'magnitude': '%.1f',
                    'depth': '%.1f'}
        for docline in HDR_DOC:
            f.write('#%%%s\n' % docline)
        for key, value in edict.items():
            if key in typedict:
                fmt = '#%s = ' + typedict[key] + '\n'
            elif isinstance(value, int):
                fmt = '#%s = %i\n'
            elif isinstance(value, float):
                fmt = '#%s = %i\n'
            else:
                fmt = '#%s = %s\n'
                value = str(value)
            f.write(fmt % (key, value))

        df.to_csv(f, index=False)
        f.close()
    return filename


if __name__ == '__main__':
    main()
