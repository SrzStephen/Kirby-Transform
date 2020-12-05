from marshmallow import Schema
from marshmallow.schema import EXCLUDE, INCLUDE
from marshmallow.fields import Dict, Float, String, Int, List, Nested
from kirby_transform.schema.validator import UnixEpoch, FieldValidator


# Don't include typing in here because some of the namespaces conflict


class NestedInputData(Schema):  # Defines valid entries in data
    class Meta:
        unknown = EXCLUDE

    tags = Dict(required=False)
    fields = Dict(required=True, validate=FieldValidator())
    timestamp = Float(required=False, validate=UnixEpoch())


class CommonInput(Schema):
    class Meta:
        unknown = EXCLUDE

    collector = String(required=True)
    data = List(Dict, required=True)  # Rather than validating NestedInputData, assume the processor will do that.
    data_tags = Dict(required=False)
    destination = String(required=True)
    language = String(required=True)
    messages = Int(required=False)
    meta_tags = Dict(required=False)
    platform = String(required=True)
    timestamp = Float(required=False, validate=UnixEpoch())
    uptime = Float(required=False)
    version = String(required=True)
