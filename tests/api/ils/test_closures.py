# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Location closures tests."""

import json

from flask import url_for

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
