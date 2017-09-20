#stdlib imports
from datetime import datetime,timedelta
from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlparse
import json
from collections import OrderedDict
import tempfile
import os
import warnings
import re
from enum import Enum

#third party imports
from obspy.core.event import read_events
import pandas as pd
import dateutil

#constants
#the detail event URL template
URL_TEMPLATE = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/[EVENTID].geojson'
#the search template for a detail event that may include one or both of includesuperseded/includedeleted.
SEARCH_DETAIL_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&eventid=%s&includesuperseded=%s&includedeleted=%s'
TIMEOUT = 60 #how long should we wait for a url to return?
WAITSECS = 3

class VersionOption(Enum):
    LAST = 1
    FIRST = 2
    ALL = 3

def _get_moment_tensor_info(tensor,get_angles=False):
    """Internal - gather up tensor components and focal mechanism angles.
    """
    msource = tensor['eventsource']+'_'+tensor['eventsourcecode']
    if tensor.hasProperty('derived-magnitude-type'):
        msource += '_'+tensor['derived-magnitude-type']
    elif tensor.hasProperty('beachball-type'):
        btype = tensor['beachball-type']
        if btype.find('/') > -1:
            btype = btype.split('/')[-1]
        msource += '_'+btype

    edict = OrderedDict()
    edict['%s_mrr' % msource] = float(tensor['tensor-mrr'])
    edict['%s_mtt' % msource] = float(tensor['tensor-mtt'])
    edict['%s_mpp' % msource] = float(tensor['tensor-mpp'])
    edict['%s_mrt' % msource] = float(tensor['tensor-mrt'])
    edict['%s_mrp' % msource] = float(tensor['tensor-mrp'])
    edict['%s_mtp' % msource] = float(tensor['tensor-mtp'])
    if get_angles and tensor.hasProperty('nodal-plane-1-strike'):
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
    """Internal - gather up focal mechanism angles.
    """
    msource = focal['eventsource']+'_'+focal['eventsourcecode']
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
    def location(self):
        """Earthquake location string.
        """
        return self._jdict['properties']['place']

    @property
    def url(self):
        """ComCat URL.
        """
        return self._jdict['properties']['url']
    
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
        time_in_msec = self._jdict['properties']['time']
        time_in_sec = time_in_msec//1000
        msec = time_in_msec - (time_in_sec*1000)
        dtime = datetime.utcfromtimestamp(time_in_sec)
        dt = timedelta(milliseconds=msec)
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

    def getDetailURL(self):
        """Instantiate a DetailEvent object from the URL found in the summary.
        
        :returns:
          URL for detailed version of event.
        """
        durl = self._jdict['properties']['detail']
        return durl
    
    def getDetailEvent(self,includedeleted=False,includesuperseded=False):
        """Instantiate a DetailEvent object from the URL found in the summary.
        :param includedeleted:
          Boolean indicating wheather to return versions of products that have been deleted.
          Cannot be used with includesuperseded.
        :param includesuperseded:
          Boolean indicating wheather to return versions of products that have been replaced by
          newer versions.
          Cannot be used with includedeleted.
        :returns:
          DetailEvent version of SummaryEvent.
        """
        if includesuperseded and includedeleted:
            raise RuntimeError('includedeleted and includesuperseded cannot be used together.')
        if not includedeleted and not includesuperseded:
            durl = self._jdict['properties']['detail']
            return DetailEvent(durl)
        else:
            true_false = {True:'true',False:'false'}
            deleted = true_false[includedeleted]
            superseded = true_false[includesuperseded]
            url = SEARCH_DETAIL_TEMPLATE % (self.id,superseded,deleted)
            return DetailEvent(url)

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
        edict['id'] = self.id
        edict['time'] = self.time
        edict['location'] = self.location
        edict['latitude'] = self.latitude
        edict['longitude'] = self.longitude
        edict['depth'] = self.depth
        edict['magnitude'] = self.magnitude
        edict['url'] = self.url
        return edict
    
class DetailEvent(object):
    """Wrapper around detailed event as returned by ComCat GeoJSON search results.
    """
    def __init__(self,url):
        """Instantiate a DetailEvent object with a url pointing to detailed GeoJSON.
        
        See detailed documentation here:

        https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson_detail.php

        :param url:
          String indicating a URL pointing to a detailed GeoJSON event.
        """
        try:
            fh = request.urlopen(url,timeout=TIMEOUT)
            data = fh.read().decode('utf-8')
            fh.close()
            self._jdict = json.loads(data)
        except HTTPError as htpe:
            try:
                fh = request.urlopen(url,timeout=TIMEOUT)
                data = fh.read().decode('utf-8')
                fh.close()
                self._jdict = json.loads(data)
            except Exception as msg:
                raise Exception('Could not connect to ComCat server - %s.' % url).with_traceback(e.__traceback__)
    
    def __repr__(self):
        tpl = (self.id,str(self.time),self.latitude,self.longitude,self.depth,self.magnitude)
        return '%s %s (%.3f,%.3f) %.1f km M%.1f' % tpl

    @property
    def location(self):
        """Earthquake location string.
        """
        return self._jdict['properties']['place']

    @property
    def url(self):
        """ComCat URL.
        """
        return self._jdict['properties']['url']
    
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
        time_in_msec = self._jdict['properties']['time']
        time_in_sec = time_in_msec//1000
        msec = time_in_msec - (time_in_sec*1000)
        dtime = datetime.utcfromtimestamp(time_in_sec)
        dt = timedelta(milliseconds=msec)
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
        """Extract DetailEvent property using the [] operator.
        
        :param key:
          Property to extract.
        :returns:
          Desired property.
        """
        if key not in self._jdict['properties']:
            raise AttributeError('No property %s found for event %s.' % (key,self.id))
        return self._jdict['properties'][key]
        
    
    def toDict(self,catalog=None,
               get_all_magnitudes=False,
               get_all_tensors=False,
               get_all_focals=False):
        """Return known origin, focal mechanism, and moment tensor information for a DetailEvent.

        :param catalog:
          Retrieve the primary event information (time,lat,lon...) from the catalog given.
          If no source for this information exists, an AttributeError will be raised.
        :param get_all_magnitudes:
          Boolean indicating whether all known magnitudes for this event should be returned.
          NOTE: The ComCat phase-data product's QuakeML file will be downloaded and parsed,
          which takes extra time.
        :param get_all_tensors:
          Boolean indicating whether all known moment tensors for this event should be returned.
        :param get_all_focals:
          Boolean indicating whether all known focal mechanisms for this event should be returned.
        :returns:
          OrderedDict with the same fields as returned by SummaryEvent.toDict(), plus
          additional magnitude/magnitude type fields, moment tensor and focal mechanism 
          data.  The number and name of the fields will vary by what data is available.
        """
        edict = OrderedDict()

        if catalog is None:
            edict['id'] = self.id
            edict['time'] = self.time
            edict['location'] = self.location
            edict['latitude'] = self.latitude
            edict['longitude'] = self.longitude
            edict['depth'] = self.depth
            edict['magnitude'] = self.magnitude
            edict['magtype'] = self._jdict['properties']['magType']
            edict['url'] = self.url
        else:
            try:
                phase_sources = []
                origin_sources = []
                if self.hasProduct('phase-data'):
                    phase_sources = [p.source for p in self.getProducts('phase-data',source='all')]
                if self.hasProduct('origin'):
                    origin_sources = [o.source for o in self.getProducts('origin',source='all')]
                if catalog in phase_sources:
                    phasedata = self.getProducts('phase-data',source=catalog)[0]
                elif catalog in origin_sources:
                    phasedata = self.getProducts('origin',source=catalog)[0]
                else:
                    msg = 'DetailEvent %s has no phase-data or origin products for source %s'
                    raise AttributeError(msg % (self.id,catalog))
                edict['id'] = phasedata['eventsource']+phasedata['eventsourcecode']
                edict['time'] = dateutil.parser.parse(phasedata['eventtime'])
                edict['location'] = self.location
                edict['latitude'] = float(phasedata['latitude'])
                edict['longitude'] = float(phasedata['longitude'])
                edict['depth'] = float(phasedata['depth'])
                edict['magnitude'] = float(phasedata['magnitude'])
                edict['magtype'] = phasedata['magnitude-type']
            except AttributeError as ae:
                raise ae

        if not get_all_tensors:
            if self.hasProduct('moment-tensor'):
                tensor = self.getProducts('moment-tensor')[0]
                edict.update(_get_moment_tensor_info(tensor,get_angles=True))
        else:
            if self.hasProduct('moment-tensor'):
                tensors = self.getProducts('moment-tensor',source='all',version=VersionOption.ALL)
                for tensor in tensors:
                    edict.update(_get_moment_tensor_info(tensor,get_angles=True))
        if not get_all_focals:
            if self.hasProduct('focal-mechanism'):
                edict.update(_get_focal_mechanism_info(self.getProducts('focal-mechanism')[0]))
        else:
            if self.hasProduct('focal-mechanism'):
                focals = self.getProducts('focal-mechanism',source='all',version=VersionOption.ALL)
                for focal in focals:
                    edict.update(_get_focal_mechanism_info(focal))

        if get_all_magnitudes:
            handle,tmpfile = tempfile.mkstemp()
            os.close(handle)
            try:
                phase_data = self.getProducts('phase-data')[0]
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
    
    def getProducts(self,product_name,source='preferred',version=VersionOption.LAST):
        """Retrieve a Product object from this DetailEvent.

        :param product_name:
          Name of product (origin, shakemap, etc.) to retrieve.
        :param version:
          An enum value from VersionOption (PREFERRED,FIRST,ALL).
        :param source:
          Any one of: 
            - 'preferred' Get version(s) of products from preferred source.
            - 'all' Get version(s) of products from all sources.
            - Any valid source network for this type of product ('us','ak',etc.)
        :returns:
          List of Product objects.
        """
        if not self.hasProduct(product_name):
            raise AttributeError('Event %s has no product of type %s' % (self.id,product_name))
                
        weights = [product['preferredWeight'] for product in self._jdict['properties']['products'][product_name]]
        sources = [product['source'] for product in self._jdict['properties']['products'][product_name]]
        times = [product['updateTime'] for product in self._jdict['properties']['products'][product_name]]
        indices = list(range(0,len(times)))
        df = pd.DataFrame({'weight':weights,'source':sources,'time':times,'index':indices})
        #we need to add a version number column here, ordinal sorted by update time, starting at 1
        #for each unique source.
        #first sort the dataframe by source and then time
        df = df.sort_values(['source','time'])
        df['version'] = 0
        psources = []
        pversion = 1
        for idx,row in df.iterrows():
            if row['source'] not in psources:
                psources.append(row['source'])
                pversion = 1
            df.loc[idx,'version'] = pversion
            pversion += 1

        if source == 'preferred':
            idx = weights.index(max(weights))
            prefsource = self._jdict['properties']['products'][product_name][idx]['source']
            df = df[df['source'] == prefsource]
            df = df.sort_values('time')
        elif source == 'all':
            df = df.sort_values(['source','time'])
        else:
            df = df[df['source'] == source]
            df = df.sort_values('time')

        #if we don't have any versions of products, raise an exception
        if not len(df):
            raise AttributeError('No products found for source "%s".' % source)

        products = []
        usources = set(sources)
        if source == 'all': #dataframe includes all sources
            for source in usources:
                df_source = df[df['source'] == source]
                df_source = df_source.sort_values('time')
                if version == VersionOption.LAST:
                    idx = df_source.iloc[-1]['index']
                    pversion = df_source.iloc[-1]['version']
                    product = Product(product_name,pversion,self._jdict['properties']['products'][product_name][idx])
                    products.append(product)
                elif version == VersionOption.FIRST:
                    idx = df_source.iloc[0]['index']
                    pversion = df_source.iloc[0]['version']
                    product = Product(product_name,pversion,self._jdict['properties']['products'][product_name][idx])
                    products.append(product)
                elif version == VersionOption.ALL:
                    for idx,row in df_source.iterrows():
                        idx = row['index']
                        pversion = row['version']
                        product = Product(product_name,pversion,self._jdict['properties']['products'][product_name][idx])
                        products.append(product)
                else:
                    raise(AttributeError('No VersionOption defined for %s' % version))
        else: #dataframe only includes one source
            if version == VersionOption.LAST:
                idx = df.iloc[-1]['index']
                pversion = df.iloc[-1]['version']
                product = Product(product_name,pversion,self._jdict['properties']['products'][product_name][idx])
                products.append(product)
            elif version == VersionOption.FIRST:
                idx = df.iloc[0]['index']
                pversion = df.iloc[0]['version']
                product = Product(product_name,pversion,self._jdict['properties']['products'][product_name][idx])
                products.append(product)
            elif version == VersionOption.ALL:
                for idx,row in df.iterrows():
                    idx = row['index']
                    pversion = row['version']
                    product = Product(product_name,pversion,self._jdict['properties']['products'][product_name][idx])
                    products.append(product)
            else:
                raise(AttributeError('No VersionOption defined for %s' % version))

        return products
        

    
class Product(object):
    """Class describing a Product from detailed GeoJSON feed.  Products contain properties and file contents.
    """
    def __init__(self,product_name,version,product):
        """Create a product class from the product found within the detailed event GeoJSON.

        :param product_name:
          Name of Product (origin, shakemap, etc.)
        :param version:
          Best guess as to ordinal version of the product.
        :param product:
          Product data to be copied from DetailEvent.
        """
        self._product_name = product_name
        self._version = version
        self._product = product.copy()
        
    def getContentsMatching(self,regexp):
        """Find all contents that match the input regex, ordered by shortest to longest.

        :param regexp:
          Regular expression which should match one of the content files in the Product.
        :returns:
          List of contents matching
        """
        contents = []
        if not len(self._product['contents']):
            return contents
            
        for contentkey in self._product['contents'].keys():
            url = self._product['contents'][contentkey]['url']
            parts = urlparse(url)
            fname = parts.path.split('/')[-1]
            if re.search(regexp+'$',fname):
                contents.append(fname)
        return contents
        
    def __repr__(self):
        ncontents = len(self._product['contents'])
        tpl = (self._product_name,self.source,self.update_time,ncontents)
        return 'Product %s from %s updated %s containing %i content files.' % tpl

    def getContentName(self,regexp):
        """Get the shortest filename matching input regular expression.

        For example, if the shakemap product has contents called grid.xml and grid.xml.zip, 
        and the input regexp is grid.xml, then grid.xml will be matched.

        :param regexp:
          Regular expression to use to search for matching contents.
        :returns:
          Shortest file name to match input regexp, or None if no matches found.
        """
        content_name = 'a'*1000
        found = False
        for contentkey,content in self._product['contents'].items():
            if re.search(regexp+'$',contentkey) is None:
                continue
            url = content['url']
            parts = urlparse(url)
            fname = parts.path.split('/')[-1]
            if len(fname) < len(content_name):
                content_name = fname
                found = True
        if found:
            return content_name
        else:
            return None

    def getContentURL(self,regexp):
        """Get the URL for the shortest filename matching input regular expression.

        For example, if the shakemap product has contents called grid.xml and grid.xml.zip, 
        and the input regexp is grid.xml, then grid.xml will be matched.

        :param regexp:
          Regular expression to use to search for matching contents.
        :returns:
          URL for shortest file name to match input regexp, or None if no matches found.
        """
        content_name = 'a'*1000
        found = False
        content_url = ''
        for contentkey,content in self._product['contents'].items():
            if re.search(regexp+'$',contentkey) is None:
                continue
            url = content['url']
            parts = urlparse(url)
            fname = parts.path.split('/')[-1]
            if len(fname) < len(content_name):
                content_name = fname
                content_url = url
                found = True
        if found:
            return content_url
        else:
            return None

        
    def getContent(self,regexp,filename=None):
        """Find and download the shortest file name matching the input regular expression.

        :param regexp:
          Regular expression which should match one of the content files in the Product.
        :param filename:
          Filename to which content should be downloaded.
        :returns:
          The URL from which the content was downloaded.
        :raises:
          Exception if content could not be downloaded from ComCat after two tries.
        """
        content_name = 'a'*1000
        content_url = None
        for contentkey,content in self._product['contents'].items():
            if re.search(regexp+'$',contentkey) is None:
                continue
            url = content['url']
            parts = urlparse(url)
            fname = parts.path.split('/')[-1]
            if len(fname) < len(content_name):
                content_name = fname
                content_url = url
        if content_url is None:
            raise AttributeError('Could not find any content matching input %s' % regexp)

        try:
            fh = request.urlopen(url,timeout=TIMEOUT)
            data = fh.read()
            fh.close()
            f = open(filename,'wb')
            f.write(data)
            f.close()
        except HTTPError as htpe:
            time.sleep(WAITSECS)
            try:
                fh = request.urlopen(url,timeout=TIMEOUT)
                data = fh.read()
                fh.close()
                f = open(filename,'wb')
                f.write(data)
                f.close()
            except Exception as msg:
                raise Exception('Could not download %s from %s.' % (content_name,url))
            
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
    def preferred_weight(self):
        """The weight assigned to this product by ComCat.
        """
        return self._product['preferredWeight']

    @property
    def source(self):
        """The contributing source for this product.
        """
        return self._product['source']

    @property
    def update_time(self):
        """The datetime for when this product was updated.
        """
        time_in_msec = self._product['updateTime']
        time_in_sec = time_in_msec//1000
        msec = time_in_msec - (time_in_sec*1000)
        dtime = datetime.utcfromtimestamp(time_in_sec)
        dt = timedelta(milliseconds=msec)
        dtime = dtime + dt
        return dtime

    @property
    def version(self):
        """The best guess for the ordinal version number of this product.
        """
        return self._version
    
    @property
    def properties(self):
        """List of product properties (retrievable from object with [] operator).
        """
        return list(self._product['properties'].keys())

    @property
    def contents(self):
        """List of product properties (retrievable from object with getContent() method).
        """
        return list(self._product['contents'].keys())
    
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
