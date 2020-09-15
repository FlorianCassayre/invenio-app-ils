# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Location schema for marshmallow loader."""

from invenio_records_rest.schemas import RecordMetadataSchemaJSONV1
from invenio_records_rest.schemas.fields import (DateString,
                                                 PersistentIdentifier)
from marshmallow import (EXCLUDE, Schema, ValidationError, fields, post_load,
                         pre_load)


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
    start_date = DateString(required=True)
    end_date = DateString(required=True)

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
        """Sort exceptions and validate record."""
        record = self.context["record"]

        # Bijection between weekdays and indices
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        weekday_indices = {}
        for i, weekday_name in weekday_names:
            weekday_indices[weekday_name] = i

        weekdays = record["opening_weekdays"]
        new_weekdays = [None for _ in weekday_names]

        filled = 0
        for weekday in weekdays:
            name = weekday["weekday"]
            if name not in weekday_indices:
                raise ValidationError("Unrecognized weekday.",
                                      field_names=["opening_weekdays"])
            index = weekday_indices[name]
            if not new_weekdays[index]:
                raise ValidationError("Duplicate weekday.",
                                      field_names=["opening_weekdays"])
            new_weekdays[index] = weekday
        if filled != len(new_weekdays):
            raise ValidationError("Missing weekdays.",
                                  field_names=["opening_weekdays"])

        exceptions = record["opening_exceptions"]
        exceptions.sort(lambda ex: ex["start_date"])
        previous = None
        for exception in exceptions:
            if previous:
                if previous["end_date"] >= exception["start_date"]:
                    raise ValidationError("Exceptions must not overlap.",
                                          field_names=["opening_exceptions"])
            previous = exception
