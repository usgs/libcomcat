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
                             get_contributors)
from libcomcat.search import search
import pandas as pd

def test_makedict():
    string = 'reviewstatus:approved'
    mydict = makedict(string)
    assert mydict['reviewstatus'] == 'approved'

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

def test_catalogs():
    catalogs = get_catalogs()
    assert 'us' in catalogs

def test_contributors():
    contributors = get_contributors()
    assert 'ak' in contributors

def test_get_summary_data_frame():
    events = search(starttime=datetime(1994,6,1),
                    endtime=datetime(1994,10,6),
                    minmagnitude=8.0,maxmagnitude=9.0)

    df = get_summary_data_frame(events)
    assert len(df) == 2
    assert df.iloc[0]['magnitude'] == 8.2
    
def test_get_detail_data_frame():
    events = search(starttime=datetime(1994,6,1),
                    endtime=datetime(1994,10,6),
                    minmagnitude=8.0,maxmagnitude=9.0)
    all_mags = get_detail_data_frame(events,get_all_magnitudes=True)
    assert all_mags.iloc[0]['magnitude'] == 8.2

if __name__ == '__main__':
    test_makedict()
    test_maketime()
    test_catalogs()
    test_contributors()
    test_get_summary_data_frame()
    test_get_detail_data_frame()
