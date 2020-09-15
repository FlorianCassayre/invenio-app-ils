# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Holidays tests."""

import arrow
import pytest

from invenio_app_ils.holidays.api import next_open_after
from invenio_app_ils.proxies import current_app_ils

_test_location_pid = "locid-1"
_today = "2000-01-01"  # was on a saturday (and it was cloudy)


@pytest.fixture()
def holidays_data(app, db, testdata):
    Location = current_app_ils.location_record_cls
    record = Location.get_record_by_pid(_test_location_pid)

    weekdays = ["monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday"]
    opening_weekdays = []
    for name in weekdays:
        obj = {
            "weekday": name,
            "is_open": name not in ["saturday", "sunday"]  # Closed on weekends
        }
        opening_weekdays.append(obj)

    exceptions = [
        ["2000-01-03", "2000-01-05", False],  # Mon. - Wed.
        ["2000-01-09", "2000-01-22", False],  # Sun. - Sat.
        ["2000-01-24", "2000-01-24", False],  # Mon.
        ["2000-01-27", "2000-01-28", False],  # Thu. - Fri.
        ["2000-01-29", "2000-01-30", True],   # Sat. - Sun.
    ]
    opening_exceptions = []
    for start_date, end_date, is_open in exceptions:
        opening_exceptions.append({
            "title": "%s - %s" % (start_date, end_date),
            "start_date": start_date,
            "end_date": end_date,
            "is_open": is_open
        })

    record.update({
        "opening_weekdays": opening_weekdays,
        "opening_exceptions": opening_exceptions
    })
    record.commit()
    db.session.commit()
    current_app_ils.location_indexer.index(record)

    return record


def _date_from_string(date_string):
    return arrow.get(date_string).date()


def test_next_open(holidays_data):
    def _test(start_date, expected_next_open_date):
        next_open = next_open_after(
            _test_location_pid, _date_from_string(start_date)
        )
        assert next_open == _date_from_string(expected_next_open_date)

    """
    Mon. Tue. Wed. Thu. Fri. Sat. Sun.
     27   28   29   30   31  -01  -02
    x03  x04  x05   06   07  -08  -09
    x10  x11  x12  x13  x14  x15  x16
    x17  x18  x19  x20  x21  x22  -23
    x24   25   26  x27  x28  o29  o30
     31   01   02   03   04  -05  -06
    """

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
