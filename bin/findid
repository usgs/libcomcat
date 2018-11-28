#!/usr/bin/env python

# stdlib
import argparse
from datetime import datetime, timedelta
import sys

# third party
from obspy.geodetics.base import gps2dist_azimuth
import pandas as pd
import numpy as np

# local imports
from libcomcat.search import search
from libcomcat.utils import maketime
from libcomcat.dataframes import get_summary_data_frame

# constants
TIMEFMT = '%Y-%m-%dT%H:%M:%S'
FILETIMEFMT = '%Y-%m-%d %H:%M:%S'
SEARCH_RADIUS = 100
TIME_WINDOW = 16  # seconds

pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 100)


def get_parser():
    desc = '''Find the id(s) of the closest earthquake to input parameters.

    To print the authoritative id of the event closest in time and space
    inside a 100 km, 16 second window to "2017-08-30 03:00:33 UTC 37.571   118.888":


    %(prog)s  2017-08-30T03:00:33 37.571 -118.888

    To make a similar query but with the time shifted by 2 minutes, and a
    custom time window of 3 minutes:

    %(prog)s  -w 180 2017-08-30T03:00:33 37.571 -118.888

    To print the authoritative id AND the url of the event closest in time and space to that point:

    %(prog)s  -u -w 180 2017-08-30T03:00:33 37.571 -118.888

    To print all of the ids associated with the event closest to above:

    %(prog)s -a 2015-03-29T23:48:31 -4.763 152.561

    To print the id(s), time/distance deltas, and azimuth from input to nearest event:

    %(prog)s -v 2015-03-29T23:48:31 -4.763 152.561

    Notes:
     - The time format at the command line must be of the form "YYYY-MM-DDTHH:MM:SS".  The time format in an input csv file
     can be either :YYYY-MM-DDTHH:MM:SS" OR "YYYY-MM-DD HH:MM:SS".  This is because on the command line the argument parser
     would be confused by the space between the date and the time, whereas in the csv file the input files are being split
     by commas.
     - Supplying the -a option with the -f option has no effect.
    '''

    parser = argparse.ArgumentParser(
        description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    # positional arguments
    parser.add_argument('time', type=maketime,
                        help='Time of earthquake, formatted as YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('lat', type=float, help='Latitude of earthquake')
    parser.add_argument('lon', type=float, help='Longitude of earthquake')

    # optional arguments
    parser.add_argument('-r', '--radius', type=float,
                        help='Change search radius from default of %.0f km.' % SEARCH_RADIUS)
    parser.add_argument('-w', '--window', type=float,
                        help='Change time window of %.0f seconds.' % TIME_WINDOW)
    parser.add_argument('-a', '--all', dest='printAll', action='store_true',
                        help='Print all ids associated with event.')
    parser.add_argument('-u', '--url', dest='printURL', action='store_true',
                        help='Print URL associated with event.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print time/distance deltas, and azimuth from input parameters to event.')
    return parser


def get_event_info(time, lat, lon, twindow, radius):
    start_time = time - timedelta(seconds=twindow)
    end_time = time + timedelta(seconds=twindow)
    events = search(starttime=start_time,
                    endtime=end_time,
                    latitude=lat,
                    longitude=lon,
                    maxradiuskm=radius)

    if not len(events):
        return None

    df = get_summary_data_frame(events)
    df['distance'] = 0
    df['timedelta'] = 0
    df['azimuth'] = 0
    df['time_dist_norm'] = 0
    for idx, row in df.iterrows():
        distance, az, azb = gps2dist_azimuth(
            lat, lon, row['latitude'], row['longitude'])
        row_time = row['time'].to_pydatetime()
        dtime = row_time - time
        dt = np.abs(dtime.days * 86400 + dtime.seconds)
        df.loc[idx, 'distance'] = distance
        df.loc[idx, 'timedelta'] = dt
        df.loc[idx, 'azimuth'] = az
        dt_norm = dt / twindow
        dd_norm = distance / radius
        df.loc[idx, 'time_dist_norm'] = (dt_norm + dd_norm) / 2.0

    return df


def main():
    parser = get_parser()

    args = parser.parse_args()

    twindow = TIME_WINDOW
    if args.window:
        twindow = args.window
    # set distance thresholds
    radius = SEARCH_RADIUS
    if args.radius:
        radius = args.radius

    event_df = get_event_info(args.time, args.lat, args.lon, twindow, radius)

    if event_df is None:
        print('No events found matching your search criteria. Exiting.')
        sys.exit(0)

    nearest = event_df[event_df['time_dist_norm']
                       == event_df['time_dist_norm'].min()]
    if args.printAll:
        for idx, row in event_df.iterrows():
            print(row['id'])
            for key, value in row.items():
                if key == 'id':
                    continue
                print('\t' + key + ' : ' + str(value))
        sys.exit(0)

    if args.verbose:
        print(nearest)
        sys.exit(0)

    if args.printURL:
        print(nearest['url'].values[0])
        sys.exit(0)

    print(nearest['id'].values[0])


if __name__ == '__main__':
    main()
