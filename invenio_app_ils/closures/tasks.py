# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Location closures tasks."""

import json
from datetime import date

import arrow
from celery import shared_task
from invenio_circulation.proxies import current_circulation
from invenio_db import db

from invenio_app_ils.circulation.mail.tasks import (
    celery_logger, send_loan_end_date_updated_mail)
from invenio_app_ils.circulation.search import get_active_loans
from invenio_app_ils.closures.api import find_next_open_date
from invenio_app_ils.proxies import current_app_ils


def _log(action, data):
    """Structured logging."""
    log_msg = dict(
        name="ils_closures",
        action=action,
        data=data,
    )
    celery_logger.info(json.dumps(log_msg, sort_keys=True))


@shared_task
def clean_locations_past_closures_exceptions():
    """Deletes all past exceptions."""
    today = date.today()
    search_cls = current_app_ils.location_search_cls()
    location = current_app_ils.location_record_cls
    for hit in search_cls.scan():
        location_pid = hit.pid
        record = location.get_record_by_pid(location_pid)
        cleaned_exceptions = []
        modified = False
        for item in record["opening_exceptions"]:
            end_date = arrow.get(item["end_date"]).date()
            if end_date >= today:
                cleaned_exceptions.append(item)
            else:
                modified = True
        if modified:
            _log("clean_exceptions_before", record)
            record["opening_exceptions"] = cleaned_exceptions
            record.commit()
            db.session.commit()
            current_app_ils.location_indexer.index(record)
            _log("clean_exceptions_after", record)


@shared_task
def extend_active_loans_location_closure():
    """Extends all ongoing loans that would end on a closure."""
    for hit in get_active_loans().scan():
        location_pid = hit.pickup_location_pid
        current_end_date = arrow.get(hit.end_date).date()
        new_end_date = find_next_open_date(location_pid, current_end_date)
        if new_end_date != current_end_date:  # Update loan
            loan = current_circulation.loan_record_cls.get_record_by_pid(
                hit.pid)
            _log("extend_loan_closure_before", loan)
            loan.update(end_date=new_end_date.isoformat())
            loan.commit()
            current_circulation.loan_indexer().index(loan)
            _log("extend_loan_closure_after", loan)
            send_loan_end_date_updated_mail(loan)
    db.session.commit()
