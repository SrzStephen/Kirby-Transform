from typing import Any

from marshmallow.validate import ValidationError, Validator


class OutputTagValidator(Validator):
    def __init__(self):
        self.important_keys = ["source", "version", "collector", "platform"]

    def __call__(self, value: dict, **kwargs) -> Any:
        missing_keys = []
        keys = value.keys()
        for key in self.important_keys:
            if key not in keys:
                missing_keys.append(key)
        if len(missing_keys) > 0:
            raise ValidationError(f"Missing important keys {missing_keys} from {value}")
        
class OutputDataValidator(Validator):
    pass