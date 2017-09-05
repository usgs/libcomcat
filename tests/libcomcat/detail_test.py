#!/usr/bin/env python

import os.path
import sys
from datetime import datetime,timedelta
import tempfile
import json

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
pathdir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, pathdir)  # put this at the front of the system path,
# ignoring any other installations of this library

from libcomcat.detail import DetailEvent,search,get_summary_data_frame,get_detail_data_frame,get_event_by_id,count,Product
import pandas as pd

def test_get_event():
    eventid = 'ci3144585'
    event = get_event_by_id(eventid)
    assert isinstance(event,DetailEvent)

def test_detail_methods():
    eventid = 'ci3144585' #northridge
    event = get_event_by_id(eventid)
    assert event.hasProduct('shakemap')
    assert event.toDict()['magnitude'] == 6.7
    assert event.getNumVersions('shakemap') > 0
    assert isinstance(event.getProduct('shakemap'),Product)
    assert event.latitude == 34.213
    assert event.longitude == -118.537
    assert event.depth == 18.202
    assert event.id == 'ci3144585'
    assert event.time == datetime(1994, 1, 17, 12, 30, 55, 390000)
    assert 'sources' in event.properties
    assert event['mag'] == 6.7

def test_product_methods():
    eventid = 'ci3144585' #northridge
    event = get_event_by_id(eventid)
    product = event.getProduct('shakemap')
    assert product.hasContent('grid.xml')[0]
    assert product.hasProperty('maxmmi')
    assert 'maxmmi' in product.properties
    assert product['maxmmi'] == '8.6'
    assert 'download/cont_mi.kmz' in product.contents
    assert product.getContentName('grid.xml') == 'download/grid.xml'
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

def test_search():
    eventlist = search(starttime=datetime(1994,1,17,12,30),
                       endtime=datetime(1994,1,18,12,35),
                       minmagnitude=6.6)
    event = eventlist[0]
    assert event.id == 'ci3144585'

def test_count():
    nevents = count(starttime=datetime(1994,1,17,12,30),
                    endtime=datetime(1994,1,18,12,35),
                    minmagnitude=6.6)
    assert nevents == 1
        
def test_summary_methods():
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

def test_summary_dataframe():
    events = search(starttime=datetime(1994,6,1),
                    endtime=datetime(1994,10,6),
                    minmagnitude=8.0,maxmagnitude=9.0)
    events[0].time
    df = get_summary_data_frame(events)
    assert len(df) == 2
    assert df.iloc[0]['magnitude'] == 8.2

if __name__ == '__main__':
    test_get_event()
    test_detail_methods()
    test_product_methods()
    test_search()
    test_count()
    test_summary_methods()
    test_summary_dataframe()
    
