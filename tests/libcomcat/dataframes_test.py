#!/usr/bin/env python

import os.path
from datetime import datetime

import numpy as np

import vcr

from libcomcat.dataframes import (get_summary_data_frame,
                                  get_detail_data_frame,
                                  get_pager_data_frame,
                                  get_phase_dataframe,
                                  get_magnitude_data_frame,
                                  get_dyfi_data_frame,
                                  get_history_data_frame)
from libcomcat.search import search, get_event_by_id
from libcomcat.exceptions import ParsingError


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', 'data')
    cassettes = os.path.join(homedir, 'cassettes')
    return cassettes, datadir


def test_magnitude_dataframe():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, 'dataframes_magnitude.yaml')
    with vcr.use_cassette(tape_file):
        detail = get_event_by_id('us1000778i')  # 2016 NZ event
        df = get_magnitude_data_frame(detail, 'us', 'mb')
        np.testing.assert_almost_equal(
            df['Magnitude'].sum(), 756.8100000000001)


def test_phase_dataframe():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, 'dataframes_phase.yaml')
    with vcr.use_cassette(tape_file):
        detail = get_event_by_id('us1000778i')  # 2016 NZ event
        df = get_phase_dataframe(detail, catalog='us')
        assert len(df) == 174


def test_get_summary_data_frame():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, 'dataframes_summary.yaml')
    with vcr.use_cassette(tape_file):
        events = search(starttime=datetime(1994, 6, 1),
                        endtime=datetime(1994, 10, 6),
                        minmagnitude=8.0, maxmagnitude=9.0)

        df = get_summary_data_frame(events)
        assert len(df) == 2
        assert df.iloc[0]['magnitude'] == 8.2


def test_get_detail_data_frame():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, 'dataframes_detailed.yaml')
    with vcr.use_cassette(tape_file):
        events = search(starttime=datetime(1994, 6, 1),
                        endtime=datetime(1994, 10, 6),
                        minmagnitude=8.0, maxmagnitude=9.0)
        all_mags = get_detail_data_frame(
            events, get_all_magnitudes=True)
        assert all_mags.iloc[0]['magnitude'] == 8.2


def test_get_pager_data_frame():
    cassettes, datadir = get_datadir()
    EVENTID = 'us2000h8ty'
    detail = get_event_by_id(EVENTID)
    tape_file = os.path.join(cassettes, 'dataframes_pager.yaml')
    with vcr.use_cassette(tape_file):
        df = get_pager_data_frame(detail)
        mmi3_total = 2248544
        mmi3 = df.iloc[0]['mmi3']
        assert mmi3 == mmi3_total

        df = get_pager_data_frame(detail, get_losses=True,
                                  get_country_exposures=True)
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


def test_dyfi():
    eventid = 'se60247871'
    detail = get_event_by_id(eventid, includesuperseded=True)
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, 'dataframes_dyfi.yaml')
    with vcr.use_cassette(tape_file):
        df1km = get_dyfi_data_frame(detail, dyfi_file='utm_1km')
        np.testing.assert_almost_equal(
            df1km['intensity'].sum(), 14913.4)
        df10km = get_dyfi_data_frame(detail, dyfi_file='utm_10km')
        np.testing.assert_almost_equal(
            df10km['intensity'].sum(), 3474.3999999999996)
        dfutm = get_dyfi_data_frame(detail, dyfi_file='utm_var')
        np.testing.assert_almost_equal(
            dfutm['intensity'].sum(), 3474.3999999999996)
        dfzip = get_dyfi_data_frame(detail, dyfi_file='zip')
        np.testing.assert_almost_equal(
            dfzip['intensity'].sum(), 2345.5)


def test_nan_mags():
    detail = get_event_by_id('us2000arrw')
    try:
        _ = get_phase_dataframe(detail)
    except ParsingError:
        pass


def test_history_data_frame():
    # SMOKE TEST
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, 'dataframes_history.yaml')
    with vcr.use_cassette(tape_file):
        nc72852151 = get_event_by_id('nc72852151', includesuperseded=True)
        (history, event) = get_history_data_frame(nc72852151, ['shakemap', 'dyfi',
                                                               'losspager', 'oaf',
                                                               'finite-fault',
                                                               'focal-mechanism',
                                                               'ground-failure',
                                                               'moment-tensor',
                                                               'phase-data',
                                                               'origin'])
        us10008e3k = get_event_by_id('us10008e3k', includesuperseded=True)
        (history, event) = get_history_data_frame(us10008e3k, ['shakemap', 'dyfi',
                                                               'oaf',
                                                               'finite-fault',
                                                               'focal-mechanism',
                                                               'moment-tensor'])
        us10007uph = get_event_by_id('us10007uph', includesuperseded=True)
        (history, event) = get_history_data_frame(us10007uph, ['shakemap', 'dyfi',
                                                               'oaf',
                                                               'finite-fault',
                                                               'focal-mechanism',
                                                               'ground-failure',
                                                               'moment-tensor',
                                                               'phase-data'])


if __name__ == '__main__':
    print('Testing nan mags extraction...')
    test_nan_mags()
    print('Testing DYFI extraction...')
    test_dyfi()
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
    print('Testing history frame...')
    test_history_data_frame()
