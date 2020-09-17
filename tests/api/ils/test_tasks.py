# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test location closure cronjobs."""

import time

import arrow
from invenio_circulation.proxies import current_circulation

from invenio_app_ils.closures.tasks import \
    clean_locations_past_closures_exceptions
from invenio_app_ils.proxies import current_app_ils

_test_location_pid = "locid-1"
_test_location_pid_2 = "locid-2"
_test_loan_pid = "loanid-6"
_test_loan_pid_2 = "loanid-5"

opening_exceptions_with_past_exceptions = [
    {
        "title": "Past holidays",
        "is_open": False,
        "start_date": "2010-01-01",
        "end_date": "2010-01-06",
    },
    {
        "title": "Past holidays",
        "is_open": False,
        "start_date": "2013-04-05",
        "end_date": "2013-04-08",
    },
    {
        "title": "Past holiday",
        "is_open": False,
        "start_date": "2005-05-14",
        "end_date": "2005-05-16",
    },
    {
        "title": "Past holidays",
        "is_open": False,
        "start_date": "2019-02-01",
        "end_date": "2019-02-06",
    },
    {
        "title": "Future holidays",
        "is_open": False,
        "start_date": "2100-02-11",
        "end_date": "2100-02-12",
    },
    {
        "title": "Future holidays",
        "is_open": False,
        "start_date": "2100-03-01",
        "end_date": "2100-03-06",
    }
]

opening_exceptions_without_changes = [
    {
        "title": "Future holidays",
        "is_open": False,
        "start_date": "2110-01-01",
        "end_date": "2110-01-06",
    },
    {
        "title": "Future holidays",
        "is_open": False,
        "start_date": "2113-04-05",
        "end_date": "2113-04-08",
    },
    {
        "title": "Future holidays",
        "is_open": False,
        "start_date": "2105-05-14",
        "end_date": "2105-05-16",
    },
    {
        "title": "Future holidays",
        "is_open": False,
        "start_date": "2119-02-01",
        "end_date": "2119-02-06",
    },
    {
        "title": "Future holidays",
        "is_open": False,
        "start_date": "2100-02-11",
        "end_date": "2100-02-12",
    },
    {
        "title": "Future holidays",
        "is_open": False,
        "start_date": "2100-03-01",
        "end_date": "2100-03-06",
    }
]


def prepare_data(db, location_pid, opening_exceptions):
    """Adds some opening exceptions to a concrete location."""

    location = current_app_ils.location_record_cls
    record = location.get_record_by_pid(location_pid)

    record.update({"opening_exceptions": opening_exceptions})
    record.commit()
    db.session.commit()
    current_app_ils.location_indexer.index(record)


def prepare_loans_data(db, testdata):
    """Updates the expire date of a loan to match a closure day."""
    loans = testdata["loans"]

    def new_expiration_date(loanTestData, date):
        loan = current_circulation.loan_record_cls.get_record_by_pid(
            loanTestData["pid"])
        loan.update(end_date=date.isoformat())
        loan.commit()
        db.session.commit()
        current_circulation.loan_indexer().index(loan)

    # Change expiration date to match closure
    date = arrow.get("2100-03-03").date()
    date_2 = arrow.get("2100-02-12").date()
    new_expiration_date(loans[5], date)
    new_expiration_date(loans[4], date_2)


def opening_exceptions_cleaned():
    """Prepare data that should match with the response."""
    opening_exceptions = [
        {
            "title": "Future holidays",
            "is_open": False,
            "start_date": "2100-02-11",
            "end_date": "2100-02-12",
        },
        {
            "title": "Future holidays",
            "is_open": False,
            "start_date": "2100-03-01",
            "end_date": "2100-03-06",
        }
    ]

    return opening_exceptions


def test_clean_locations_past_closures_exceptions(
    db, users, testdata
):
    """Test cleaning of past exceptions."""
    prepare_data(db, _test_location_pid,
                 opening_exceptions_with_past_exceptions)
    prepare_data(db, _test_location_pid_2,
                 opening_exceptions_with_past_exceptions)
    clean_locations_past_closures_exceptions()
    location = current_app_ils.location_record_cls
    record = location.get_record_by_pid(_test_location_pid)
    record_2 = location.get_record_by_pid(_test_location_pid_2)

    assert record["opening_exceptions"] == opening_exceptions_cleaned()
    assert record_2["opening_exceptions"] == opening_exceptions_cleaned()
