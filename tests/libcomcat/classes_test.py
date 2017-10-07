#!/usr/bin/env python

import os.path
import sys
from datetime import datetime,timedelta
import tempfile
import json

from libcomcat.classes import SummaryEvent,DetailEvent,Product,VersionOption
from libcomcat.search import search,get_event_by_id
import pandas as pd

def test_summary():
    eventlist = search(starttime=datetime(1994,1,17,12,30),
                       endtime=datetime(1994,1,18,12,35),
                       minmagnitude=6.6)
    event = eventlist[0]
    assert str(event) == 'ci3144585 1994-01-17 12:30:55.390000 (34.213,-118.537) 18.2 km M6.7'
    assert event.id == 'ci3144585'
    assert event.time == datetime(1994, 1, 17, 12, 30, 55, 390000)
    assert event.latitude == 34.213
    assert event.longitude == -118.537
    assert event.depth == 18.202
    assert event.magnitude == 6.7
    assert 'cdi' in event.properties
    assert event['cdi'] == 8.6
    assert event.hasProduct('shakemap')
    assert event.hasProduct('foo') == False
    try:
        event['foo']
        assert 1 == 2
    except AttributeError as ae:
        pass
    assert event.hasProperty('cdi')
    assert event.hasProperty('foo') == False
    assert isinstance(event.getDetailEvent(),DetailEvent)
    durl = 'https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=ci3144585&format=geojson'
    assert event.getDetailURL() == durl
    try:
        detail = event.getDetailEvent(includedeleted=True,
                                      includesuperseded=True)
        assert 1==2
    except RuntimeError as re:
        pass

    #find an event that has multiple versions of shakemap to test includesuperseded
    #official20110311054624120_30
    eventlist = search(starttime=datetime(2011,3,11,0,0),
                       endtime=datetime(2011,3,12,0,0),
                       minmagnitude=8.8)
    honshu = eventlist[0]
    detail = honshu.getDetailEvent(includesuperseded=True)
    shakemaps = detail.getProducts('shakemap',version=VersionOption.ALL)
    assert shakemaps[1].source == 'atlas'
    assert event.toDict()['depth'] == 18.202

def test_detail_product_versions():
    eventid = 'nn00570710'
    detail = get_event_by_id(eventid,includesuperseded=True)
    pref_origin_pref_source = detail.getProducts('origin',source='preferred',version=VersionOption.LAST)[0]
    pref_origin_pref_source2 = detail.getProducts('origin')[0]
    
    first_origin_pref_source = detail.getProducts('origin',source='preferred',version=VersionOption.FIRST)[0]
    first_origin_us_source = detail.getProducts('origin',source='us',version=VersionOption.FIRST)[0]
    last_origin_us_source = detail.getProducts('origin',source='us',version=VersionOption.LAST)[0]
    
    pref_origins_all_sources = detail.getProducts('origin',source='all',version=VersionOption.LAST)
    first_origins_all_sources = detail.getProducts('origin',source='all',version=VersionOption.FIRST)
    all_origins_all_sources = detail.getProducts('origin',source='all',version=VersionOption.ALL)
    
    assert pref_origin_pref_source.source == 'nn'
    assert pref_origin_pref_source2.source == 'nn'
    assert pref_origin_pref_source.version >= 7
    assert pref_origin_pref_source2.version >= 7
    assert first_origin_pref_source.source == 'nn'
    assert first_origin_pref_source.version == 1
    assert first_origin_us_source.source == 'us'
    assert first_origin_us_source.version == 1
    assert last_origin_us_source.source == 'us'
    assert last_origin_us_source.version >= 5

    sources = []
    for origin in pref_origins_all_sources:
        source = origin.source
        version = origin.version
        assert source not in sources
        sources.append(source)

    sources = []
    for origin in first_origins_all_sources:
        source = origin.source
        version = origin.version
        assert source not in sources
        assert version == 1
        sources.append(source)

    
        
def test_moment_supplement():
    eventid = 'us2000ar20' #2017 M7.1 Mexico City
    detail = get_event_by_id(eventid)
    edict = detail.toDict(get_moment_supplement=True,get_tensors='preferred')
    assert edict['us_Mww_percent_double_couple'] == 0.9992
    
def test_detail():
    eventid = 'ci3144585' #northridge
    url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/%s.geojson' % eventid
    event = DetailEvent(url)
    assert str(event) == 'ci3144585 1994-01-17 12:30:55.390000 (34.213,-118.537) 18.2 km M6.7'
    assert event.hasProduct('shakemap')
    assert event.hasProduct('foo') == False
    assert event.hasProperty('foo') == False
    assert event.hasProperty('time')
    try:
        event['foo']
        assert 1 == 2
    except AttributeError as ae:
        pass

    try:
        event.getNumVersions('foo')
        assert 1 == 2
    except AttributeError as ae:
        pass

    try:
        event.getProducts('foo')
        assert 1 == 2
    except AttributeError as ae:
        pass

    try:
        event.getProducts('shakemap',source='foo')
        assert 1 == 2
    except AttributeError as ae:
        pass
    
    assert event.toDict()['magnitude'] == 6.7

    eventid = 'nc72282711' #Napa 2014 eq, multiple origins and MTs.
    # cievent = get_event_by_id(eventid,catalog='ci')
    # usevent = get_event_by_id(eventid,catalog='us')
    # atevent = get_event_by_id(eventid,catalog='at')
    event = get_event_by_id(eventid)

    phases = event.getProducts('phase-data',source='all')
    
    ncdict = event.toDict(catalog='nc')
    usdict = event.toDict(catalog='us')
    atdict = event.toDict(catalog='at')

    try:
        event.toDict(catalog='foo')
        assert 1 == 2
    except AttributeError as ae:
        pass

    assert ncdict['depth'] == 11.12
    assert usdict['depth'] == 11.25
    assert atdict['depth'] == 9.0

    ncdict_allmags = event.toDict(get_all_magnitudes=True)
    assert ncdict_allmags['magtype3'] == 'Ml'

    ncdict_alltensors = event.toDict(get_tensors='all')
    assert ncdict_alltensors['us_Mwb_mrr'] == 7.63e+16
    ncdict_allfocals = event.toDict(get_focals='all')
    assert ncdict_allfocals['nc_np1_strike'] == '345.0'

    assert event.getNumVersions('shakemap') > 0
    assert isinstance(event.getProducts('shakemap')[0],Product)
    assert event.latitude == 38.2151667
    assert event.longitude == -122.3123333
    assert event.depth == 11.12
    assert event.id == eventid
    assert event.time == datetime(2014, 8, 24, 10, 20, 44, 70000)
    assert 'sources' in event.properties
    assert event['mag'] == 6.02

    #test all of the different functionality of the getProducts() method
    #first, test default behavior (get the most preferred product):
    event = get_event_by_id('nc21323712',includesuperseded=True) #2003 Central California
    pref_shakemap = event.getProducts('shakemap')[0]
    assert pref_shakemap.source == 'atlas'
    assert pref_shakemap.update_time >= datetime(2017, 4, 12, 10, 50, 9, 368000)
    assert pref_shakemap.preferred_weight >= 100000000

    #get the first Atlas shakemap
    first_shakemap = event.getProducts('shakemap',version=VersionOption.FIRST,source='atlas')[0]
    assert first_shakemap.source == 'atlas'
    assert first_shakemap.update_time >= datetime(2015, 2, 4, 6, 1, 33, 400000)
    assert first_shakemap.preferred_weight >= 81

    #get the first nc shakemap
    first_shakemap = event.getProducts('shakemap',version=VersionOption.FIRST,source='nc')[0]
    assert first_shakemap.source == 'nc'
    assert first_shakemap.update_time >= datetime(2017, 3, 8, 20, 12, 59, 380000)
    assert first_shakemap.preferred_weight >= 231
    
    #get the last version of the nc shakemaps
    last_shakemap = event.getProducts('shakemap',version=VersionOption.LAST,source='nc')[0]
    assert last_shakemap.source == 'nc'
    assert last_shakemap.update_time >= datetime(2017, 3, 17, 17, 40, 26, 576000)
    assert last_shakemap.preferred_weight >= 231

    #get all the nc versions of the shakemap
    shakemaps = event.getProducts('shakemap',version=VersionOption.ALL,source='nc')
    for shakemap4 in shakemaps:
        assert shakemap4.source == 'nc'

    #get all versions of all shakemaps
    shakemaps = event.getProducts('shakemap',version=VersionOption.ALL,source='all')
    assert event.getNumVersions('shakemap') == len(shakemaps)

    
def test_product():
    eventid = 'ci3144585' #northridge
    event = get_event_by_id(eventid)
    product = event.getProducts('shakemap')[0]
    assert product.preferred_weight == 100000000
    assert product.source == 'atlas'
    assert product.update_time >= datetime(2017, 4, 12, 6, 25, 42, 120000)
    pnames = product.getContentsMatching('grid.xml')
    url = product.getContentURL('grid.xml')
    assert url == 'https://earthquake.usgs.gov/archive/product/shakemap/atlas19940117123055/atlas/1491978342120/download/grid.xml'
    assert len(product.getContentsMatching('foo')) == 0
    assert len(pnames) > 1
    assert str(product) == 'Product shakemap from atlas updated 2017-04-12 06:25:42.120000 containing 63 content files.'
    assert product.hasProperty('maxmmi')
    assert 'maxmmi' in product.properties
    assert product['maxmmi'] == '8.6'
    assert 'download/cont_mi.kmz' in product.contents
    assert product.getContentName('grid.xml') == 'grid.xml'
    assert product.getContentName('foo') is None
    assert product.getContentURL('foo') is None
    
    try:
        product.getContent('foo')
        assert 1==2
    except AttributeError as ae:
        pass

    try:
        product['foo']
        assert 1==2
    except AttributeError as ae:
        pass
    
    try:
        handle,tfilename = tempfile.mkstemp()
        os.close(handle)
        product.getContent('info.json',tfilename)
        f = open(tfilename,'rt')
        jdict = json.load(f)
        f.close()
        assert jdict['input']['event_information']['depth'] == 19
    except:
        raise Exception('Failure to download Product content file')
    finally:
        os.remove(tfilename)

if __name__ == '__main__':
    test_moment_supplement()
    test_detail_product_versions()
    test_summary()
    test_detail()
    test_product()
