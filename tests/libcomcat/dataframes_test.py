#!/usr/bin/env python

import os.path
import pathlib
from datetime import datetime
from unittest import mock

import numpy as np
import pandas as pd
import vcr

from libcomcat import search
from libcomcat.dataframes import (
    associate,
    get_detail_data_frame,
    get_dyfi_data_frame,
    get_history_data_frame,
    get_magnitude_data_frame,
    get_pager_data_frame,
    get_phase_dataframe,
    get_summary_data_frame,
)
from libcomcat.exceptions import ParsingError
from libcomcat.search import get_event_by_id

DMINUTE = 60  # number of seconds in a minute
DHOUR = 3600  # number of seconds in an hour
DDAY = 86400  # number of seconds in a day


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, "..", "data")
    cassettes = os.path.join(homedir, "cassettes")
    return cassettes, datadir


def test_magnitude_dataframe():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "dataframes_magnitude.yaml")
    with vcr.use_cassette(tape_file, record_mode="new_episodes"):
        detail = get_event_by_id("us1000778i")  # 2016 NZ event
        df = get_magnitude_data_frame(detail, "us", "mb")
        np.testing.assert_almost_equal(df["Magnitude"].sum(), 756.8100000000001)


def test_phase_dataframe():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "dataframes_phase.yaml")
    with vcr.use_cassette(tape_file, record_mode="new_episodes"):
        detail = get_event_by_id("us1000778i")  # 2016 NZ event
        df = get_phase_dataframe(detail, catalog="us")
        assert len(df) == 174


def test_get_summary_data_frame():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "dataframes_summary.yaml")
    with vcr.use_cassette(tape_file, record_mode="new_episodes"):
        events = search.search(
            starttime=datetime(1994, 6, 1),
            endtime=datetime(1994, 10, 6),
            minmagnitude=8.0,
            maxmagnitude=9.0,
        )

        df = get_summary_data_frame(events)
        assert len(df) == 2
        assert df.iloc[0]["magnitude"] == 8.2


def test_get_detail_data_frame():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "dataframes_detailed.yaml")
    with vcr.use_cassette(tape_file, record_mode="new_episodes"):
        events = search.search(
            starttime=datetime(1994, 6, 1),
            endtime=datetime(1994, 10, 6),
            minmagnitude=8.0,
            maxmagnitude=9.0,
        )
        all_mags = get_detail_data_frame(events, get_all_magnitudes=True)
        assert all_mags.iloc[0]["magnitude"] == 8.2


def test_get_pager_data_frame():
    cassettes, datadir = get_datadir()
    EVENTID = "us2000h8ty"
    detail = get_event_by_id(EVENTID)
    tape_file = os.path.join(cassettes, "dataframes_pager.yaml")
    with vcr.use_cassette(tape_file, record_mode="new_episodes"):
        df = get_pager_data_frame(detail)
        mmi3_total = 2248544
        mmi3 = df.iloc[0]["mmi3"]
        assert mmi3 == mmi3_total

        df = get_pager_data_frame(detail, get_losses=True, get_country_exposures=True)
        assert mmi3_total == df.iloc[1:]["mmi3"].sum()

        df = get_pager_data_frame(detail, get_losses=True)
        testfat = 13
        testeco = 323864991
        assert df.iloc[0]["predicted_fatalities"] == testfat
        assert df.iloc[0]["predicted_dollars"] == testeco

        df = get_pager_data_frame(detail, get_losses=True, get_country_exposures=True)
        assert df.iloc[1:]["predicted_fatalities"].sum() == testfat
        assert df.iloc[1:]["predicted_dollars"].sum() == testeco

        EVENTID = "us1000778i"
        detail = get_event_by_id(EVENTID)
        df = get_pager_data_frame(detail)
        testval = 14380
        assert df.iloc[0]["mmi4"] == testval

        # test getting superseded versions of the pager product
        EVENTID = "us2000h8ty"
        detail = get_event_by_id(EVENTID, includesuperseded=True)
        df = get_pager_data_frame(detail, get_losses=True)
        version_7 = df[df["pager_version"] == 7].iloc[0]
        v7fats = 16
        assert version_7["predicted_fatalities"] == v7fats


def test_dyfi():
    eventid = "se60247871"
    detail = get_event_by_id(eventid, includesuperseded=True)
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "dataframes_dyfi.yaml")
    with vcr.use_cassette(tape_file, record_mode="new_episodes"):
        df1km = get_dyfi_data_frame(detail, dyfi_file="utm_1km")
        np.testing.assert_almost_equal(df1km["intensity"].sum(), 14629.1)
        df10km = get_dyfi_data_frame(detail, dyfi_file="utm_10km")
        np.testing.assert_almost_equal(df10km["intensity"].sum(), 3459.0)
        dfutm = get_dyfi_data_frame(detail, dyfi_file="utm_var")
        np.testing.assert_almost_equal(dfutm["intensity"].sum(), 3459.0)
        dfzip = get_dyfi_data_frame(detail, dyfi_file="zip")
        np.testing.assert_almost_equal(dfzip["intensity"].sum(), 2296.3)


def test_nan_mags():
    detail = get_event_by_id("us2000arrw")
    try:
        _ = get_phase_dataframe(detail)
    except ParsingError:
        pass


def test_history_data_frame():
    # SMOKE TEST
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "dataframes_history.yaml")
    products = [
        "shakemap",
        "dyfi",
        "losspager",
        "oaf",
        "finite-fault",
        "focal-mechanism",
        "ground-failure",
        "moment-tensor",
        "phase-data",
        "origin",
    ]

    with vcr.use_cassette(tape_file, record_mode="new_episodes"):
        nc72852151 = get_event_by_id("nc72852151", includesuperseded=True)
        (history, event) = get_history_data_frame(nc72852151, products)
        us10008e3k = get_event_by_id("us10008e3k", includesuperseded=True)
        (history, event) = get_history_data_frame(
            us10008e3k,
            [
                "shakemap",
                "dyfi",
                "oaf",
                "finite-fault",
                "focal-mechanism",
                "moment-tensor",
            ],
        )
        us10007uph = get_event_by_id("us10007uph", includesuperseded=True)
        (history, event) = get_history_data_frame(
            us10007uph,
            [
                "shakemap",
                "dyfi",
                "oaf",
                "finite-fault",
                "focal-mechanism",
                "ground-failure",
                "moment-tensor",
                "phase-data",
            ],
        )


# class MockEvent(object):
#     def toDict(self):
#         return {'id': self.id,
#                 'time': self.time,
#                 'latitude': self.latitude,
#                 'longitude': self.longitude,
#                 'magnitude': self.magnitude,
#                 'depth': self.depth
#                 }


def test_associate():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "dataframes_association.yaml")
    with vcr.use_cassette(tape_file, record_mode="new_episodes"):
        one_to_one = pd.DataFrame(
            {
                "time": [datetime(2019, 7, 6, 3, 19, 53)],
                "latitude": [35.770],
                "longitude": [-117.599],
                "magnitude": 7.1,
            }
        )
        associated, alternates = associate(one_to_one)
        assert associated.iloc[0]["comcat_id"] == "ci38457511"

        ambiguous = pd.DataFrame(
            {
                "time": [datetime(2019, 7, 6, 4, 20, 17)],
                "latitude": [35.78],
                "longitude": [-117.614],
                "magnitude": 4.3,
            }
        )
        # this should be empty, b/c default time tolerance is too small
        associated, alternates = associate(ambiguous)
        assert associated.empty

        # now widen the tolerance to include four total events
        associated, alternates = associate(ambiguous, time_tol_secs=120)
        assert associated.iloc[0]["comcat_id"] == "ci37221932"
        assert associated.iloc[0]["comcat_score"] < alternates["score"].min()

        # make sure this works on multiple events
        two_events = pd.DataFrame(
            {
                "time": [
                    datetime(2019, 7, 6, 9, 30, 15),
                    datetime(2019, 7, 6, 3, 33, 15),
                ],
                "latitude": [35.911, 35.624],
                "longitude": [-117.732, -117.486],
                "magnitude": [4.5, 4.1],
            }
        )
        associated, alternates = associate(two_events, time_tol_secs=120)
        for idx, row in associated.iterrows():
            palt = alternates[alternates["chosen_id"] == row["comcat_id"]]
            assert row["comcat_score"] < palt["score"].min()
        cmpids = ["ci37219700", "ci38460983"]
        assert sorted(associated["comcat_id"].tolist()) == cmpids

        # test an array of events
        datafile = (
            pathlib.Path(__file__).parent / ".." / "data" / "sample_catalogue.csv"
        )
        dataframe = pd.read_csv(datafile)
        idx_sec = dataframe["SECOND"].isnull()

        idx_minute = dataframe["MINUTE"].isnull()
        idx_hour = dataframe["HOUR"].isnull()

        dataframe["accuracy"] = 0
        dataframe.loc[idx_sec, "accuracy"] = DMINUTE
        dataframe.loc[idx_minute, "accuracy"] = DHOUR
        dataframe.loc[idx_hour, "accuracy"] = DDAY

        dataframe["HOUR"] = dataframe["HOUR"].fillna(value=0)
        dataframe["MINUTE"] = dataframe["MINUTE"].fillna(value=0)
        dataframe["SECOND"] = dataframe["SECOND"].fillna(value=0)

        tcols = ["YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND"]
        dataframe["time"] = dataframe["time"] = pd.to_datetime(dataframe[tcols])
        dataframe = dataframe.sort_values("time")

        seconds_frame = dataframe[dataframe["accuracy"] == 0]
        associated_seconds, alternate_seconds = associate(
            seconds_frame,
            time_tol_secs=60,
            mag_column="MAGNITUDE",
            lat_column="LATITUDE",
            lon_column="LONGITUDE",
        )
        cmplist = [
            "ushis474",
            "ushis524",
            "ushis529",
            "ushis532",
            "ushis533",
            "ushis541",
        ]
        assert sorted(associated_seconds["comcat_id"].tolist()) == cmplist

        minutes_frame = dataframe[dataframe["accuracy"] == 60]
        associated_minutes, alternate_minutes = associate(
            minutes_frame,
            time_tol_secs=300,
            mag_column="MAGNITUDE",
            lat_column="LATITUDE",
            lon_column="LONGITUDE",
        )
        cmplist = ["official17271110034000000", "ushis4", "ushis6", "ushis7"]
        assert sorted(associated_minutes["comcat_id"].tolist()) == cmplist

        hours_frame = dataframe[dataframe["accuracy"] == 3600]
        associated_hours, alternate_hours = associate(
            hours_frame,
            time_tol_secs=3600,
            mag_column="MAGNITUDE",
            lat_column="LATITUDE",
            lon_column="LONGITUDE",
        )
        cmplist = ["cdmg18731123050000000"]
        assert sorted(associated_hours["comcat_id"].tolist()) == cmplist

        days_frame = dataframe[dataframe["accuracy"] == 86400]
        associated_days, alternate_days = associate(
            days_frame,
            time_tol_secs=86400,
            mag_column="MAGNITUDE",
            lat_column="LATITUDE",
            lon_column="LONGITUDE",
        )
        cmplist = ["ushis21"]
        # assert sorted(associated_days['comcat_id'].tolist()) == cmplist

        # TODO: test what happens if either or both of dist, magnitude are nan
        missing_mag = pd.DataFrame(
            {
                "time": [datetime(1905, 4, 4, 0, 49, 59)],
                "latitude": [32.636],
                "longitude": [76.788],
                "magnitude": np.nan,
            }
        )
        associated, alternates = associate(missing_mag)
        assert associated["comcat_id"].iloc[0] == "iscgem16957848"

        missing_loc = pd.DataFrame(
            {
                "time": [datetime(1905, 4, 4, 0, 49, 59)],
                "latitude": [np.nan],
                "longitude": [np.nan],
                "magnitude": [7.9],
            }
        )
        associated, alternates = associate(missing_loc)
        assert associated["comcat_id"].iloc[0] == "iscgem16957848"

        missing_both = pd.DataFrame(
            {
                "time": [datetime(1905, 4, 4, 0, 49, 59)],
                "latitude": [np.nan],
                "longitude": [np.nan],
                "magnitude": [np.nan],
            }
        )
        associated, alternates = associate(missing_both)
        assert associated["comcat_id"].iloc[0] == "iscgem16957848"

        # # test weighting
        # # now widen the tolerance to include four total events
        # etimes = [datetime(2020, 1, 1, 0, 0, 12),
        #           datetime(2020, 1, 1, 0, 0, 10),
        #           datetime(2020, 1, 1, 0, 0, 15),
        #           ]
        # emags = [5.0,
        #          4.8,
        #          5.4
        #          ]
        # elats = [0.8,
        #          0.8,
        #          0.1
        #          ]
        # elons = [0.3,
        #          0.9,
        #          0.6
        #          ]
        # ids = ['1', '2', '3']
        # events = []
        # for eid, etime, emag, elat, elon in zip(ids, etimes, emags, elats, elons):
        #     event = MockEvent()
        #     event.id = eid
        #     event.time = etime
        #     event.latitude = elat
        #     event.longitude = elon
        #     event.depth = 0.0
        #     event.magnitude = emag
        #     events.append(event)

        # origin = pd.DataFrame({'time': [datetime(2020, 1, 1, 0, 0, 0)],
        #                        'latitude': [0.3],
        #                        'longitude': [0.6],
        #                        'magnitude': [5.0]})
        # with mock.patch('libcomcat.search.search', return_value=events):
        #     associated, alternates = associate(origin,
        #                                        time_tol_secs=130,
        #                                        time_weight=1)
        # assert associated.iloc[0]['comcat_id'] == '2'

        # with mock.patch('libcomcat.search.search', return_value=events):
        #     associated, alternates = associate(origin,
        #                                        time_tol_secs=130,
        #                                        dist_weight=100)
        # assert associated.iloc[0]['comcat_id'] == '3'


if __name__ == "__main__":
    print("Testing history frame...")
    test_history_data_frame()
    print("Testing catalog association...")
    test_associate()
    print("Testing nan mags extraction...")
    test_nan_mags()
    print("Testing DYFI extraction...")
    test_dyfi()
    print("Testing pager extraction...")
    test_get_pager_data_frame()
    print("Testing getting phase dataframe...")
    test_phase_dataframe()
    print("Testing summary frame...")
    test_get_summary_data_frame()
    print("Testing detail frame...")
    test_get_detail_data_frame()
    print("Testing magnitude frame...")
    test_magnitude_dataframe()
