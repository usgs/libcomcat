#!/usr/bin/env python

import os.path
from datetime import datetime

import numpy as np

import vcr

from libcomcat.utils import (makedict,
                             maketime,
                             get_catalogs,
                             read_phases,
                             get_contributors)
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


if __name__ == '__main__':
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
