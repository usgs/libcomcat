#!/usr/bin/env python

from datetime import datetime,timedelta
from urllib import request
from urllib.parse import urlparse,urlencode
import json
from xml.dom import minidom
import re
from collections import OrderedDict
import calendar
import sys
from io import StringIO
import tempfile
import os
import warnings
import time

#third party imports
from impactutils.time.ancient_time import HistoricTime
from obspy.core.event import read_events
from pandas import DataFrame

URL_TEMPLATE = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/[EVENTID].geojson'
CATALOG_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/catalogs'
CONTRIBUTORS_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/contributors'
SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson'
TIMEOUT = 60
TIMEFMT = '%Y-%m-%dT%H:%M:%S'

WEEKSECS = 86400*7
WAITSECS = 3 #number of seconds to wait after failing download before trying again

TIMEFMT1 = '%Y-%m-%dT%H:%M:%S'
TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%f'
DATEFMT = '%Y-%m-%d'

def makedict(dictstring):
    try:
        parts = dictstring.split(':')
        key = parts[0]
        value = parts[1]
        return {key:value}
    except:
        raise Exception('Could not create a single key dictionary out of %s' % dictstring)

def maketime(timestring):
    outtime = None
    try:
        outtime = HistoricTime.strptime(timestring,TIMEFMT1)
    except:
        try:
            outtime = HistoricTime.strptime(timestring,TIMEFMT2)
        except:
            try:
                outtime = HistoricTime.strptime(timestring,DATEFMT)
            except:
                raise Exception('Could not parse time or date from %s' % timestring)
    return outtime

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
           eventid=None,
           includedeleted=False,
           includesuperseded=False,
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
           reviewstatus=None):
    """Search the ComCat database for events matching input criteria.

    This search function is a wrapper around the ComCat Web API described here:
    
    https://earthquake.usgs.gov/fdsnws/event/1/

    Some of the search parameters described there are NOT implemented here, usually because they do not 
    apply to GeoJSON search results, which we are getting here and parsing into Python data structures.

    This function returns a list of SummaryEvent objects, described elsewhere in this package.

    Usage:
      TODO
    
    :param starttime:
      Python datetime - Limit to events on or after the specified start time. 
    :param endtime:
      Python datetime - Limit to events on or before the specified end time. 
    :param updatedafter:
      Python datetime - Limit to events updated after the specified time.
    :param minlatitude:
      Limit to events with a latitude larger than the specified minimum.
    :param maxlatitude:
      Limit to events with a latitude smaller than the specified maximum.
    :param minlongitude:
      Limit to events with a longitude larger than the specified minimum.
    :param maxlongitude:
      Limit to events with a longitude smaller than the specified maximum.
    :param latitude:
      Specify the latitude to be used for a radius search.
    :param longitude:
      Specify the longitude to be used for a radius search.
    :param maxradiuskm:
      Limit to events within the specified maximum number of kilometers 
      from the geographic point defined by the latitude and longitude parameters.
    :param maxradius:
      Limit to events within the specified maximum number of degrees 
      from the geographic point defined by the latitude and longitude parameters.
    :param catalog:
      Limit to events from a specified catalog.
    :param contributor:
      Limit to events contributed by a specified contributor.
    :param eventid:
      Select a specific event by ID; event identifiers are data center specific.
    :param includedeleted:
      Specify if deleted products should be incuded. NOTE: Only works when specifying eventid parameter.
    :param includesuperseded:
      Specify if superseded products should be included. This also includes all 
      deleted products, and is mutually exclusive to the includedeleted parameter. 
      NOTE: Only works when specifying eventid parameter.
    :param limit:
      Limit the results to the specified number of events.  
      NOTE, this will be throttled by this Python API to the supported Web API limit of 20,000.
    :param maxdepth:
      Limit to events with depth less than the specified maximum.
    :param maxmagnitude:
      Limit to events with a magnitude smaller than the specified maximum.
    :param mindepth:
      Limit to events with depth more than the specified minimum.
    :param minmagnitude:
      Limit to events with a magnitude larger than the specified minimum.
    :param offset:
      Return results starting at the event count specified, starting at 1.
    :param orderby:
      Order the results. The allowed values are:
        - time order by origin descending time
        - time-asc order by origin ascending time
        - magnitude order by descending magnitude
        - magnitude-asc order by ascending magnitude
    :param alertlevel:
      Limit to events with a specific PAGER alert level. The allowed values are:
      - green Limit to events with PAGER alert level "green".
      - yellow Limit to events with PAGER alert level "yellow".
      - orange Limit to events with PAGER alert level "orange".
      - red Limit to events with PAGER alert level "red".
    :param eventtype:
      Limit to events of a specific type. NOTE: "earthquake" will filter non-earthquake events.
    :param maxcdi:
      Maximum value for Maximum Community Determined Intensity reported by DYFI.
    :param maxgap:
      Limit to events with no more than this azimuthal gap.
    :param maxmmi:
      Maximum value for Maximum Modified Mercalli Intensity reported by ShakeMap.
    :param maxsig:
      Limit to events with no more than this significance.
    :param mincdi:
      Minimum value for Maximum Community Determined Intensity reported by DYFI.
    :param minfelt:
      Limit to events with this many DYFI responses.
    :param mingap:
      Limit to events with no less than this azimuthal gap.
    :param minsig:
      Limit to events with no less than this significance.
    :param producttype:
      Limit to events that have this type of product associated. Example producttypes:
       - moment-tensor
       - focal-mechanism
       - shakemap
       - losspager
       - dyfi
    :param productcode:
      Return the event that is associated with the productcode. 
      The event will be returned even if the productcode is not 
      the preferred code for the event. Example productcodes:
       - nn00458749
       - at00ndf1fr
    :param reviewstatus:
      Limit to events with a specific review status. The different review statuses are:
       - automatic Limit to events with review status "automatic".
       - reviewed Limit to events with review status "reviewed".
    """
    #getting the inputargs must be the first line of the method!
    inputargs = locals().copy()
    newargs = {}
    for key,value in inputargs.items():
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

    segments = _get_time_segments(starttime,endtime)
    events = []

    for stime,etime in segments:
        newargs['starttime'] = stime
        newargs['endtime'] = etime
        events += _search(**newargs)

    return events

def get_catalogs():
    """Get the list of catalogs available in ComCat.

    :returns:
      List of catalogs available in ComCat (see the catalog parameter in search() method.)
    """
    fh = request.urlopen(CATALOG_SEARCH_TEMPLATE,timeout=TIMEOUT)
    data = fh.read().decode('utf8')
    fh.close()
    root = minidom.parseString(data)
    catalogs = root.getElementsByTagName('Catalog')
    catlist = []
    for catalog in catalogs:
        catlist.append(catalog.firstChild.data)
    root.unlink()
    return catlist

def get_contributors():
    """Get the list of contributors available in ComCat.

    :returns:
      List of contributors available in ComCat (see the contributor parameter in search() method.)
    """
    fh = request.urlopen(CONTRIBUTORS_SEARCH_TEMPLATE,timeout=TIMEOUT)
    data = fh.read().decode('utf8')
    fh.close()
    root = minidom.parseString(data)
    contributors = root.getElementsByTagName('Contributor')
    conlist = []
    for contributor in contributors:
        conlist.append(contributor.firstChild.data)
    root.unlink()
    return conlist

def get_detail_data_frame(events,get_all_magnitudes=False,
                          get_all_tensors=False,
                          get_all_focal=False):
    """Take the results of a search and extract the detailed event informat in a pandas DataFrame.

    Usage:
      TODO
    
    :param events:
      List of SummaryEvent objects as returned by search() function.
    :param get_all_magnitudes:
      Boolean indicating whether to return all magnitudes in results for each event.
    :param get_all_tensors:
      Boolean indicating whether to return all moment tensors in results for each event.
    :param get_all_focal:
      Boolean indicating whether to return all focal mechanisms in results for each event.
    
    :returns:  
      Pandas DataFrame with one row per event, and all relevant information in columns.
    """
    df = DataFrame()
    for event in events:
        detail = event.getDetailEvent()
        edict = detail.toDict(get_all_magnitudes=get_all_magnitudes,
                              get_all_tensors=get_all_tensors,
                              get_all_focal=get_all_focal)
        df = df.append(edict,ignore_index=True)
    return df
        
def get_summary_data_frame(events):
    """Take the results of a search and extract the summary event informat in a pandas DataFrame.

    Usage:
      TODO
    
    :param events:
      List of SummaryEvent objects as returned by search() function.
    
    :returns:  
      Pandas DataFrame with one row per event, and columns:
       - id (string) Authoritative ComCat event ID.
       - time (datetime) Authoritative event origin time.
       - latitude (float) Authoritative event latitude.
       - longitude (float) Authoritative event longitude.
       - depth (float) Authoritative event depth.
       - magnitude (float) Authoritative event magnitude.
    """
    df = DataFrame()
    for event in events:
        edict = event.toDict()
        df = df.append(edict,ignore_index=True)
    return df

def _get_moment_tensor_info(tensor,get_angles=False):
    if tensor.hasProperty('beachball-source'):
        msource = tensor['beachball-source']
    elif tensor.hasProperty('beachball-type'):
        msource = tensor['beachball-type']
    else:
        msource = 'unknown'
        
    edict = OrderedDict()
    edict['%s_mrr' % msource] = tensor['tensor-mrr']
    edict['%s_mtt' % msource] = tensor['tensor-mtt']
    edict['%s_mpp' % msource] = tensor['tensor-mpp']
    edict['%s_mrt' % msource] = tensor['tensor-mrt']
    edict['%s_mrp' % msource] = tensor['tensor-mrp']
    edict['%s_mtp' % msource] = tensor['tensor-mtp']
    if get_angles:
        edict['%s_np1_strike' % msource] = tensor['nodal-plane-1-strike']
        edict['%s_np1_dip' % msource] = tensor['nodal-plane-1-dip']
        if tensor.hasProperty('nodal-plane-1-rake'):
            edict['%s_np1_rake' % msource] = tensor['nodal-plane-1-rake']
        else:
            edict['%s_np1_rake' % msource] = tensor['nodal-plane-1-slip']
        edict['%s_np2_strike' % msource] = tensor['nodal-plane-2-strike']
        edict['%s_np2_dip' % msource] = tensor['nodal-plane-2-dip']
        if tensor.hasProperty('nodal-plane-2-rake'):
            edict['%s_np2_rake' % msource] = tensor['nodal-plane-2-rake']
        else:
            edict['%s_np2_rake' % msource] = tensor['nodal-plane-2-slip']
    return edict

def _get_focal_mechanism_info(focal):
    msource = focal['eventsource']
    edict = OrderedDict()
    edict['%s_np1_strike' % msource] = focal['nodal-plane-1-strike']
    edict['%s_np1_dip' % msource] = focal['nodal-plane-1-dip']
    if focal.hasProperty('nodal-plane-1-rake'):
        edict['%s_np1_rake' % msource] = focal['nodal-plane-1-rake']
    else:
        edict['%s_np1_rake' % msource] = focal['nodal-plane-1-slip']
    edict['%s_np2_strike' % msource] = focal['nodal-plane-2-strike']
    edict['%s_np2_dip' % msource] = focal['nodal-plane-2-dip']
    if focal.hasProperty('nodal-plane-2-rake'):
        edict['%s_np2_rake' % msource] = focal['nodal-plane-2-rake']
    else:
        edict['%s_np2_rake' % msource] = focal['nodal-plane-2-slip']
    return edict
    

def _get_time_segments(starttime,endtime):
    #startsecs = int(starttime.strftime('%s'))
    startsecs = calendar.timegm(starttime.timetuple())
    #endsecs = int(endtime.strftime('%s'))
    endsecs = calendar.timegm(endtime.timetuple())
    starts = list(range(startsecs,endsecs,WEEKSECS))
    ends = list(range(startsecs+WEEKSECS+1,endsecs+WEEKSECS,WEEKSECS))
    if ends[-1] > endsecs:
        ends[-1] = endsecs
    segments = []
    if len(starts) != len(ends):
        raise IndexError('Number of time segment starts/ends does not match for times: "%s" and "%s"' % (starttime,endtime))
    sys.stderr.write('Breaking search up into %i segments...\n' % len(starts))
    for start,end in zip(starts,ends):
        segments.append((HistoricTime.utcfromtimestamp(start),HistoricTime.utcfromtimestamp(end)))

    return segments
        
def _search(**newargs):
    if 'starttime' in newargs:
        newargs['starttime'] = newargs['starttime'].strftime(TIMEFMT)
    if 'endtime' in newargs:
        newargs['endtime'] = newargs['endtime'].strftime(TIMEFMT)
    if 'updatedafter' in newargs:
        newargs['updatedafter'] = newargs['updatedafter'].strftime(TIMEFMT)
        
    paramstr = urlencode(newargs)
    url = SEARCH_TEMPLATE+'&'+paramstr
    try:
        fh = request.urlopen(url,timeout=TIMEOUT)
        data = fh.read().decode('utf8')
        fh.close()
        jdict = json.loads(data)
        events = []
        for feature in jdict['features']:
            events.append(SummaryEvent(feature))
    except urllib.error.HTTPError as htpe:
        if htpe.code == 503:
            try:
                time.sleep(WAITSECS)
                fh = request.urlopen(url,timeout=TIMEOUT)
                data = fh.read().decode('utf8')
                fh.close()
                jdict = json.loads(data)
                events = []
                for feature in jdict['features']:
                    events.append(SummaryEvent(feature))
            except Exception as msg:
                raise Exception('Error downloading data from url %s.  "%s".' % (url,msg))
    except Exception as msg:
        raise Exception('Error downloading data from url %s.  "%s".' % (url,msg))
            
    return events

class SummaryEvent(object):
    """Wrapper around summary feature as returned by ComCat GeoJSON search results.
    """
    def __init__(self,feature):
        """Instantiate a SummaryEvent object with a feature.
        
        See summary documentation here:

        https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php

        :param feature:
          GeoJSON feature as described at above URL.
        """
        self._jdict = feature.copy()

    @property
    def latitude(self):
        """Authoritative origin latitude.
        """
        return self._jdict['geometry']['coordinates'][1]

    @property
    def longitude(self):
        """Authoritative origin longitude.
        """
        return self._jdict['geometry']['coordinates'][0]

    @property
    def depth(self):
        """Authoritative origin depth.
        """
        return self._jdict['geometry']['coordinates'][2]

    @property
    def id(self):
        """Authoritative origin ID.
        """
        return self._jdict['id']

    @property
    def time(self):
        """Authoritative origin time.
        """
        itime = self._jdict['properties']['time']
        itime_secs = itime//1000
        dtime = datetime.utcfromtimestamp(itime_secs)
        dt = timedelta(milliseconds=itime-itime_secs)
        dtime = dtime + dt
        return dtime

    @property
    def magnitude(self):
        """Authoritative origin magnitude.
        """
        return self._jdict['properties']['mag']

    def __repr__(self):
        tpl = (self.id,str(self.time),self.latitude,self.longitude,self.depth,self.magnitude)
        return '%s %s (%.3f,%.3f) %.1f km M%.1f' % tpl
    
    @property
    def properties(self):
        """List of summary event properties (retrievable from object with [] operator).
        """
        return list(self._jdict['properties'].keys())

    def hasProduct(self,product):
        """Test to see whether a given product exists for this event.
        
        :param product:
          Product to search for.
        :returns:
          Boolean indicating whether that product exists or not.
        """
        if product not in self._jdict['properties']['types'].split(',')[1:]:
            return False
        return True

    def hasProperty(self,key):
        """Test to see whether a property with a given key is present in list of properties.
        
        :param key:
          Property to search for.
        :returns:
          Boolean indicating whether that key exists or not.
        """
        if key not in self._jdict['properties']:
            return False
        return True

    def __getitem__(self,key):
        """Extract SummaryEvent property using the [] operator.
        
        :param key:
          Property to extract.
        :returns:
          Desired property.
        """
        if key not in self._jdict['properties']:
            raise AttributeError('No property %s found for event %s.' % (key,self.id))
        return self._jdict['properties'][key]
    
    def getDetailEvent(self):
        """Instantiate a DetailEvent object from the URL found in the summary.
        
        :returns:
          DetailEvent version of SummaryEvent.
        """
        durl = self._jdict['properties']['detail']
        return DetailEvent(durl)

    def toDict(self):
        """Render the SummaryEvent origin information as an OrderedDict().
        
        :returns:
          Dictionary containing fields:
            - id (string) Authoritative ComCat event ID.
            - time (datetime) Authoritative event origin time.
            - latitude (float) Authoritative event latitude.
            - longitude (float) Authoritative event longitude.
            - depth (float) Authoritative event depth.
            - magnitude (float) Authoritative event magnitude.
        """
        edict = OrderedDict()
        edict['id'] = self.id,
        edict['time'] = self.time,
        edict['latitude'] = self.latitude,
        edict['longitude'] = self.longitude,
        edict['depth'] = self.depth,
        edict['magnitude'] = self.magnitude
        return edict
    
class DetailEvent(object):
    """Wrapper around detailed event as returned by ComCat GeoJSON search results.
    """
    def __init__(self,eventid_or_url):
        """Instantiate a DetailEvent object with an event ID or url pointing to detailed GeoJSON.
        
        See detailed documentation here:

        https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson_detail.php

        :param eventid_or_url:
          String indicating event ID or a URL pointing to a detailed GeoJSON event.
        """
        parsed_url = urlparse(eventid_or_url)
        if bool(parsed_url.scheme):
            url = eventid_or_url
        else:
            url = URL_TEMPLATE.replace('[EVENTID]',eventid_or_url)
        try:
            fh = request.urlopen(url,timeout=TIMEOUT)
            data = fh.read().decode('utf-8')
            fh.close()
            self._jdict = json.loads(data)
        except Exception as e:
            raise Exception('Could not connect to ComCat server.').with_traceback(e.__traceback__)
        
    def __repr__(self):
        tpl = (self.id,str(self.time),self.latitude,self.longitude,self.depth,self.magnitude)
        return '%s %s (%.3f,%.3f) %.1f km M%.1f' % tpl
        
    @property
    def latitude(self):
        """Authoritative origin latitude.
        """
        return self._jdict['geometry']['coordinates'][1]

    @property
    def longitude(self):
        """Authoritative origin longitude.
        """
        return self._jdict['geometry']['coordinates'][0]

    @property
    def depth(self):
        """Authoritative origin depth.
        """
        return self._jdict['geometry']['coordinates'][2]

    @property
    def id(self):
        """Authoritative origin ID.
        """
        return self._jdict['id']

    @property
    def time(self):
        """Authoritative origin time.
        """
        itime = self._jdict['properties']['time']
        itime_secs = itime//1000
        dtime = datetime.utcfromtimestamp(itime_secs)
        dt = timedelta(milliseconds=itime-itime_secs)
        dtime = dtime + dt
        return dtime

    @property
    def magnitude(self):
        """Authoritative origin magnitude.
        """
        return self._jdict['properties']['mag']
    
    @property
    def properties(self):
        """List of summary event properties (retrievable from object with [] operator).
        """
        return list(self._jdict['properties'].keys())

    def hasProduct(self,product):
        """Return a boolean indicating whether given product can be extracted from DetailEvent.

        :param product:
          Product to search for.
        :returns:
          Boolean indicating whether that product exists or not.
        """
        if product in self._jdict['properties']['products']:
            return True
        return False

    def toDict(self,get_all_magnitudes=False,get_all_tensors=False,get_all_focal=False):
        """Return known origin, focal mechanism, and moment tensor information for an event.

        :param get_all_magnitudes:
          Boolean indicating whether all known magnitudes for this event should be returned.
          NOTE: The ComCat phase-data product's QuakeML file will be downloaded and parsed,
          which takes extra time.
        :param get_all_tensors:
          Boolean indicating whether all known moment tensors for this event should be returned.
        :param get_all_focal:
          Boolean indicating whether all known focal mechanisms for this event should be returned.
        :returns:
          OrderedDict with the same fields as returned by SummaryEvent.toDict(), plus
          additional magnitude/magnitude type fields, moment tensor and focal mechanism 
          data.  The number and name of the fields will vary by what data is available.
        """
        edict = OrderedDict()
        edict['id'] = self.id
        edict['time'] = self.time
        edict['latitude'] = self.latitude
        edict['longitude'] = self.longitude
        edict['depth'] = self.depth
        edict['magnitude'] = self.magnitude
        edict['magtype'] = self._jdict['properties']['magType']

        if not get_all_tensors:
            if self.hasProduct('moment-tensor'):
                edict.update(_get_moment_tensor_info(self.getProduct('moment-tensor')))
        else:
            if self.hasProduct('moment-tensor'):
                num_tensors = self.getNumVersions('moment-tensor')
                for idx in range(0,num_tensors):
                    tensor = self.getProduct('moment-tensor',auth=False,index=idx)
                    edict.update(_get_moment_tensor_info(tensor,get_angles=get_all_focal))
        if not get_all_focal:
            if self.hasProduct('focal-mechanism'):
                edict.update(_get_focal_mechanism_info(self.getProduct('focal-mechanism')))
        else:
            if self.hasProduct('focal-mechanism'):
                num_focal = self.getNumVersions('focal-mechanism')
                for idx in range(0,num_focal):
                    focal = self.getProduct('focal-mechanism',auth=False,index=idx)
                    edict.update(_get_focal_mechanism_info(focal))

        if get_all_magnitudes:
            handle,tmpfile = tempfile.mkstemp()
            os.close(handle)
            phase_data = self.getProduct('phase-data')
            hasContent,content_url = phase_data.hasContent('quakeml.xml')
            try:
                phase_data.getContent('quakeml.xml',filename=tmpfile)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    catalog = read_events(tmpfile)
                    event = catalog.events[0]
                    imag = 1
                    if get_all_magnitudes:
                        for magnitude in event.magnitudes:
                            edict['magnitude%i' % imag] = magnitude.mag
                            edict['magtype%i' % imag] = magnitude.magnitude_type
                            imag += 1
            except:
                raise Exception('Failed to retrieve quakeml.xml file from phase-data product (%s).' % content_url)
            finally:
                os.remove(tmpfile)
                
        return edict

    def getNumVersions(self,product_name):
        """Count the number of versions of a product (origin, shakemap, etc.) available for this event.
        
        :param product_name:
          Name of product to query.
        :returns:
          Number of versions of a given product.
        """
        if not self.hasProduct(product_name):
            raise AttributeError('Event %s has no product of type %s' % (self.id,product_name))
        return len(self._jdict['properties']['products'][product_name])
    
    def getProduct(self,product_name,auth=True,index=0):
        """Retrieve a Product object from this DetailEvent.

        :param product_name:
          Name of product (origin, shakemap, etc.) to retrieve.
        :param auth:
          Boolean indicating whether to retrieve the authoritative version of the product.
        :param index:
          If auth==False, then use this index value (starts at 0) of desired version.
        :returns:
          Product object, from authoritative version or version at a given index.
        """
        if not self.hasProduct(product_name):
            raise AttributeError('Event %s has no product of type %s' % (self.id,product))
        # if user wants authoritative product
        if auth:
            weights = []
            for product in self._jdict['properties']['products'][product_name]:
                weights.append(product['preferredWeight'])
            idx = weights.index(max(weights))
            return Product(product_name,self._jdict['properties']['products'][product_name][idx])

        # if user wants a product by index (default=0)
        if index >= self.getNumVersions(product_name):
            tpl = (index,product_name)
            raise IndexError('%i is outside the range of the number of versions of product %s' % (tpl))
        return Product(product_name,self._jdict['properties']['products'][product_name][index])
    
class Product(object):
    """Class describing a Product from detailed GeoJSON feed.  Products contain properties and file contents.
    """
    def __init__(self,product_name,product):
        """Create a product class from the product found within the detailed event GeoJSON.

        :param product_name:
          Name of Product (origin, shakemap, etc.)
        :param product:
          Product data to be copied from DetailEvent.
        """
        self._product_name = product_name
        self._product = product.copy()

    def hasContent(self,regexp):
        """Determine whether the Product contains any content matching the input regular expression.

        :param regexp:
          Regular expression which should match one of the content files in the Product.
        :returns:
          Boolean indicating whether content matching input regexp exists.
        """
        for contentkey in self._product['contents'].keys():
            if re.search(regexp,contentkey) is not None:
                url = self._product['contents'][contentkey]['url']
                return (True,url)

        return False

    def __repr__(self):
        ncontents = len(self._product['contents'])
        tpl = (self._product_name,ncontents)
        return 'Product %s containing %i content files.' % tpl

    def getContentName(self,regexp):
        for contentkey in self._product['contents'].keys():
            if re.search(regexp,contentkey) is not None:
                url = self._product['contents'][contentkey]['url']
                parts = urlparse(url)
                content_name = parts.path.split('/')[-1]
                return content_name
        return None
                
    
    def getContent(self,regexp,filename=None):
        """Find and download the file associated with the input content regular expression.

        :param regexp:
          Regular expression which should match one of the content files in the Product.
        :param filename:
          Filename to which content should be downloaded.
        :returns:
          The URL from which the content was downloaded.
        """
        for contentkey,content in self._product['contents'].items():
            #print(contentkey)
            if re.search(regexp,contentkey) is not None:
                url = content['url']
                fh = request.urlopen(url,timeout=TIMEOUT)
                data = fh.read()
                fh.close()
                f = open(filename,'wb')
                f.write(data)
                f.close()
                return None

        raise AttributeError('Could not find any content matching input %s' % regexp)
        return url
    
    def hasProperty(self,key):
        """Determine if this Product contains a given property.

        :param key:
          Property to search for.
        :returns:
          Boolean indicating whether that key exists or not.
        """
        if key not in self._product['properties']:
            return False
        return True

    @property
    def properties(self):
        """List of summary event properties (retrievable from object with [] operator).
        """
        return list(self._product['properties'].keys())
    
    def __getitem__(self,key):
        """Extract Product property using the [] operator.
        
        :param key:
          Property to extract.
        :returns:
          Desired property.
        """
        if key not in self._product['properties']:
            raise AttributeError('No property %s found in %s product.' % (key,self._product_name))
        return self._product['properties'][key]
