# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Location schema for marshmallow loader."""

from invenio_records_rest.schemas import RecordMetadataSchemaJSONV1
from invenio_records_rest.schemas.fields import PersistentIdentifier
from marshmallow import EXCLUDE, Schema, fields, pre_load, ValidationError, post_load


class OpeningWeekdaySchema(Schema):
    """Opening weekday."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    weekday = fields.Str(required=True)
    is_open = fields.Str(required=True)


class OpeningExceptionSchema(Schema):
    """Opening exception."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    title = fields.Str()
    is_open = fields.Bool(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @pre_load
    def validate_dates(self, data, **kwargs):
        """Validate dates."""
        if data["end_date"] < data["start_date"]:
            raise ValidationError("End date cannot happen before start date.",
                                  field_names=["start_date", "end_date"])


class LocationSchemaV1(RecordMetadataSchemaJSONV1):
    """Location schema."""

    pid = PersistentIdentifier()
    name = fields.Str(required=True)
    address = fields.Str()
    email = fields.Email()
    phone = fields.Str()
    notes = fields.Str()
    opening_weekdays = fields.List(fields.Nested(OpeningWeekdaySchema))
    opening_exceptions = fields.List(fields.Nested(OpeningExceptionSchema))

    @post_load
    def postload_checks(self, data, **kwargs):
        """Validate record."""
        record = self.context["record"]
        exceptions = record["opening_exceptions"]
        for i in range(len(exceptions)):
            exception = exceptions[i]
            if i > 0:
                previous = exceptions[i - 1]
                if previous["end_date"] >= exception["start_date"]:
                    raise ValidationError("Exceptions must be sorted and not overlap.",
                                          field_names=["opening_exceptions"])
