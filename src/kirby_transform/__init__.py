__version__ = "0.1.0"

from marshmallow import ValidationError

from kirby_transform.processor.processor import ProcessedData, Processor
from kirby_transform.schema.input.schema import CommonInput, NestedInputData


def setloglevel():
    # Set log level of various components
    raise NotImplementedError
