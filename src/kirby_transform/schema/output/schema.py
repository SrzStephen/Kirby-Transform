from marshmallow import Schema
from marshmallow.fields import Dict, Float, String, Nested # I have an object called "fields" in my data
from kirby_transform.schema.validator import UnixEpoch
from marshmallow.schema import EXCLUDE, INCLUDE
from .validator import OutputTagValidator


class ImportantTags(Schema):
    class Meta:
        unknown = INCLUDE

    collector = String(required=True)
    version = String(required=True)  # todo validator


class BasicOutputTags(Schema):
    class Meta:
        unknown = EXCLUDE
        fields = Dict(required=True)
        tags = Nested(ImportantTags, required=True)
        timestamp = Float(required=True, validate=UnixEpoch())

class OutputDataSchema(Schema):
    class Meta:
        unknown = INCLUDE

    pass
