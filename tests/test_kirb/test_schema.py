from kirby_transform.test import get_sucessful_files
from kirby_transform.schema import CommonInput, NestedInputData, ValidationError, FieldValidator, UnixEpoch
from unittest import TestCase
from json import load
from typing import List, Tuple
from pathlib import Path
data_dir = Path(__file__).parent.parent.absolute() / 'data'

class InputSchemaTest(TestCase):
    def setUp(self) -> None:
        self.InputSchema = CommonInput()

    def test_in(self):
        """Test known good inputs"""
        for filename, data in get_sucessful_files(data_dir):
            try:
                self.InputSchema.load(data)
            except Exception as e:
                print(f"failed on {filename.name}")
                print(data)
                raise
    def test_failure(self):

            for filename,data in get_sucessful_files(data_dir):
                required_fields = [x.name for x in self.InputSchema.fields.values() if x.required == True]
                for field in required_fields:
                    with self.assertRaises(expected_exception=ValidationError):
                        d = data.copy().pop(field)
                        self.InputSchema.load(d)

    def test_nested_data(self):
        NestedFormat = NestedInputData()
        for filename, data in get_sucessful_files(data_dir):
                data = data['data']
                for entry in data:
                    try:
                        NestedFormat.load(entry)
                    except Exception as e:
                        print(f"failed on {filename.path}")
                        raise


class TestInputValidators(TestCase):
    """Custom validators"""

    def test_datafield(self):
        validator = FieldValidator()
        validator(dict())
        mydict = dict(dict(a=1, b=2.2, c=3.14))
        validator(mydict)
        mydict["invalid"] = "foo"
        with self.assertRaises(expected_exception=ValidationError):
            validator(mydict)

    def test_unix_epoch(self):
        validator = UnixEpoch()
        # string instead of numeric
        invalid_inputs = ["1588517294", 1546272061.0 * 1000]
        for input in invalid_inputs:
            with self.assertRaises(expected_exception=ValidationError):
                validator(input)
        validator(1588517294)
