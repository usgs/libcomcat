#!/usr/bin/env python

# stdlib imports
import argparse
import os.path
import sys
from datetime import datetime, timedelta
import logging

# local imports
import libcomcat
from libcomcat.search import search, get_event_by_id
from libcomcat.utils import (maketime, makedict, check_ccode,
                             get_country_bounds, filter_by_country,
                             BUFFER_DISTANCE_KM)
from libcomcat.logging import setup_logger

# third party imports
import numpy as np
import pandas as pd
from shapely.geometry import Point


class MyFormatter(argparse.RawTextHelpFormatter,
                  argparse.ArgumentDefaultsHelpFormatter):
    pass


def _get_product_from_detail(detail, product, contents, folder,
                             version, source, list_only=False):
    if not detail.hasProduct(product):
        return False

    products = detail.getProducts(
        product, source=source, version=version)

    ic = len(products)
    eventfolder = os.path.join(folder, detail.id)
    if not os.path.isdir(eventfolder):
        os.makedirs(eventfolder)

    nzeros = int(np.ceil(np.log10(len(products))))
    fmt = '%%0%ii' % (nzeros + 1)
    eventid = detail.id
    for product in products:
        iversion = product.version
        prodsource = product.source
        for content in contents:
            if not list_only:
                content_name = product.getContentName(content)
                sversion = fmt % iversion
                fname = '%s_%s_%s_%s' % (
                    eventid, prodsource, sversion, content_name)
                filename = os.path.join(eventfolder, fname)
                try:
                    product.getContent(content_name, filename=filename)
                except Exception as e:
                    print('Could not download %s from event %s.  Continuing...' % (
                        content_name, detail.id))
                    continue
                logging.info('Downloaded %s %s to %s\n' %
                             (eventid, content, filename))
            else:
                url = product.getContentURL(content_name)
                print(url)
        iversion += 1

        ic -= 1
    return True


def get_parser():
    desc = '''Download product content files from USGS ComCat.

    To download ShakeMap grid.xml files for a box around New Zealand during 2013:

    %(prog)s shakemap "grid.xml" -o /home/user/newzealand -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01

    Note that when specifying a search box that crosses the -180/180 meridian, you simply specify longitudes
    as you would if you were not crossing that meridian.

    Note: Some product content files do not always have the same name, usually because they incorporate the event ID
    into the file name, such as with most of the files associated with the finite-fault product.  To download these files,
    you will need to input a unique fragment of the file name that can be matched in a search.

    For example, to retrieve all of the coulomb input files for the finite-fault product, you would construct your
    search like this:
    %(prog)s finite-fault _coulomb.inp -o ~/tmp/chile -b -76.509 -49.804  -67.72 -17.427 -s 2007-01-01 -e 2016-05-01 -m 6.5 9.9

    To retrieve the moment rate function files, do this:
    %(prog)s finite-fault .mr -o ~/tmp/chile -b -76.509 -49.804  -67.72 -17.427 -s 2007-01-01 -e 2016-05-01 -m 6.5 9.9
    '''
    parser = argparse.ArgumentParser(
        description=desc, formatter_class=MyFormatter)
    # positional arguments
    parser.add_argument('product', metavar='PRODUCT',
                        help='The name of the desired product (shakemap, dyfi, etc.)')
    parser.add_argument('contents', metavar='CONTENTLIST', nargs='*',
                        help='The names of the product contents (grid.xml, stationlist.txt, etc.) ')
    # optional arguments
    parser.add_argument('--version', action='version',
                        version=libcomcat.__version__)
    parser.add_argument('-o', '--output-folder', dest='outputFolder', default=os.getcwd(),
                        help='Folder where output files should be written (must exist).')
    parser.add_argument('-b', '--bounds', metavar=('lonmin', 'lonmax', 'latmin', 'latmax'),
                        dest='bounds', type=float, nargs=4,
                        help='Bounds to constrain event search [lonmin lonmax latmin latmax]')

    country_str = '''Specify three character country code and earthquakes
    from inside country polygon (50m resolution) will be returned. Earthquakes
    in the ocean likely will NOT be returned.'''
    parser.add_argument('--country', help=country_str)

    buffer_str = '''Use in conjunction with --country. Specify a buffer in km
    around country border where events will be selected.
    '''
    parser.add_argument('--buffer', help=buffer_str,
                        type=int, default=BUFFER_DISTANCE_KM)

    parser.add_argument('-r', '--radius', dest='radius', metavar=('lat', 'lon', 'rmax'), type=float,
                        nargs=3, help='Search radius in KM (use instead of bounding box)')
    parser.add_argument('-s', '--start-time', dest='startTime', type=maketime,
                        help='Start time for search (defaults to ~30 days ago). YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-e', '--end-time', dest='endTime', type=maketime,
                        help='End time for search (defaults to current date/time). YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-a', '--after', dest='after', type=maketime,
                        help='Limit to events modified after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('-m', '--mag-range', metavar=('minmag', 'maxmag'), dest='magRange', type=float, nargs=2,
                        help='Min/max magnitude to restrict search.')
    parser.add_argument('-c', '--catalog', dest='catalog',
                        help='Source catalog from which products derive (atlas, centennial, etc.)')
    parser.add_argument('-n', '--contributor', dest='contributor',
                        help='Source contributor (who loaded product) (us, nc, etc.)')
    parser.add_argument('-i', '--event-id', dest='eventid',
                        help='Event ID from which to download product contents.')
    parser.add_argument('-p', '--product-property', dest='productProperties', type=makedict,
                        help='Product property (reviewstatus:approved).')
    parser.add_argument('-t', '--event-property', dest='eventProperties',
                        help='Event property (alert:yellow, status:REVIEWED, etc.).', type=makedict)
    parser.add_argument('-v', '--event-type', dest='eventType',
                        help='Event type (earthquake, "volcanic eruption", etc.).')
    parser.add_argument('-l', '--list-url', dest='list_only', action='store_true',
                        help='Only list urls for contents in events that match criteria.')

    parser.add_argument('--get-version', dest='version', choices=['first', 'last', 'all', 'preferred'],
                        help='Get contents for first, last, preferred or all versions of product.',
                        default='preferred')
    parser.add_argument('--get-source', dest='source', default='preferred',
                        help='Get contents for the "preferred" source, "all" sources, or a specific source ("us").')
    parser.add_argument('--host',
                        help='Specify a different comcat *search* host than earthquake.usgs.gov.')

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

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    setup_logger(args.logfile, args.loglevel)

    if args.eventid:
        detail = get_event_by_id(args.eventid, includesuperseded=True)
        _get_product_from_detail(detail, args.product, args.contents,
                                 args.outputFolder, args.version,
                                 args.source, list_only=args.list_only)
        sys.exit(0)

    tsum = (args.bounds is not None) + \
        (args.radius is not None) + (args.country is not None)
    if tsum != 1:
        print('Please specify a bounding box, radius, or country code.')
        sys.exit(1)

    latitude = None
    longitude = None
    radiuskm = None
    lonmin = latmin = lonmax = latmax = None

    if args.startTime is None:
        starttime = datetime.utcnow() - timedelta(days=30)
        print('You did not specify a search start time, defaulting to %s' %
              str(starttime))
    else:
        starttime = args.startTime

    if args.endTime is None:
        endtime = datetime.utcnow()
        print('You did not specify a search end time, defaulting to %s' %
              str(endtime))
    else:
        endtime = args.endTime

    bounds = None
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
        bounds = (lonmin, lonmax, latmin, latmax)

    if args.country:
        ccode = args.country
        if not check_ccode(ccode):
            curl = 'https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2'
            fmt = '%s is not a valid ISO 3166 country code. See %s for the list.'
            tpl = (ccode, curl)
            print(fmt % tpl)
            sys.exit(1)
        bounds = get_country_bounds(ccode, args.buffer)  # this returns a list

    minmag = 0.0
    maxmag = 9.9
    if args.magRange:
        minmag = args.magRange[0]
        maxmag = args.magRange[1]

    if isinstance(bounds, tuple) or bounds is None:
        events = search(starttime=starttime,
                        endtime=endtime,
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
                        producttype=args.product,
                        eventtype=args.eventType,
                        maxmagnitude=maxmag,
                        minmagnitude=minmag,
                        host=args.host)
    else:
        events = []
        for i, tbounds in enumerate(bounds):
            lonmin, lonmax, latmin, latmax = tbounds
            tevents = search(starttime=starttime,
                             endtime=endtime,
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
                             producttype=args.product,
                             eventtype=args.eventType,
                             maxmagnitude=maxmag,
                             minmagnitude=minmag,
                             host=args.host)
            events += tevents

    if not len(events):
        print('No events found matching your search criteria. Exiting.')
        sys.exit(0)

    if args.country:
        ids = [event.id for event in events]
        lats = [event.latitude for event in events]
        lons = [event.longitude for event in events]
        df = pd.DataFrame({'id': ids, 'latitude': lats, 'longitude': lons})
        df2 = filter_by_country(df, ccode, buffer_km=args.buffer)
        events = [event for event in events if event.id in df2['id'].unique()]

    for event in events:
        logging.debug('Retrieving products for event %s...' % event.id)
        if not event.hasProduct(args.product):
            continue
        if args.country:
            elon = event.longitude
            elat = event.latitude
            point = Point(elon, elat)
        try:
            detail = event.getDetailEvent(includesuperseded=True)
        except Exception as e:
            print(
                'Failed to retrieve detail event for event %s... continuing.' % event.id)
            continue
        _get_product_from_detail(detail, args.product,
                                 args.contents, args.outputFolder,
                                 args.version, args.source, list_only=args.list_only)

    sys.exit(0)


if __name__ == '__main__':
    main()
