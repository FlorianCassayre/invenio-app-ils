# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""ILS holidays API."""
from datetime import timedelta

from invenio_app_ils.proxies import current_app_ils

_weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_day_increment = timedelta(days=1)  # Atomic increment

def _is_normally_open(location, date):
    """
    Checks if the location is normally opened on a given date,
    according to the regular schedule.
    """
    opening = location["opening_weekdays"]
    assert len(opening) == len(_weekdays)
    weekday_number = date.weekday()
    opening_weekday = opening[weekday_number]
    assert opening_weekday["weekday"] == _weekdays[weekday_number]
    return opening_weekday["is_open"]


def _is_exceptionally_open(location, date):
    """
    Checks if the location is exceptionally opened on a given date,
    according to the exceptional schedule, or None is no exception
    is defined.
    """
    for exception in location["opening_exceptions"]:
        if date <= exception["end_date"]:
            if exception["start_date"] <= date:
                return exception["is_open"]
            else:
                return None  # Early return
    return None  # Exhaustion


def is_open_on(location_pid, date):
    """Checks if the location is open or closed on a given date."""
    location = current_app_ils.location_record_cls.get_record_by_pid(location_pid)
    exceptionally_open = _is_exceptionally_open(location, date)
    if exceptionally_open is not None:
        return exceptionally_open
    return _is_normally_open(location, date)


def _next_normally_open_after(location, date):
    """Finds the next normally open day."""
    for i in range(len(_weekdays)):  # Maximum number of iterations
        if _is_normally_open(location, date):
            return date
        else:
            date += _day_increment
    return None  # Not normally open


def next_open_after(location_pid, date):
    """Finds the next day where this location is open."""
    location = current_app_ils.location_record_cls.get_record_by_pid(location_pid)

    0 / 0
