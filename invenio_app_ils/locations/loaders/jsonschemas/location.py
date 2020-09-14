# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Location schema for marshmallow loader."""

from invenio_records_rest.schemas import RecordMetadataSchemaJSONV1
from invenio_records_rest.schemas.fields import PersistentIdentifier
from marshmallow import EXCLUDE, Schema, fields


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
