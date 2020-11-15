from marshmallow import Schema
from marshmallow.fields import Dict, Float  # I have an object called "fields" in my data
from kirby_transform.schema.validator import UnixEpoch
from .validator import OutputTagValidator


class OutputMetaSchema(Schema):
    timestamp = Float(required=True, validate=UnixEpoch())
    tags = Dict(required=True, validate=OutputTagValidator())
    fields = Dict(required=True, validate=OutputTagValidator())


class OutputDataSchema(Schema):
    timestamp = Float(required=True, validate=UnixEpoch())
    tags = Dict(required=True, validate=OutputTagValidator())
    fields = Dict(required=True, validate=OutputTagValidator())


class OutputSchema:
    meta = OutputMetaSchema
    data = OutputDataSchema
