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
                         pre_load, validates)

_WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_WEEKDAY_INDICES = {weekday_name: i for i, weekday_name in enumerate(_WEEKDAY_NAMES)}


class OpeningWeekdaySchema(Schema):
    """Opening weekday."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    weekday = fields.Str(required=True)
    is_open = fields.Bool(required=True)

    @validates("weekday")
    def validate_weekday_name(self, value, **kwargs):
        """Validate weekday."""
        if value not in _WEEKDAY_NAMES:
            raise ValidationError("Illegal weekday name.", field_names=["weekday"])


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
        return data


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
        weekdays = data["opening_weekdays"]
        new_weekdays = [None for _ in _WEEKDAY_NAMES]

        exists_open = False
        for weekday in weekdays:
            name = weekday["weekday"]
            exists_open = exists_open or weekday["is_open"]
            index = _WEEKDAY_INDICES[name]
            if new_weekdays[index]:
                raise ValidationError(
                    "There are two distinct configurations for the same weekday.",
                    field_names=["opening_weekdays"])
            new_weekdays[index] = weekday
        if len(weekdays) != len(new_weekdays):
            raise ValidationError("A weekday configuration is missing.",
                                  field_names=["opening_weekdays"])
        if not exists_open:
            raise ValidationError("At least one weekday must be declared as open.",
                                  field_names=["opening_weekdays"])

        exceptions = data["opening_exceptions"]
        exceptions.sort(key=lambda ex: ex["start_date"])
        previous = None
        for exception in exceptions:
            if previous:
                if previous["end_date"] >= exception["start_date"]:
                    raise ValidationError("Exceptions must not overlap.",
                                          field_names=["opening_exceptions"])
            previous = exception

        return data
