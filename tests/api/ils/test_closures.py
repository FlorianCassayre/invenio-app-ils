# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Location closures tests."""

import json

import arrow
from flask import url_for

from invenio_app_ils.closures.api import find_next_open_date
from invenio_app_ils.proxies import current_app_ils
from tests.helpers import user_login

_test_location_pid = "locid-1"
_weekdays = ["monday", "tuesday", "wednesday",
             "thursday", "friday", "saturday", "sunday"]


def _build_location_closures_data(closed_weekdays, exceptions):
    opening_weekdays = []
    for name in _weekdays:
        obj = {
            "weekday": name,
            "is_open": name not in closed_weekdays
        }
        opening_weekdays.append(obj)

    opening_exceptions = []
    for start_date, end_date, is_open in exceptions:
        opening_exceptions.append({
            "title": "%s - %s" % (start_date, end_date),
            "start_date": start_date,
            "end_date": end_date,
            "is_open": is_open
        })

    return {
        "opening_weekdays": opening_weekdays,
        "opening_exceptions": opening_exceptions
    }


def _date_from_string(date_string):
    return arrow.get(date_string).date()


def test_location_validation(client, json_headers, users, testdata):
    def _test_update_location_closures(data, expected_code):
        url = url_for("invenio_records_rest.locid_item",
                      pid_value=_test_location_pid)
        res = client.get(url, headers=json_headers)
        assert res.status_code == 200
        metadata = res.get_json()["metadata"]
        metadata.update(data)
        res = client.put(url, headers=json_headers, data=json.dumps(metadata))
        assert res.status_code == expected_code

    def _test_update_location_closures_data(
        closed_weekdays, exceptions, expected_code
    ):
        _test_update_location_closures(
            _build_location_closures_data(closed_weekdays, exceptions),
            expected_code
        )

    user_login(client, "librarian", users)

    # Weekdays

    _test_update_location_closures({
        "opening_weekdays":
            [{"weekday": w, "is_open": True} for w in _weekdays],
        "opening_exceptions": []
    }, 200)

    _test_update_location_closures({
        "opening_weekdays":
            [{"weekday": w, "is_open": True} for w in _weekdays[::-1]],
        "opening_exceptions": []
    }, 200)

    _test_update_location_closures({
        "opening_weekdays":
            [{"weekday": w, "is_open": False} for w in _weekdays],
        "opening_exceptions": []
    }, 400)

    _test_update_location_closures({
        "opening_weekdays":
            [{"weekday": w, "is_open": True} for w in _weekdays[:6]],
        "opening_exceptions": []
    }, 400)

    _test_update_location_closures({
        "opening_weekdays":
            [{"weekday": w, "is_open": True}
             for w in _weekdays[:6] + ["monday"]],
        "opening_exceptions": []
    }, 400)

    _test_update_location_closures({
        "opening_weekdays": [{"weekday": "foobar", "is_open": True}],
        "opening_exceptions": []
    }, 400)

    # Exceptions

    _test_update_location_closures_data(["saturday", "sunday"], [
        ["2000-01-01", "2000-01-05", False],
        ["2000-01-07", "2000-01-09", True],
        ["2000-01-10", "2000-01-15", True],
    ], 200)

    _test_update_location_closures_data(["saturday", "sunday"], [
        ["2000-01-12", "2000-01-17", True],
        ["2000-01-07", "2000-01-11", False],
        ["2000-01-02", "2000-01-04", True],
    ], 200)

    _test_update_location_closures_data([], [
        ["2000-01-01", "2000-01-05", False],
        ["2000-01-04", "2000-01-08", False],
    ], 400)

    _test_update_location_closures_data([], [
        ["2000-01-01", "2000-01-05", False],
        ["2000-01-04", "2000-01-08", True],
    ], 400)

    _test_update_location_closures_data([], [
        ["2000-01-01", "2000-01-01", False],
        ["2000-01-01", "2000-01-01", False],
    ], 400)

    _test_update_location_closures_data([], [
        ["2000-01-02", "2000-01-01", True],
    ], 400)


def test_find_next_open_date(app, db, testdata):
    def _update_location_closures_data(closed_weekdays, exceptions):
        Location = current_app_ils.location_record_cls
        record = Location.get_record_by_pid(_test_location_pid)

        record.update(
            _build_location_closures_data(closed_weekdays, exceptions))
        record.commit()
        db.session.commit()
        current_app_ils.location_indexer.index(record)

        return record

    def _test(start_date, expected_next_open_date):
        next_open = find_next_open_date(
            _test_location_pid, _date_from_string(start_date)
        )
        if expected_next_open_date:
            assert next_open == _date_from_string(expected_next_open_date)
        else:
            assert next_open is None

    """
    Mon. Tue. Wed. Thu. Fri. Sat. Sun.
     27   28   29   30   31  -01  -02
    x03  x04  x05   06   07  -08  -09
    x10  x11  x12  x13  x14  x15  x16
    x17  x18  x19  x20  x21  x22  -23
    x24   25   26  x27  x28  o29  o30
     31   01   02   03   04  -05  -06
    """

    closed_weekdays = ["saturday", "sunday"]
    exceptions = [
        ["2000-01-03", "2000-01-05", False],  # Mon. - Wed.
        ["2000-01-09", "2000-01-22", False],  # Sun. - Sat.
        ["2000-01-24", "2000-01-24", False],  # Mon.
        ["2000-01-27", "2000-01-28", False],  # Thu. - Fri.
        ["2000-01-29", "2000-01-30", True],   # Sat. - Sun.
    ]
    _update_location_closures_data(closed_weekdays, exceptions)

    _test("2000-01-01", "2000-01-06")
    _test("2000-01-04", "2000-01-06")
    _test("2000-01-06", "2000-01-06")
    _test("2000-01-07", "2000-01-07")

    _test("2000-01-09", "2000-01-25")
    _test("2000-01-13", "2000-01-25")

    _test("2000-01-26", "2000-01-26")
    _test("2000-01-27", "2000-01-29")
    _test("2000-01-30", "2000-01-30")

    _test("2000-02-05", "2000-02-07")
