#!/usr/bin/env python

# stdlib imports
from datetime import datetime, timedelta
import os.path

# third party imports
import vcr
import numpy as np

# local imports
from libcomcat.search import search, count, get_event_by_id
from libcomcat.classes import DetailEvent


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, "cassettes")
    return datadir


def test_get_event():
    eventid = "ci3144585"
    datadir = get_datadir()
    tape_file = os.path.join(datadir, "search_id.yaml")
    with vcr.use_cassette(tape_file):
        event = get_event_by_id(eventid)

    assert isinstance(event, DetailEvent)
    assert event.id == eventid
    assert (event.latitude, event.longitude) == (34.213, -118.537)


def test_count():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, "search_count.yaml")
    with vcr.use_cassette(tape_file):
        nevents = count(
            starttime=datetime(1994, 1, 17, 12, 30),
            endtime=datetime(1994, 1, 18, 12, 35),
            minmagnitude=6.6,
            updatedafter=datetime(2010, 1, 1),
        )
    assert nevents == 1


def test_search_nullmag():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, "search_null.yaml")
    with vcr.use_cassette(tape_file):
        tstart = datetime(2018, 1, 18, 5, 56, 0)
        tend = tstart + timedelta(seconds=60)
        eventlist = search(starttime=tstart, endtime=tend)
        assert np.isnan(eventlist[1].magnitude)


def test_search():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, "search_search.yaml")
    with vcr.use_cassette(tape_file):
        eventlist = search(
            starttime=datetime(1994, 1, 17, 12, 30),
            endtime=datetime(1994, 1, 18, 12, 35),
            minmagnitude=6.6,
        )
        event = eventlist[0]
        assert event.id == "ci3144585"

        events = search(
            minmagnitude=9.0,
            maxmagnitude=9.9,
            starttime=datetime(2008, 1, 1),
            endtime=datetime(2010, 2, 1),
            updatedafter=datetime(2010, 1, 1),
        )

        events = search(
            maxmagnitude=0.1,
            starttime=datetime(2017, 1, 1),
            endtime=datetime(2017, 1, 30),
        )


def test_url_error():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, "search_error.yaml")
    with vcr.use_cassette(tape_file):
        passed = True
        try:
            eventlist = search(
                starttime=datetime(1994, 1, 17, 12, 30),
                endtime=datetime(1994, 1, 18, 12, 35),
                minmagnitude=6.6,
                host="error",
            )
        except Exception as e:
            passed = False
        assert passed == False


# scenarios may not be supported any more?
# def test_scenario():
#     datadir = get_datadir()
#     tape_file = os.path.join(datadir, "search_scenario.yaml")
#     with vcr.use_cassette(tape_file):
#         try:
#             eventlist = search(
#                 starttime=datetime(2013, 10, 10, 12, 0),
#                 endtime=datetime(2013, 10, 10, 12, 30, 0),
#                 minmagnitude=0,
#                 maxmagnitude=9.9,
#                 scenario=True,
#             )
#             assert eventlist[0].id == "ak013d08buqb"
#         except Exception as e:
#             raise AssertionError('Scenario search failed with "%s".' % (str(e)))


if __name__ == "__main__":
    test_search_nullmag()
    test_get_event()
    test_count()
    test_search()
    test_url_error()
