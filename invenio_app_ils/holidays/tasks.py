# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Holidays tasks."""

from copy import deepcopy
from datetime import date

import arrow
from celery import shared_task
from invenio_circulation.proxies import current_circulation
from invenio_db import db

from invenio_app_ils.circulation.search import get_active_loans
from invenio_app_ils.holidays.api import next_open_after
from invenio_app_ils.proxies import current_app_ils


@shared_task
def extend_active_loans_holiday():
    """Extends all ongoing loans that would end on a holiday."""
    for hit in get_active_loans().scan():
        location_pid = hit.pickup_location_pid
        current_end_date = arrow.get(hit["request_expire_date"]).date()
        new_end_date = next_open_after(location_pid, current_end_date)
        if new_end_date and new_end_date != current_end_date:  # Update loan
            loan = current_circulation.loan_record_cls.get_record_by_pid(
                hit["pid"])
            loan.update(request_expire_date=new_end_date.strftime("%Y-%m-%d"))
            loan.commit()
            current_circulation.loan_indexer().index(loan)
    db.session.commit()


@shared_task
def clean_past_exceptions():
    """Deletes all past exceptions."""
    today = date.today()
    search_cls = current_app_ils.location_search_cls()
    location = current_app_ils.location_record_cls
    for hit in search_cls.scan():
        index = 0
        location_pid = hit.pid
        record = location.get_record_by_pid(location_pid)
        record_copy = deepcopy(record)
        for item in record_copy["opening_exceptions"]:
            end_date = arrow.get(item["end_date"]).date()
            if end_date < today:
                del record["opening_exceptions"][index]
                index -= 1
            index += 1
        record.commit()
        current_app_ils.location_indexer.index(record)
    db.session.commit()


def _send_loan_update_email():
    """Sends an email to the patron whose loan was updated."""
    pass
