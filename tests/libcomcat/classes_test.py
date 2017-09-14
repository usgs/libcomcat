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
    assert event.id == 'ci3144585'
    assert event.time == datetime(1994, 1, 17, 12, 30, 55, 390000)
    assert event.latitude == 34.213
    assert event.longitude == -118.537
    assert event.depth == 18.202
    assert event.magnitude == 6.7
    assert 'cdi' in event.properties
    assert event['cdi'] == 8.6
    assert event.hasProduct('shakemap')
    assert event.hasProperty('cdi')
    assert isinstance(event.getDetailEvent(),DetailEvent)
    durl = 'https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=ci3144585&format=geojson'
    assert event.getDetailURL() == durl
    assert event.toDict()['depth'] == 18.202

def test_detail():
    eventid = 'ci3144585' #northridge
    url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/%s.geojson' % eventid
    event = DetailEvent(url)
    assert event.hasProduct('shakemap')
    assert event.toDict()['magnitude'] == 6.7
    assert event.getNumVersions('shakemap') > 0
    assert isinstance(event.getProducts('shakemap')[0],Product)
    assert event.latitude == 34.213
    assert event.longitude == -118.537
    assert event.depth == 18.202
    assert event.id == 'ci3144585'
    assert event.time == datetime(1994, 1, 17, 12, 30, 55, 390000)
    assert 'sources' in event.properties
    assert event['mag'] == 6.7

    #test all of the different functionality of the getProducts() method
    #first, test default behavior (get the most preferred product):
    event = get_event_by_id('nc21323712',includesuperseded=True) #2003 Central California
    pref_shakemap = event.getProducts('shakemap')[0]
    assert pref_shakemap.source == 'atlas'
    assert pref_shakemap.update_time >= datetime(2017, 4, 12, 10, 50, 9, 368000)
    assert pref_shakemap.preferred_weight >= 100000000

    #get the first Atlas shakemap
    first_shakemap = event.getProducts('shakemap',version_option=VersionOption.FIRST,source='atlas')[0]
    assert first_shakemap.source == 'atlas'
    assert first_shakemap.update_time >= datetime(2015, 2, 4, 6, 1, 33, 400000)
    assert first_shakemap.preferred_weight >= 81

    #get the first nc shakemap
    first_shakemap = event.getProducts('shakemap',version_option=VersionOption.FIRST,source='nc')[0]
    assert first_shakemap.source == 'nc'
    assert first_shakemap.update_time >= datetime(2017, 3, 8, 20, 12, 59, 380000)
    assert first_shakemap.preferred_weight >= 231
    
    #get the last version of the nc shakemaps
    last_shakemap = event.getProducts('shakemap',version_option=VersionOption.LAST,source='nc')[0]
    assert last_shakemap.source == 'nc'
    assert last_shakemap.update_time >= datetime(2017, 3, 17, 17, 40, 26, 576000)
    assert last_shakemap.preferred_weight >= 231

    #get all the nc versions of the shakemap
    shakemaps = event.getProducts('shakemap',version_option=VersionOption.ALL,source='nc')
    for shakemap4 in shakemaps:
        assert shakemap4.source == 'nc'

    #get all versions of all shakemaps
    shakemaps = event.getProducts('shakemap',version_option=VersionOption.ALL,source='all')
    assert event.getNumVersions('shakemap') == len(shakemaps)

    
def test_product():
    eventid = 'ci3144585' #northridge
    event = get_event_by_id(eventid)
    product = event.getProducts('shakemap')[0]
    assert product.preferred_weight == 100000000
    assert product.source == 'atlas'
    assert product.update_time >= datetime(2017, 4, 12, 6, 25, 42, 120000)
    pnames = product.getContentsMatching('grid.xml')
    assert len(pnames) > 1
    assert product.hasProperty('maxmmi')
    assert 'maxmmi' in product.properties
    assert product['maxmmi'] == '8.6'
    assert 'download/cont_mi.kmz' in product.contents
    assert product.getContentName('grid.xml') == 'grid.xml'
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
    test_summary()
    test_detail()
    test_product()
