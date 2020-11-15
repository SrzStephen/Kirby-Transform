from kirby_transform.test import get_sucessful_files, get_failed_files, input_combinations
from json import load, JSONDecodeError
from unittest import TestCase
from pathlib import Path


class TestBasic(TestCase):
    """ If any of these fail then pretty much every test is expected to fail so testing these properly is worthwhile"""

    def test_get_successful_files(self):

        self.assertGreater(len(list(get_sucessful_files())), 0)
        for path, file in get_sucessful_files():
            self.assertIsInstance(path, Path)
            self.assertIsInstance(file, dict)

    def test_combination_tester(self):
        for file, data in get_sucessful_files():
            for report, combo in input_combinations(data):
                missing_toplevel = combo['missing_toplevel']
                missing_datalevel = combo['missing_datalevel']
                for key in missing_toplevel:
                    self.assertNotIn(key,report)
                for item in report['data']:
                    for data_key in missing_datalevel:
                        self.assertNotIn(data_key, item)
