#!/usr/bin/env python

import os.path
from datetime import datetime

import numpy as np
import pandas as pd

import vcr

from libcomcat.dataframes import (get_summary_data_frame,
                                  get_detail_data_frame,
                                  get_pager_data_frame,
                                  get_phase_dataframe,
                                  get_magnitude_data_frame,
                                  get_dyfi_data_frame,
                                  get_impact_data_frame)
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


def test_impact_data_frame():
    datadir = get_datadir()
    print('iscgem910478 limited sources')
    iscgem910478_file = os.path.join(datadir, 'impact_iscgem910478.csv')
    event = get_event_by_id('iscgem910478',
                            host="dev01-earthquake.cr.usgs.gov")
    iscgem910478 = get_impact_data_frame(event).reset_index(drop=True)
    target_iscgem910478 = pd.read_csv(
        iscgem910478_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        iscgem910478[column] = iscgem910478[column].astype(str)
        target_iscgem910478[column] = target_iscgem910478[column].astype(str)
    pd.util.testing.assert_frame_equal(iscgem910478, target_iscgem910478)

    print('iscgem910478 all sources')
    iscgem910478_file = os.path.join(
        datadir, 'impact_iscgem910478_allsources.csv')
    event = get_event_by_id('iscgem910478',
                            host="dev01-earthquake.cr.usgs.gov")
    iscgem910478 = get_impact_data_frame(
        event, all_sources=True).reset_index(drop=True)
    target_iscgem910478 = pd.read_csv(
        iscgem910478_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        iscgem910478[column] = iscgem910478[column].astype(str)
        target_iscgem910478[column] = target_iscgem910478[column].astype(str)
    pd.util.testing.assert_frame_equal(iscgem910478, target_iscgem910478)

    print('iscgem910478 limited sources and shaking')
    iscgem910478_file = os.path.join(
        datadir, 'impact_iscgem910478_shaking.csv')
    event = get_event_by_id('iscgem910478',
                            host="dev01-earthquake.cr.usgs.gov")
    iscgem910478 = get_impact_data_frame(
        event, effect_types='shaking').reset_index(drop=True)
    target_iscgem910478 = pd.read_csv(
        iscgem910478_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        iscgem910478[column] = iscgem910478[column].astype(str)
        target_iscgem910478[column] = target_iscgem910478[column].astype(str)
    pd.util.testing.assert_frame_equal(iscgem910478, target_iscgem910478)

    print('usp0005rcg without contributing')
    usp0005rcg_file = os.path.join(datadir, 'impact_usp0005rcg.csv')
    event = get_event_by_id('usp0005rcg',
                            host="dev02-earthquake.cr.usgs.gov")
    usp0005rcg = get_impact_data_frame(event).reset_index(drop=True)
    target_usp0005rcg = pd.read_csv(
        usp0005rcg_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        usp0005rcg[column] = usp0005rcg[column].astype(str)
        target_usp0005rcg[column] = target_usp0005rcg[column].astype(str)
    pd.util.testing.assert_frame_equal(usp0005rcg, target_usp0005rcg)

    print('usp0005rcg without contributing all sources')
    usp0005rcg_file = os.path.join(datadir,
                                   'impact_usp0005rcg_allsources.csv')
    event = get_event_by_id('usp0005rcg',
                            host="dev02-earthquake.cr.usgs.gov")
    usp0005rcg = get_impact_data_frame(event,
                                       all_sources=True).reset_index(drop=True)
    target_usp0005rcg = pd.read_csv(
        usp0005rcg_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        usp0005rcg[column] = usp0005rcg[column].astype(str)
        target_usp0005rcg[column] = target_usp0005rcg[column].astype(str)
    pd.util.testing.assert_frame_equal(usp0005rcg, target_usp0005rcg)

    print('usp0005rcg with contributing all sources')
    usp0005rcg_file = os.path.join(datadir,
                                   'impact_usp0005rcg_allsources_contributing.csv')
    event = get_event_by_id('usp0005rcg',
                            host="dev02-earthquake.cr.usgs.gov")
    usp0005rcg = get_impact_data_frame(event,
                                       include_contributing=True, all_sources=True).reset_index(drop=True)
    target_usp0005rcg = pd.read_csv(
        usp0005rcg_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        usp0005rcg[column] = usp0005rcg[column].astype(str)
        target_usp0005rcg[column] = target_usp0005rcg[column].astype(str)
    pd.util.testing.assert_frame_equal(usp0005rcg, target_usp0005rcg)

    print('usp0005rcg with contributing')
    usp0005rcg_file = os.path.join(datadir,
                                   'impact_usp0005rcg_contributing.csv')
    event = get_event_by_id('usp0005rcg',
                            host="dev02-earthquake.cr.usgs.gov")
    usp0005rcg = get_impact_data_frame(event,
                                       include_contributing=True).reset_index(drop=True)
    target_usp0005rcg = pd.read_csv(
        usp0005rcg_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        usp0005rcg[column] = usp0005rcg[column].astype(str)
        target_usp0005rcg[column] = target_usp0005rcg[column].astype(str)
    pd.util.testing.assert_frame_equal(usp0005rcg, target_usp0005rcg)

    print('usp0005rcg landslide and shaking')
    usp0005rcg_file = os.path.join(datadir,
                                   'impact_usp0005rcg_landslide_shaking.csv')
    event = get_event_by_id('usp0005rcg',
                            host="dev02-earthquake.cr.usgs.gov")
    usp0005rcg = get_impact_data_frame(event,
                                       effect_types=['landslide', 'shaking']).reset_index(drop=True)
    target_usp0005rcg = pd.read_csv(
        usp0005rcg_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        usp0005rcg[column] = usp0005rcg[column].astype(str)
        target_usp0005rcg[column] = target_usp0005rcg[column].astype(str)
    pd.util.testing.assert_frame_equal(usp0005rcg, target_usp0005rcg)

    print('usp0005rcg destroyed')
    usp0005rcg_file = os.path.join(datadir,
                                   'impact_usp0005rcg_destroyed.csv')
    event = get_event_by_id('usp0005rcg',
                            host="dev02-earthquake.cr.usgs.gov")
    usp0005rcg = get_impact_data_frame(event,
                                       loss_extents=['destroyed']).reset_index(drop=True)
    target_usp0005rcg = pd.read_csv(
        usp0005rcg_file).reset_index(drop=True).fillna('')
    for column in iscgem910478.columns:
        usp0005rcg[column] = usp0005rcg[column].astype(str)
        target_usp0005rcg[column] = target_usp0005rcg[column].astype(str)
    pd.util.testing.assert_frame_equal(usp0005rcg, target_usp0005rcg)


def test_dyfi():
    eventid = 'se60247871'
    detail = get_event_by_id(eventid, includesuperseded=True)
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_dyfi_dataframe.yaml')
    with vcr.use_cassette(tape_file):
        df1km = get_dyfi_data_frame(detail, dyfi_file='utm_1km')
        np.testing.assert_almost_equal(df1km['intensity'].sum(), 14887.3)
        df10km = get_dyfi_data_frame(detail, dyfi_file='utm_10km')
        np.testing.assert_almost_equal(df10km['intensity'].sum(), 3479.5)
        dfutm = get_dyfi_data_frame(detail, dyfi_file='utm_var')
        np.testing.assert_almost_equal(dfutm['intensity'].sum(), 3479.5)
        dfzip = get_dyfi_data_frame(detail, dyfi_file='zip')
        np.testing.assert_almost_equal(dfzip['intensity'].sum(), 2344.7)


if __name__ == '__main__':
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
    print('Testing impact frame...')
    test_impact_data_frame()
