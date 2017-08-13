#!/usr/bin/env python

from datetime import datetime,timedelta
from urllib import request
from urllib.parse import urlparse,urlencode
import json
import re
from collections import OrderedDict
import calendar
import sys
from io import StringIO
import tempfile
import os
import warnings

#third party imports
from impactutils.time.ancient_time import HistoricTime
from obspy.core.event import read_events

URL_TEMPLATE = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/[EVENTID].geojson'
SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson'
TIMEOUT = 60
TIMEFMT = '%Y-%m-%dT%H:%M:%S'

WEEKSECS = 86400*7


def get_time_segments(starttime,endtime):
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
           includearrivals=False,
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

    segments = get_time_segments(starttime,endtime)
    events = []
    for stime,etime in segments:
        newargs['starttime'] = stime
        newargs['endtime'] = etime
        events += _search(**newargs)

    return events
        
def _search(**newargs):
    if 'starttime' in newargs:
        newargs['starttime'] = newargs['starttime'].strftime(TIMEFMT)
    if 'endtime' in newargs:
        newargs['endtime'] = newargs['endtime'].strftime(TIMEFMT)
    if 'updatedafter' in newargs:
        newargs['updatedafter'] = newargs['updatedafter'].strftime(TIMEFMT)
        
    paramstr = urlencode(newargs)
    url = SEARCH_TEMPLATE+'&'+paramstr
    fh = request.urlopen(url,timeout=TIMEOUT)
    data = fh.read().decode('utf8')
    fh.close()
    jdict = json.loads(data)
    events = []
    for feature in jdict['features']:
        events.append(SummaryEvent(feature))

    return events

class SummaryEvent(object):
    def __init__(self,feature):
        self._jdict = feature.copy()

    @property
    def latitude(self):
        return self._jdict['geometry']['coordinates'][1]

    @property
    def longitude(self):
        return self._jdict['geometry']['coordinates'][0]

    @property
    def depth(self):
        return self._jdict['geometry']['coordinates'][2]

    @property
    def id(self):
        return self._jdict['id']

    @property
    def time(self):
        itime = self._jdict['properties']['time']
        itime_secs = itime//1000
        dtime = datetime.utcfromtimestamp(itime_secs)
        dt = timedelta(milliseconds=itime-itime_secs)
        dtime = dtime + dt
        return dtime

    @property
    def magnitude(self):
        return self._jdict['properties']['mag']

    def __repr__(self):
        tpl = (self.id,str(self.time),self.latitude,self.longitude,self.depth,self.magnitude)
        return '%s %s (%.3f,%.3f) %.1f km M%.1f' % tpl
    
    @property
    def properties(self):
        return self._jdict['properties'].copy()

    def hasProperty(self,key):
        if key not in self._jdict['properties']:
            return False
        return True

    def __getitem__(self,key):
        if key not in self._jdict['properties']:
            raise AttributeError('No property %s found for event %s.' % (key,self.id))
        return self._jdict['properties'][key]
    
    def getDetailEvent(self):
        durl = self._jdict['properties']['detail']
        return DetailEvent(durl)

    def toDict(self):
        edict = OrderedDict()
        edict['id'] = self.id,
        edict['time'] = self.time,
        edict['latitude'] = self.latitude,
        edict['longitude'] = self.longitude,
        edict['depth'] = self.depth,
        edict['magnitude'] = self.magnitude
        return edict
    
class DetailEvent(object):
    def __init__(self,eventid_or_url):
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
        return self._jdict['geometry']['coordinates'][1]

    @property
    def longitude(self):
        return self._jdict['geometry']['coordinates'][0]

    @property
    def depth(self):
        return self._jdict['geometry']['coordinates'][2]

    @property
    def id(self):
        return self._jdict['id']

    @property
    def time(self):
        itime = self._jdict['properties']['time']
        itime_secs = itime//1000
        dtime = datetime.utcfromtimestamp(itime_secs)
        dt = timedelta(milliseconds=itime-itime_secs)
        dtime = dtime + dt
        return dtime

    @property
    def magnitude(self):
        return self._jdict['properties']['mag']
    
    @property
    def properties(self):
        return self._jdict['properties'].copy()

    def hasProduct(self,product):
        if product in self._jdict['properties']['products']:
            return True
        return False

    def toDict(self,get_all_magnitudes=False,get_all_tensors=False,get_all_focal=False):
        if self.hasProduct('moment-tensor'):
            angle_dict = self.getProduct('moment-tensor')
        elif self.hasProduct('focal-mechanism'):
            angle_dict = self.getProduct('focal-mechanism')
        else:
            angle_dict = None
        edict = OrderedDict()
        edict['id'] = self.id
        edict['time'] = self.time
        edict['latitude'] = self.latitude
        edict['longitude'] = self.longitude
        edict['depth'] = self.depth
        edict['magnitude'] = self.magnitude
        edict['magtype'] = self._jdict['properties']['magType']
        if angle_dict:
            edict['strike1'] = angle_dict['nodal-plane-1-strike']
            edict['dip1'] = angle_dict['nodal-plane-1-dip']
            if angle_dict.hasProperty('nodal-plane-1-rake'):
                edict['rake1'] = angle_dict['nodal-plane-1-rake']
            else:
                edict['rake1'] = angle_dict['nodal-plane-1-slip']
            edict['strike2'] = angle_dict['nodal-plane-2-strike']
            edict['dip2'] = angle_dict['nodal-plane-2-dip']
            if angle_dict.hasProperty('nodal-plane-2-rake'):
                edict['rake2'] = angle_dict['nodal-plane-2-rake']
            else:
                edict['rake2'] = angle_dict['nodal-plane-2-slip']
        if angle_dict.hasProperty('tensor-mrp'):
            edict['mrr'] = angle_dict['tensor-mrr']
            edict['mpp'] = angle_dict['tensor-mpp']
            edict['mtt'] = angle_dict['tensor-mtt']
            edict['mrp'] = angle_dict['tensor-mrp']
            edict['mrt'] = angle_dict['tensor-mrt']
            edict['mtp'] = angle_dict['tensor-mtp']

        if get_all_magnitudes:
            handle,tmpfile = tempfile.mkstemp()
            os.close(handle)
            phase_data = self.getProduct('phase-data')
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
                raise Exception('Failed to retrieve quakeml.xml file from phase-data product.')
            finally:
                os.remove(tmpfile)
                            
        if get_all_tensors:
            num_tensors = self.getNumProducts('moment-tensor')
            for idx in range(0,num_tensors):
                tensor = self.getProduct('moment-tensor',auth=False,index=idx)
                handle,tmpfile = tempfile.mkstemp()
                os.close(handle)
                try:
                    tensor.getContent('quakeml.xml',filename=tmpfile)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        catalog = read_events(tmpfile)
                        event = catalog.events[0]
                        if get_all_focal:
                            for mechanism in event.focal_mechanisms:
                                if hasattr(mechanism,'nodal_planes'):
                                    plane1 = mechanism.nodal_planes.nodal_plane1
                                    plane2 = mechanism.nodal_planes.nodal_plane2
                        

                
                
                except:
                    raise exception('failed to retrieve quakeml.xml file from phase-data product.')
                finally:
                    os.remove(tmpfile)
        return edict

    def getNumProducts(self,product_name):
        if not self.hasProduct(product_name):
            raise AttributeError('Event %s has no product of type %s' % (self.id,product))
        return len(self._jdict['properties']['products'][product_name])
    
    def getProduct(self,product_name,auth=True,index=0):
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
        return Product(product_name,self._jdict['products'][product_name][index])
    
class Product(object):
    def __init__(self,product_name,product):
        self._product_name = product_name
        self._product = product.copy()

    def hasContent(self,regexp):
        for contentkey in self._product['contents'].keys():
            if re.search(regexp,contentkey) is not None:
                return True

        return False

    def __repr__(self):
        ncontents = len(self._product['contents'])
        tpl = (self._product_name,ncontents)
        return 'Product %s containing %i content files.' % tpl
    
    def getContent(self,regexp,filename=None):
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
    

    def hasProperty(self,key):
        if key not in self._product['properties']:
            return False
        return True
    
    def __getitem__(self,key):
        if key not in self._product['properties']:
            raise AttributeError('No property %s found in %s product.' % (key,self._product_name))
        return self._product['properties'][key]
