#!/usr/bin/env python

import os.path
import sys
from datetime import datetime,timedelta
import tempfile
import json

from libcomcat.utils import (get_summary_data_frame,
                             get_detail_data_frame,
                             makedict,
                             maketime,
                             get_catalogs,
                             get_phase_dataframe,
                             read_phases,
                             get_contributors)
from libcomcat.search import search,get_event_by_id
import pandas as pd

def test_reader():
    homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
    datadir = os.path.abspath(os.path.join(homedir,'..','data'))
    datafile = os.path.join(datadir,'us2000ahv0_phases.xlsx')
    hdr,dataframe = read_phases(datafile)
    assert hdr['id'] == 'us2000ahv0'
    assert dataframe.iloc[0]['Channel'] == 'GI.HUEH.HHZ.--'

    datafile = os.path.join(datadir,'us2000ahv0_phases.csv')
    hdr,dataframe = read_phases(datafile)
    assert hdr['id'] == 'us2000ahv0'
    assert dataframe.iloc[0]['Channel'] == 'GI.HUEH.HHZ.--'

    try:
        read_phases('foo')
    except FileNotFoundError as fnfe:
        pass

    try:
        fname = os.path.abspath(__file__)
        read_phases(fname)
    except Exception as e:
        assert str(e).find('Filenames with extension') > -1
        

def test_makedict():
    string = 'reviewstatus:approved'
    mydict = makedict(string)
    assert mydict['reviewstatus'] == 'approved'
    
    try:
        makedict('foo')
        assert 1==2
    except Exception as e:
        pass
    

def test_maketime():
    str1 = '2000-01-02T03:04:05'
    str2 = '2000-01-02T03:04:05.678'
    str3 = '2000-01-02'
    time1 = maketime(str1)
    time2 = maketime(str2)
    time3 = maketime(str3)
    assert time1 == datetime(2000,1,2,3,4,5)
    assert time2 == datetime(2000,1,2,3,4,5,678000)
    assert time3 == datetime(2000,1,2)

    try:
        maketime('foo')
        assert 1==2
    except Exception as e:
        pass

def test_phase_dataframe():
    detail = get_event_by_id('us1000778i') #2016 NZ event
    df = get_phase_dataframe(detail,catalog='us')
    assert len(df) == 174
    
def test_catalogs():
    catalogs = get_catalogs()
    assert 'us' in catalogs

def test_contributors():
    contributors = get_contributors()
    assert 'ak' in contributors

def test_get_summary_data_frame():
    events = search(starttime=datetime(1994,6,1),
                    endtime=datetime(1994,10,6),
                    minmagnitude=8.0,maxmagnitude=9.0,verbose=True)

    df = get_summary_data_frame(events)
    assert len(df) == 2
    assert df.iloc[0]['magnitude'] == 8.2

    
    
def test_get_detail_data_frame():
    events = search(starttime=datetime(1994,6,1),
                    endtime=datetime(1994,10,6),
                    minmagnitude=8.0,maxmagnitude=9.0)
    all_mags = get_detail_data_frame(events,get_all_magnitudes=True,verbose=True)
    assert all_mags.iloc[0]['magnitude'] == 8.2

if __name__ == '__main__':
    print('Testing getting phase dataframe...')
    test_phase_dataframe()
    print('Testing reader...')
    test_reader()
    print('Testing makedict...')
    test_makedict()
    print('Testing maketime...')
    test_maketime()
    print('Testing catalogs...')
    test_catalogs()
    print('Testing conributors...')
    test_contributors()
    print('Testing summary frame...')
    test_get_summary_data_frame()
    print('Testing detail frame...')
    test_get_detail_data_frame()
    
