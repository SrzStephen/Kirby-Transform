from typing import Any, Union
from marshmallow.validate import Validator, ValidationError
from datetime import datetime


class UnixEpoch(Validator):
    def __init__(self, min_timestamp: [float, None] = datetime(year=2019, month=1, day=1, hour=0, minute=1,
                                                               second=1).timestamp(),
                 max_timestamp: [float, None] = datetime(year=3000, month=1, day=1, hour=0, minute=1,
                                                         second=1).timestamp()):
        # I started this project in 2020, so no dates should be before 2019
        if not min_timestamp:
            self.min_timestmap = datetime(year=2019, month=1, day=1, hour=0, minute=1, second=1).timestamp()
        else:
            self.min_timestmap = min_timestamp

        # Some time vastly in the future.
        if not max_timestamp:
            self.max_timestamp = datetime(year=3000, month=1, day=1, hour=0, minute=1, second=1).timestamp()
        else:
            self.max_timestamp = max_timestamp

    def __call__(self, value) -> Any:
        if not (type(value) is int or type(value) is float):
            raise ValidationError(f"value {value} isn't an int or float")

        if self.max_timestamp:
            if value > self.max_timestamp:
                raise ValidationError(f"value {value} seems to be either not in seconds, or further than year 3000.")
        if self.min_timestmap:
            if value < self.min_timestmap:
                raise ValidationError(f"value {value} seems to be too far in the past")


class FieldValidator(Validator):
    def __init__(self):
        pass

    def __call__(self, value: dict, **kwargs) -> Any:
        non_numeric = dict()
        if type(value) is not dict:
            raise ValidationError(f"fields input isn't a dict. got {value}")
        for key, val in value.items():
            # blank dicts are fine
            if type(val) is dict:
                if len(val) == 0:
                    return
                else:
                    ValidationError(f"Don't know what to do with {value} for key {key}")

            if not (type(val) is float or type(val) is int):
                non_numeric[key] = val
        #if len(non_numeric) > 0:
        #    raise ValidationError(f"got metric fields that were non numeric {non_numeric}")



