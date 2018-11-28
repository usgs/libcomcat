# stdlib imports
from datetime import datetime, timedelta
from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlparse, urlencode
import json
import calendar
import sys
import time

# third party imports
from impactutils.time.ancient_time import HistoricTime
import numpy as np

# local imports
from libcomcat.classes import SummaryEvent, DetailEvent

# constants
# url template for counting events
HOST = 'earthquake.usgs.gov'
CATALOG_COUNT_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson'
SEARCH_TEMPLATE = 'https://[HOST]/fdsnws/event/1/query?format=geojson'
TIMEOUT = 60  # how long do we wait for a url to return?
TIMEFMT = '%Y-%m-%dT%H:%M:%S'
WEEKSECS = 86400 * 7  # number of seconds in a week
WAITSECS = 3  # number of seconds to wait after failing download before trying again
SEARCH_LIMIT = 20000  # maximum number of events ComCat will return in one search


def count(starttime=None,
          endtime=None,
          updatedafter=None,
          minlatitude=None,
          maxlatitude=None,
          minlongitude=None,
          maxlongitude=None,
          latitude=None,
          longitude=None,
          maxradiuskm=None,
          maxradius=None,
          catalog=None,
          contributor=None,
          limit=20000,
          maxdepth=1000,
          maxmagnitude=10.0,
          mindepth=-100,
          minmagnitude=0,
          offset=1,
          orderby='time-asc',
          alertlevel=None,
          eventtype='earthquake',
          maxcdi=None,
          maxgap=None,
          maxmmi=None,
          maxsig=None,
          mincdi=None,
          minfelt=None,
          mingap=None,
          minsig=None,
          producttype=None,
          productcode=None,
          reviewstatus=None,
          verbose=False):
    """Ask the ComCat database for the number of events matching input criteria.

    This count function is a wrapper around the ComCat Web API described here:

    https://earthquake.usgs.gov/fdsnws/event/1/ (see count section)

    Some of the search parameters described there are NOT implemented here, usually because they do not 
    apply to GeoJSON search results, which we are getting here and parsing into Python data structures.

    This function returns a list of SummaryEvent objects, described elsewhere in this package.

    Usage:
      TODO

    Args:
        starttime (datetime):  Python datetime - Limit to events on or after 
            the specified start time. 
        endtime (datetime):
            Python datetime - Limit to events on or before the specified end time. 
        updatedafter (datetime):
            Limit to events updated after the specified time.
        minlatitude (float):
            Limit to events with a latitude larger than the specified minimum.
        maxlatitude (float):
            Limit to events with a latitude smaller than the specified maximum.
        minlongitude (float):
            Limit to events with a longitude larger than the specified minimum.
        maxlongitude (float):
            Limit to events with a longitude smaller than the specified maximum.
        latitude (float):
            Specify the latitude to be used for a radius search.
        longitude (float):
            Specify the longitude to be used for a radius search.
        maxradiuskm (float):
            Limit to events within the specified maximum number of kilometers 
            from the geographic point defined by the latitude and longitude parameters.
        maxradius (float):
            Limit to events within the specified maximum number of degrees 
            from the geographic point defined by the latitude and longitude parameters.
        catalog (str):
            Limit to events from a specified catalog.
        contributor (str):
            Limit to events contributed by a specified contributor.
        limit (int):
            Limit the results to the specified number of events.  
            NOTE, this will be throttled by this Python API to the supported 
            Web API limit of 20,000.
        maxdepth (float):
            Limit to events with depth less than the specified maximum.
        maxmagnitude (float):
            Limit to events with a magnitude smaller than the specified maximum.
        mindepth (float):
            Limit to events with depth more than the specified minimum.
        minmagnitude (float):
            Limit to events with a magnitude larger than the specified minimum.
        offset (int):
            Return results starting at the event count specified, starting at 1.
        orderby (str):
            Order the results. The allowed values are:
              - time order by origin descending time
              - time-asc order by origin ascending time
              - magnitude order by descending magnitude
              - magnitude-asc order by ascending magnitude
        alertlevel (str):
            Limit to events with a specific PAGER alert level. The allowed values are:
              - green Limit to events with PAGER alert level "green".
              - yellow Limit to events with PAGER alert level "yellow".
              - orange Limit to events with PAGER alert level "orange".
              - red Limit to events with PAGER alert level "red".
        eventtype (str):
            Limit to events of a specific type. NOTE: "earthquake" will filter non-earthquake events.
        maxcdi (float):
            Maximum value for Maximum Community Determined Intensity reported by DYFI.
        maxgap (float):
            Limit to events with no more than this azimuthal gap.
        maxmmi (float):
            Maximum value for Maximum Modified Mercalli Intensity reported by ShakeMap.
        maxsig (float):
            Limit to events with no more than this significance.
        mincdi (float):
            Minimum value for Maximum Community Determined Intensity reported by DYFI.
        minfelt (int):
            Limit to events with this many DYFI responses.
        mingap (float):
            Limit to events with no less than this azimuthal gap.
        minsig (float):
            Limit to events with no less than this significance.
        producttype (str):
            Limit to events that have this type of product associated. Example producttypes:
               - moment-tensor
               - focal-mechanism
               - shakemap
               - losspager
               - dyfi
        productcode (str):
            Return the event that is associated with the productcode. 
            The event will be returned even if the productcode is not 
            the preferred code for the event. Example productcodes:
             - nn00458749
             - at00ndf1fr
        reviewstatus (str):
            Limit to events with a specific review status. The different review statuses are:
               - automatic Limit to events with review status "automatic".
               - reviewed Limit to events with review status "reviewed".
    Returns:
        list: List of SummaryEvent() objects.
    """
    # getting the inputargs must be the first line of the method!
    inputargs = locals().copy()
    newargs = {}
    for key, value in inputargs.items():
        if value is True:
            newargs[key] = 'true'
            continue
        if value is False:
            newargs[key] = 'false'
            continue
        if value is None:
            continue
        newargs[key] = value
    if newargs['limit'] > 20000:
        newargs['limit'] = 20000
    nevents = 0
    segments = _get_time_segments(starttime, endtime, newargs['minmagnitude'])
    iseg = 1

    # remove the verbose element from the arguments
    del newargs['verbose']

    for stime, etime in segments:
        newargs['starttime'] = stime
        newargs['endtime'] = etime
        if verbose:
            sys.stderr.write(
                'Searching time segment %i: %s to %s\n' % (iseg, stime, etime))
        iseg += 1
        nevents += _count(**newargs)

    return nevents


def get_event_by_id(eventid, catalog=None,
                    includedeleted=False,
                    includesuperseded=False,
                    host=None):
    """Search the ComCat database for an event matching the input event id.

    This search function is a wrapper around the ComCat Web API described here:

    https://earthquake.usgs.gov/fdsnws/event/1/

    Some of the search parameters described there are NOT implemented here, usually because they do not 
    apply to GeoJSON search results, which we are getting here and parsing into Python data structures.

    This function returns a DetailEvent object, described elsewhere in this package.

    Usage:
      TODO


    Args:
        eventid (str): Select a specific event by ID; event identifiers are data center specific.
        includesuperseded (bool):
            Specify if superseded products should be included. This also includes all 
            deleted products, and is mutually exclusive to the includedeleted parameter. 
        includedeleted (bool): Specify if deleted products should be incuded. 
        host (str): Replace default ComCat host (earthquake.usgs.gov) with a custom host.
    Returns: DetailEvent object.
    """
    # getting the inputargs must be the first line of the method!
    inputargs = locals().copy()
    newargs = {}
    for key, value in inputargs.items():
        if value is True:
            newargs[key] = 'true'
            continue
        if value is False:
            newargs[key] = 'false'
            continue
        if value is None:
            continue
        newargs[key] = value

    event = _search(**newargs)  # this should be a DetailEvent
    return event


def search(starttime=None,
           endtime=None,
           updatedafter=None,
           minlatitude=None,
           maxlatitude=None,
           minlongitude=None,
           maxlongitude=None,
           latitude=None,
           longitude=None,
           maxradiuskm=None,
           maxradius=None,
           catalog=None,
           contributor=None,
           limit=20000,
           maxdepth=1000,
           maxmagnitude=10.0,
           mindepth=-100,
           minmagnitude=0,
           offset=1,
           orderby='time-asc',
           alertlevel=None,
           eventtype='earthquake',
           maxcdi=None,
           maxgap=None,
           maxmmi=None,
           maxsig=None,
           mincdi=None,
           minfelt=None,
           mingap=None,
           minsig=None,
           producttype=None,
           productcode=None,
           reviewstatus=None,
           host=None,
           enable_limit=False,
           verbose=False):
    """Search the ComCat database for events matching input criteria.

    This search function is a wrapper around the ComCat Web API described here:

    https://earthquake.usgs.gov/fdsnws/event/1/

    Some of the search parameters described there are NOT implemented here, usually because they do not 
    apply to GeoJSON search results, which we are getting here and parsing into Python data structures.

    This function returns a list of SummaryEvent objects, described elsewhere in this package.

    Usage:
      TODO

    Args:
        starttime (datetime):
            Python datetime - Limit to events on or after the specified start time. 
        endtime (datetime):
            Python datetime - Limit to events on or before the specified end time. 
        updatedafter (datetime):
           Python datetime - Limit to events updated after the specified time.
        minlatitude (float):
            Limit to events with a latitude larger than the specified minimum.
        maxlatitude (float):
            Limit to events with a latitude smaller than the specified maximum.
        minlongitude (float):
            Limit to events with a longitude larger than the specified minimum.
        maxlongitude (float):
            Limit to events with a longitude smaller than the specified maximum.
        latitude (float):
            Specify the latitude to be used for a radius search.
        longitude (float):
            Specify the longitude to be used for a radius search.
        maxradiuskm (float):
            Limit to events within the specified maximum number of kilometers 
            from the geographic point defined by the latitude and longitude parameters.
        maxradius (float):
            Limit to events within the specified maximum number of degrees 
            from the geographic point defined by the latitude and longitude parameters.
        catalog (str):
            Limit to events from a specified catalog.
        contributor (str):
            Limit to events contributed by a specified contributor.
        limit (int):
            Limit the results to the specified number of events.  
             NOTE, this will be throttled by this Python API to the supported Web API limit of 20,000.
        maxdepth (float):
            Limit to events with depth less than the specified maximum.
        maxmagnitude (float):
            Limit to events with a magnitude smaller than the specified maximum.
        mindepth (float):
            Limit to events with depth more than the specified minimum.
        minmagnitude (float):
            Limit to events with a magnitude larger than the specified minimum.
        offset (int):
            Return results starting at the event count specified, starting at 1.
        orderby (str):
            Order the results. The allowed values are:
            - time order by origin descending time
            - time-asc order by origin ascending time
            - magnitude order by descending magnitude
            - magnitude-asc order by ascending magnitude
        alertlevel (str):
            Limit to events with a specific PAGER alert level. The allowed values are:
              - green Limit to events with PAGER alert level "green".
              - yellow Limit to events with PAGER alert level "yellow".
              - orange Limit to events with PAGER alert level "orange".
              - red Limit to events with PAGER alert level "red".
        eventtype (str):
            Limit to events of a specific type. NOTE: "earthquake" will filter non-earthquake events.
        maxcdi (float):
            Maximum value for Maximum Community Determined Intensity reported by DYFI.
        maxgap (float):
            Limit to events with no more than this azimuthal gap.
        maxmmi (float):
            Maximum value for Maximum Modified Mercalli Intensity reported by ShakeMap.
        maxsig (float):
            Limit to events with no more than this significance.
        mincdi (float):
            Minimum value for Maximum Community Determined Intensity reported by DYFI.
        minfelt (int):
            Limit to events with this many DYFI responses.
        mingap (float):
            Limit to events with no less than this azimuthal gap.
        minsig (float):
            Limit to events with no less than this significance.
        producttype (str):
            Limit to events that have this type of product associated. Example producttypes:
               - moment-tensor
               - focal-mechanism
               - shakemap
               - losspager
               - dyfi
        productcode (str):
              Return the event that is associated with the productcode. 
              The event will be returned even if the productcode is not 
              the preferred code for the event. Example productcodes:
               - nn00458749
               - at00ndf1fr
        reviewstatus (str):
            Limit to events with a specific review status. The different review statuses are:
                - automatic Limit to events with review status "automatic".
                - reviewed Limit to events with review status "reviewed".
        host (str): 
            Replace default ComCat host (earthquake.usgs.gov) with a custom host.
        enable_limit (bool): Enable 20,000 event search limit. Will turn off searching
            in segments, which is meant to safely avoid that limit.
            Use only when you are certain your search will be small.

    Returns:
        list: List of SummaryEvent() objects.
    """
    # getting the inputargs must be the first line of the method!
    inputargs = locals().copy()
    newargs = {}
    for key, value in inputargs.items():
        if value is True:
            newargs[key] = 'true'
            continue
        if value is False:
            newargs[key] = 'false'
            continue
        if value is None:
            continue
        newargs[key] = value
    if newargs['limit'] > 20000:
        newargs['limit'] = 20000

    # remove the verbose element from the arguments
    del newargs['verbose']
    del newargs['enable_limit']
    if enable_limit:
        events = _search(**newargs)
        return events
    segments = _get_time_segments(starttime, endtime, newargs['minmagnitude'])
    events = []
    iseg = 1
    for stime, etime in segments:
        newargs['starttime'] = stime
        newargs['endtime'] = etime
        if verbose:
            sys.stderr.write(
                'Searching time segment %i: %s to %s\n' % (iseg, stime, etime))
        iseg += 1
        events += _search(**newargs)

    return events


def _get_time_segments(starttime, endtime, minmag):
    if starttime is None:
        starttime = HistoricTime.utcnow() - timedelta(days=30)
    if endtime is None:
        endtime = HistoricTime.utcnow()
    # earthquake frequency table: minmag:earthquakes per day
    freq_table = {0: 3000 / 7,
                  1: 3500 / 14,
                  2: 3000 / 18,
                  3: 4000 / 59,
                  4: 9000 / 151,
                  5: 3000 / 365,
                  6: 210 / 365,
                  7: 20 / 365,
                  8: 5 / 365,
                  9: 0.05 / 365}

    floormag = int(np.floor(minmag))
    ndays = (endtime - starttime).days + 1
    freq = freq_table[floormag]
    nsegments = int(np.ceil((freq * ndays) / SEARCH_LIMIT))
    days_per_segment = int(np.ceil(ndays / nsegments))
    segments = []
    startseg = starttime
    endseg = starttime
    while startseg <= endtime:
        endseg = min(endtime, startseg + timedelta(days_per_segment))
        segments.append((startseg, endseg))
        startseg += timedelta(days=days_per_segment, microseconds=1)
    return segments


def _search(**newargs):
    if 'starttime' in newargs:
        newargs['starttime'] = newargs['starttime'].strftime(TIMEFMT)
    if 'endtime' in newargs:
        newargs['endtime'] = newargs['endtime'].strftime(TIMEFMT)
    if 'updatedafter' in newargs:
        newargs['updatedafter'] = newargs['updatedafter'].strftime(TIMEFMT)
    if 'host' in newargs and newargs['host'] is not None:
        template = SEARCH_TEMPLATE.replace('[HOST]', newargs['host'])
        del newargs['host']
    else:
        template = SEARCH_TEMPLATE.replace('[HOST]', HOST)

    paramstr = urlencode(newargs)
    url = template + '&' + paramstr
    events = []
    # handle the case when they're asking for an event id
    if 'eventid' in newargs:
        return DetailEvent(url)

    try:
        fh = request.urlopen(url, timeout=TIMEOUT)
        data = fh.read().decode('utf8')
        fh.close()
        jdict = json.loads(data)
        events = []
        for feature in jdict['features']:
            events.append(SummaryEvent(feature))
    except HTTPError as htpe:
        if htpe.code == 503:
            try:
                time.sleep(WAITSECS)
                fh = request.urlopen(url, timeout=TIMEOUT)
                data = fh.read().decode('utf8')
                fh.close()
                jdict = json.loads(data)
                events = []
                for feature in jdict['features']:
                    events.append(SummaryEvent(feature))
            except Exception as msg:
                raise Exception(
                    'Error downloading data from url %s.  "%s".' % (url, msg))
    except Exception as msg:
        raise Exception(
            'Error downloading data from url %s.  "%s".' % (url, msg))

    return events


def _count(**newargs):
    if 'starttime' in newargs:
        newargs['starttime'] = newargs['starttime'].strftime(TIMEFMT)
    if 'endtime' in newargs:
        newargs['endtime'] = newargs['endtime'].strftime(TIMEFMT)
    if 'updatedafter' in newargs:
        newargs['updatedafter'] = newargs['updatedafter'].strftime(TIMEFMT)

    paramstr = urlencode(newargs)
    url = CATALOG_COUNT_TEMPLATE + '&' + paramstr
    nevents = 0
    try:
        fh = request.urlopen(url, timeout=TIMEOUT)
        data = fh.read().decode('utf8')
        fh.close()
        jdict = json.loads(data)
        nevents = jdict['count']
    except HTTPError as htpe:
        if htpe.code == 503:
            try:
                time.sleep(WAITSECS)
                fh = request.urlopen(url, timeout=TIMEOUT)
                data = fh.read().decode('utf8')
                fh.close()
                jdict = json.loads(data)
                nevents = jdict['count']
            except Exception as msg:
                raise Exception(
                    'Error downloading data from url %s.  "%s".' % (url, msg))
    except Exception as msg:
        raise Exception(
            'Error downloading data from url %s.  "%s".' % (url, msg))

    return nevents
