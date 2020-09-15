# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Holidays tasks."""

import arrow
from celery import shared_task
from invenio_db import db

from invenio_app_ils.circulation.search import get_active_loans
from invenio_app_ils.holidays.api import next_open_after
from invenio_app_ils.proxies import current_app_ils


@shared_task
def extend_active_loans_holiday():
    """Extends all ongoing loans that would end on a holiday."""
    Location = current_app_ils.location_record_cls
    cached = {}  # pid -> location
    for hit in get_active_loans().scan():
        location_pid = hit.pickup_location_pid
        if location_pid in cached:
            record = cached[location_pid]
        else:
            record = Location.get_record_by_pid(location_pid)
            cached[location_pid] = record

        current_end_date = arrow.get(record["end_date"]).date()
        new_end_date = next_open_after(location_pid, current_end_date)
        if new_end_date and new_end_date != new_end_date:  # Update loan
            record.update({"end_date": new_end_date})
            record.commit()
            db.session.commit()
            current_app_ils.location_indexer.index(record)


def _send_loan_update_email():
    """Sends an email to the patron whose loan was updated."""
    pass
