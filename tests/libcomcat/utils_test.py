#!/usr/bin/env python

import os.path
from datetime import datetime

import numpy as np
import pandas as pd

import vcr

from libcomcat.utils import (makedict,
                             maketime,
                             get_catalogs,
                             read_phases,
                             get_contributors,
                             check_ccode,
                             get_country_bounds,
                             _get_country_shape,
                             filter_by_country,
                             _get_utm_proj)
from libcomcat.search import search, get_event_by_id


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', 'data')
    return datadir


def test_reader():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir = os.path.abspath(os.path.join(homedir, '..', 'data'))
    datafile = os.path.join(datadir, 'us2000ahv0_phases.xlsx')
    hdr, dataframe = read_phases(datafile)
    assert hdr['id'] == 'us2000ahv0'
    assert dataframe.iloc[0]['Channel'] == 'GI.HUEH.HHZ.--'

    datafile = os.path.join(datadir, 'us2000ahv0_phases.csv')
    hdr, dataframe = read_phases(datafile)
    assert hdr['id'] == 'us2000ahv0'
    assert dataframe.iloc[0]['Channel'] == 'GI.HUEH.HHZ.--'

    try:
        read_phases('foo')
    except FileNotFoundError:
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
        assert 1 == 2
    except Exception:
        pass


def test_maketime():
    str1 = '2000-01-02T03:04:05'
    str2 = '2000-01-02T03:04:05.678'
    str3 = '2000-01-02'
    time1 = maketime(str1)
    time2 = maketime(str2)
    time3 = maketime(str3)
    assert time1 == datetime(2000, 1, 2, 3, 4, 5)
    assert time2 == datetime(2000, 1, 2, 3, 4, 5, 678000)
    assert time3 == datetime(2000, 1, 2)

    try:
        maketime('foo')
        assert 1 == 2
    except Exception:
        pass


def test_catalogs():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_catalogs.yaml')
    with vcr.use_cassette(tape_file):
        catalogs = get_catalogs()
        assert 'us' in catalogs


def test_contributors():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_contributors.yaml')
    with vcr.use_cassette(tape_file):
        contributors = get_contributors()
        assert 'ak' in contributors


def test_get_utm_proj():
    tuples = [(36, -76, '+proj=utm +zone=18S, +ellps=WGS84 +datum=WGS84 +units=m +no_defs '),
              (-66, 0, '+proj=utm +zone=31D, +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs '),
              (-81, 0, '+proj=utm +zone=31C, +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs '),
              (85, 0, '+proj=utm +zone=31X, +ellps=WGS84 +datum=WGS84 +units=m +no_defs '),
              (76, 178, '+proj=utm +zone=60X, +ellps=WGS84 +datum=WGS84 +units=m +no_defs '),
              (4, 122, '+proj=utm +zone=51N, +ellps=WGS84 +datum=WGS84 +units=m +no_defs '),
              ]

    for tpl in tuples:
        lat, lon, projstr = tpl
        proj = _get_utm_proj(lat, lon)
        assert proj.srs == projstr


def test_check_ccode():
    for ccode in ['AFG', 'CHN', 'USA', 'FRA']:
        assert check_ccode(ccode)

    try:
        assert check_ccode('foo')
    except Exception:
        pass


def test_get_country_bounds():
    bounds = get_country_bounds('FRA')
    assert len(bounds) == 10
    tbounds = (7.944129165762711, 10.177941146737316,
               40.54592258835411, 43.860473896020885)
    assert bounds[0] == tbounds


def test_get_country_shape():
    shape = _get_country_shape('JAM')
    assert len(shape.exterior.coords[:]) == 48


def test_filter_by_country():
    # first event is in Haiti, second is in Dom. Rep.
    data = {'id': ['us1000h8hi', 'pr2019035005'],
            'latitude': [20.041, 18.136],
            'longitude': [-73.014, -68.552]}
    df = pd.DataFrame(data)
    df2 = filter_by_country(df, 'DOM')
    assert len(df2) == 1
    assert df2.iloc[0]['id'] == 'pr2019035005'


if __name__ == '__main__':
    test_filter_by_country()
    test_get_country_shape()
    test_get_country_bounds()
    test_check_ccode()
    test_get_utm_proj()
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
