#!/usr/bin/env python

import json
import os.path
import tempfile
from datetime import datetime

import vcr

from libcomcat.classes import DetailEvent, Product
from libcomcat.exceptions import (
    ArgumentConflictError,
    ContentNotFoundError,
    ProductNotFoundError,
)
from libcomcat.search import get_event_by_id, search


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, "..", "data")
    cassettes = os.path.join(homedir, "cassettes")
    return cassettes, datadir


def test_summary():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "classes_summary.yaml")
    with vcr.use_cassette(tape_file):
        eventlist = search(
            starttime=datetime(1994, 1, 17, 12, 30),
            endtime=datetime(1994, 1, 18, 12, 35),
            minmagnitude=6.6,
        )
        event = eventlist[0]
        cmp = "ci3144585 1994-01-17 12:30:55.390000 (34.213,-118.537) " "18.2 km M6.7"
        assert str(event) == cmp
        assert event.id == "ci3144585"
        assert event.time == datetime(1994, 1, 17, 12, 30, 55, 390000)
        assert event.latitude == 34.213
        assert event.longitude == -118.537
        assert event.depth == 18.202
        assert event.magnitude == 6.7
        assert "cdi" in event.properties
        assert event["cdi"] >= 8.6
        assert event.hasProduct("shakemap")
        assert not event.hasProduct("foo")
        try:
            event["foo"]
            assert 1 == 2
        except AttributeError:
            pass
        assert event.hasProperty("cdi")
        assert not event.hasProperty("foo")
        assert isinstance(event.getDetailEvent(), DetailEvent)
        durl = (
            "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid="
            "ci3144585&format=geojson"
        )
        assert event.getDetailURL() == durl
        try:
            detail = event.getDetailEvent(includedeleted=True, includesuperseded=True)
            assert 1 == 2
        except ArgumentConflictError:
            pass

        # find an event that has multiple versions of shakemap to test
        # include superseded
        # official20110311054624120_30
        eventlist = search(
            starttime=datetime(2011, 3, 11, 0, 0),
            endtime=datetime(2011, 3, 12, 0, 0),
            minmagnitude=8.8,
        )
        honshu = eventlist[0]
        detail = honshu.getDetailEvent(includesuperseded=True)
        shakemaps = detail.getProducts("shakemap", source="all", version="all")
        assert shakemaps[1].source == "atlas"
        assert event.toDict()["depth"] == 18.202


def test_detail_product_versions():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "classes_detailsummary.yaml")
    with vcr.use_cassette(tape_file):
        eventid = "nn00570710"
        detail = get_event_by_id(eventid, includesuperseded=True)
        pref_origin_pref_source = detail.getProducts(
            "origin", source="preferred", version="last"
        )[0]
        pref_origin_pref_source2 = detail.getProducts("origin")[0]

        first_origin_pref_source = detail.getProducts(
            "origin", source="preferred", version="first"
        )[0]
        first_origin_us_source = detail.getProducts(
            "origin", source="us", version="first"
        )[0]
        last_origin_us_source = detail.getProducts(
            "origin", source="us", version="last"
        )[0]

        pref_origins_all_sources = detail.getProducts(
            "origin", source="all", version="last"
        )
        first_origins_all_sources = detail.getProducts(
            "origin", source="all", version="first"
        )

        assert pref_origin_pref_source.source == "nn"
        assert pref_origin_pref_source2.source == "nn"
        assert pref_origin_pref_source.version >= 7
        assert pref_origin_pref_source2.version >= 7
        assert first_origin_pref_source.source == "nn"
        assert first_origin_pref_source.version == 1
        assert first_origin_us_source.source == "us"
        assert first_origin_us_source.version == 1
        assert last_origin_us_source.source == "us"
        assert last_origin_us_source.version >= 5

        sources = []
        for origin in pref_origins_all_sources:
            source = origin.source
            version = origin.version
            assert source not in sources
            sources.append(source)

        sources = []
        for origin in first_origins_all_sources:
            source = origin.source
            version = origin.version
            assert source not in sources
            assert version == 1
            sources.append(source)


def test_moment_supplement():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "classes_moment.yaml")
    with vcr.use_cassette(tape_file):
        eventid = "us2000ar20"  # 2017 M7.1 Mexico City
        detail = get_event_by_id(eventid)
        edict = detail.toDict(get_moment_supplement=True, get_tensors="preferred")
        assert edict["us_Mww_percent_double_couple"] == 0.9992


def test_detail():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "classes_detailevent.yaml")
    with vcr.use_cassette(tape_file, record_mode="once"):
        eventid = "ci3144585"  # northridge
        fmt = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/" "detail/%s.geojson"
        url = fmt % eventid
        event = DetailEvent(url)
        assert str(event) == (
            "ci3144585 1994-01-17 12:30:55.390000 " "(34.213,-118.537) 18.2 km M6.7"
        )
        assert event.hasProduct("shakemap")
        assert event.hasProduct("foo") is False
        assert event.hasProperty("foo") is False
        assert event.hasProperty("time")
        try:
            event["foo"]
            assert 1 == 2
        except AttributeError:
            pass

        try:
            event.getNumVersions("foo")
            assert 1 == 2
        except ProductNotFoundError:
            pass

        try:
            event.getProducts("foo")
            assert 1 == 2
        except ProductNotFoundError:
            pass

        try:
            event.getProducts("shakemap", source="foo")
            assert 1 == 2
        except ProductNotFoundError:
            pass

        assert event.toDict()["magnitude"] == 6.7

        eventid = "nc72282711"  # Napa 2014 eq, multiple origins and MTs.
        # cievent = get_event_by_id(eventid,catalog='ci')
        # usevent = get_event_by_id(eventid,catalog='us')
        # atevent = get_event_by_id(eventid,catalog='at')
        event = get_event_by_id(eventid)

        # smoke test
        _ = event.getProducts("phase-data", source="all")

        ncdict = event.toDict(catalog="nc")
        usdict = event.toDict(catalog="us")
        atdict = event.toDict(catalog="at")

        try:
            event.toDict(catalog="foo")
            assert 1 == 2
        except ProductNotFoundError:
            pass

        assert ncdict["depth"] == 11.12
        assert usdict["depth"] == 11.25
        assert atdict["depth"] == 9.0

        ncdict_allmags = event.toDict(get_all_magnitudes=True)
        allmags = []
        for key, value in ncdict_allmags.items():
            if key.startswith("magtype"):
                allmags.append(value)
        cmpmags = ["Md", "Ml", "Ms_20", "Mw", "Mwb", "Mwc", "Mwr", "Mww", "mb", "mw"]
        assert set(allmags) == set(cmpmags)

        ncdict_alltensors = event.toDict(get_tensors="all")
        assert ncdict_alltensors["us_Mwb_mrr"] == 7.63e16
        ncdict_allfocals = event.toDict(get_focals="all")
        assert ncdict_allfocals["nc_np1_strike"] == 345.0

        assert event.getNumVersions("shakemap") > 0
        assert isinstance(event.getProducts("shakemap")[0], Product)
        assert event.latitude == 38.2151667
        assert event.longitude == -122.3123333
        assert event.depth == 11.12
        assert event.id == eventid
        assert event.time == datetime(2014, 8, 24, 10, 20, 44, 70000)
        assert "sources" in event.properties
        assert event["mag"] == 6.02

        # test all of the different functionality of the getProducts() method
        # first, test default behavior (get the most preferred product):
        # 2003 Central California
        event = get_event_by_id("nc21323712", includesuperseded=True)
        pref_shakemap = event.getProducts("shakemap")[0]
        assert pref_shakemap.source == "atlas"
        assert pref_shakemap.update_time >= datetime(2017, 4, 12, 10, 50, 9, 368000)
        assert pref_shakemap.preferred_weight >= 100000000

        # get the first Atlas shakemap
        first_shakemap = event.getProducts("shakemap", version="first", source="atlas")[
            0
        ]
        assert first_shakemap.source == "atlas"
        assert first_shakemap.update_time >= datetime(2015, 2, 4, 6, 1, 33, 400000)
        assert first_shakemap.preferred_weight >= 81

        # get the first nc shakemap
        first_shakemap = event.getProducts("shakemap", version="first", source="nc")[0]
        assert first_shakemap.source == "nc"
        assert first_shakemap.update_time >= datetime(2017, 3, 8, 20, 12, 59, 380000)
        assert first_shakemap.preferred_weight >= 231

        # get the last version of the nc shakemaps
        last_shakemap = event.getProducts("shakemap", version="last", source="nc")[0]
        assert last_shakemap.source == "nc"
        assert last_shakemap.update_time >= datetime(2017, 3, 17, 17, 40, 26, 576000)
        assert last_shakemap.preferred_weight >= 231

        # get all the nc versions of the shakemap
        shakemaps = event.getProducts("shakemap", version="all", source="nc")
        for shakemap4 in shakemaps:
            assert shakemap4.source == "nc"

        # get all versions of all shakemaps
        shakemaps = event.getProducts("shakemap", version="all", source="all")
        assert event.getNumVersions("shakemap") == len(shakemaps)


def test_product():
    cassettes, datadir = get_datadir()
    tape_file = os.path.join(cassettes, "classes_product.yaml")
    with vcr.use_cassette(tape_file):
        eventid = "ci3144585"  # northridge
        event = get_event_by_id(eventid)
        product = event.getProducts("shakemap")[0]
        assert product.preferred_weight == 100000000
        assert product.source == "atlas"
        assert product.update_time >= datetime(2017, 4, 12, 6, 25, 42, 120000)
        pnames = product.getContentsMatching("grid.xml")
        url = product.getContentURL("grid.xml")
        cmpurl = (
            "https://earthquake.usgs.gov/product/shakemap/"
            "ci3144585/atlas/1594159786829/download/grid.xml"
        )
        assert url == cmpurl
        assert len(product.getContentsMatching("foo")) == 0
        assert len(pnames) == 1
        cmpstr = (
            "Product shakemap from atlas updated "
            "2020-07-07 22:09:46.829000 containing "
            "58 content files."
        )
        assert str(product) == cmpstr
        assert product.hasProperty("maxmmi")
        assert "maxmmi" in product.properties
        assert product["maxmmi"] >= "8.6"
        assert "download/cont_mi.json" in product.contents
        assert product.getContentName("grid.xml") == "grid.xml"
        assert product.getContentName("foo") is None
        assert product.getContentURL("foo") is None

        try:
            product.getContent("foo", filename=None)
            assert 1 == 2
        except ContentNotFoundError:
            pass

        try:
            product["foo"]
            assert 1 == 2
        except AttributeError:
            pass

        try:
            handle, tfilename = tempfile.mkstemp()
            os.close(handle)
            product.getContent("info.json", tfilename)
            f = open(tfilename, "rt")
            jdict = json.load(f)
            f.close()
            assert float(jdict["input"]["event_information"]["depth"]) > 18.0
        except Exception:
            raise Exception("Failure to download Product content file")
        finally:
            os.remove(tfilename)

        # test getting content as a string.
        infobytes, url = product.getContentBytes("info.json")
        infostring = infobytes.decode("utf-8")
        jdict = json.loads(infostring)
        eid = jdict["input"]["event_information"]["event_id"]
        assert eid == "ci3144585"


if __name__ == "__main__":
    test_moment_supplement()
    test_detail_product_versions()
    test_summary()
    test_detail()
    test_product()
