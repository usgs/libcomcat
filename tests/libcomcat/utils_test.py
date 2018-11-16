#!/usr/bin/env python

import os.path
from datetime import datetime

import numpy as np

import vcr

from libcomcat.utils import (get_summary_data_frame,
                             get_detail_data_frame,
                             get_pager_results,
                             makedict,
                             maketime,
                             get_catalogs,
                             get_phase_dataframe,
                             get_magnitude_data_frame,
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


def test_phase_dataframe():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_phase_dataframe.yaml')
    # with vcr.use_cassette(tape_file):
    detail = get_event_by_id('us1000778i')  # 2016 NZ event
    df = get_magnitude_data_frame(detail, 'us', 'mb')
    np.testing.assert_almost_equal(df['Magnitude'].sum(), 756.8100000000001)
    x = 1


def test_magnitude_dataframe():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_magnitude_dataframe.yaml')
    with vcr.use_cassette(tape_file):
        detail = get_event_by_id('us1000778i')  # 2016 NZ event
        df = get_phase_dataframe(detail, catalog='us')
        assert len(df) == 174


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


def test_get_summary_data_frame():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_summary_frame.yaml')
    with vcr.use_cassette(tape_file):
        events = search(starttime=datetime(1994, 6, 1),
                        endtime=datetime(1994, 10, 6),
                        minmagnitude=8.0, maxmagnitude=9.0, verbose=True)

        df = get_summary_data_frame(events)
        assert len(df) == 2
        assert df.iloc[0]['magnitude'] == 8.2


def test_get_detail_data_frame():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_detail_frame.yaml')
    with vcr.use_cassette(tape_file):
        events = search(starttime=datetime(1994, 6, 1),
                        endtime=datetime(1994, 10, 6),
                        minmagnitude=8.0, maxmagnitude=9.0)
        all_mags = get_detail_data_frame(
            events, get_all_magnitudes=True, verbose=True)
        assert all_mags.iloc[0]['magnitude'] == 8.2

def test_get_pager_results():
    datadir = get_datadir()
    EVENTID = 'us2000h8ty'
    detail = get_event_by_id(EVENTID)
    tape_file = os.path.join(datadir, 'vcr_pager_results.yaml')
    # with vcr.use_cassette(tape_file):
    df = get_pager_results(detail)
    mmi3_total = 2248544
    mmi3 = df.iloc[0]['mmi3']
    assert mmi3 == mmi3_total

    df = get_pager_results(detail, get_country_exposures=True)
    assert mmi3_total == df.iloc[1:]['mmi3'].sum()

    df = get_pager_results(detail, get_losses=True)
    testfat = 13
    testeco = 323864991
    assert df.iloc[0]['predicted_fatalities'] == testfat
    assert df.iloc[0]['predicted_dollars'] == testeco

    df = get_pager_results(detail, get_losses=True, get_country_exposures=True)
    assert df.iloc[1:]['predicted_fatalities'].sum() == testfat
    assert df.iloc[1:]['predicted_dollars'].sum() == testeco

    EVENTID = 'us1000778i'
    detail = get_event_by_id(EVENTID)
    x = 1

        

        

if __name__ == '__main__':
    print('Testing pager extraction...')
    test_get_pager_results()
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
    print('Testing magnitude frame...')
    test_get_magnitude_data_frame()
