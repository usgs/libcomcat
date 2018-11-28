#!/usr/bin/env python

import os.path
from datetime import datetime

import numpy as np

import vcr

from libcomcat.dataframes import (get_summary_data_frame,
                                  get_detail_data_frame,
                                  get_pager_data_frame,
                                  get_phase_dataframe,
                                  get_magnitude_data_frame)
from libcomcat.search import search, get_event_by_id


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', 'data')
    return datadir


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


def test_get_pager_data_frame():
    datadir = get_datadir()
    EVENTID = 'us2000h8ty'
    detail = get_event_by_id(EVENTID)
    tape_file = os.path.join(datadir, 'vcr_pager_results.yaml')
    # with vcr.use_cassette(tape_file):
    df = get_pager_data_frame(detail)
    mmi3_total = 2248544
    mmi3 = df.iloc[0]['mmi3']
    assert mmi3 == mmi3_total

    df = get_pager_data_frame(detail, get_country_exposures=True)
    assert mmi3_total == df.iloc[1:]['mmi3'].sum()

    df = get_pager_data_frame(detail, get_losses=True)
    testfat = 13
    testeco = 323864991
    assert df.iloc[0]['predicted_fatalities'] == testfat
    assert df.iloc[0]['predicted_dollars'] == testeco

    df = get_pager_data_frame(detail, get_losses=True,
                              get_country_exposures=True)
    assert df.iloc[1:]['predicted_fatalities'].sum() == testfat
    assert df.iloc[1:]['predicted_dollars'].sum() == testeco

    EVENTID = 'us1000778i'
    detail = get_event_by_id(EVENTID)
    df = get_pager_data_frame(detail)
    testval = 14380
    assert df.iloc[0]['mmi4'] == testval

    # test getting superseded versions of the pager product
    EVENTID = 'us2000h8ty'
    detail = get_event_by_id(EVENTID, includesuperseded=True)
    df = get_pager_data_frame(detail, get_losses=True)
    version_7 = df[df['pager_version'] == 7].iloc[0]
    v7fats = 16
    assert version_7['predicted_fatalities'] == v7fats


if __name__ == '__main__':
    print('Testing pager extraction...')
    test_get_pager_data_frame()
    print('Testing getting phase dataframe...')
    test_phase_dataframe()
    print('Testing summary frame...')
    test_get_summary_data_frame()
    print('Testing detail frame...')
    test_get_detail_data_frame()
    print('Testing magnitude frame...')
    test_magnitude_dataframe()
