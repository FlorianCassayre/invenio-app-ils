# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Circulation custom transitions."""

import arrow
from invenio_circulation.transitions.transitions import (
    ItemOnLoanToItemOnLoan, ToItemOnLoan)

from invenio_app_ils.holidays.api import next_open_after


def _update_loan_end_date(loan):
    """Update the end date to the next opening day."""
    current_end_date = arrow.get(loan["end_date"]).date()
    new_end_date = next_open_after(loan["pickup_location_pid"], current_end_date)
    if new_end_date:  # New end date must be defined
        loan["end_date"] = arrow.get(new_end_date)


class ILSToItemOnLoan(ToItemOnLoan):
    """Action to checkout."""

    def before(self, loan, initial_loan, **kwargs):
        """Update the end date to the next opening day."""
        super().before(loan, initial_loan, **kwargs)

        _update_loan_end_date(loan)


class ILSItemOnLoanToItemOnLoan(ItemOnLoanToItemOnLoan):
    """Extend action to perform a item loan extension."""

    def before(self, loan, initial_loan, **kwargs):
        """Update the end date to the next opening day."""
        super().before(loan, initial_loan, **kwargs)

        _update_loan_end_date(loan)
