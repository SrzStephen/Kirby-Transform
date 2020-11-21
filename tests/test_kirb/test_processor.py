from kirby_transform.test import get_sucessful_files, input_combinations
from kirby_transform.processor import make_data, make_meta_data_level, make_meta_report_level, Processor
from kirby_transform.schema import CommonInput, NestedInputData
from unittest import TestCase
from time import time
from pathlib import Path
from io import StringIO
data_dir = Path(__file__).parent.parent.absolute() / 'data'

class TestDataGeneration(TestCase):
    def setUp(self) -> None:
        self.InputSchema = CommonInput()
        self.NestedInput = NestedInputData()

    def test_optional(self):
        for file, data in get_sucessful_files(data_dir):
            for report, combo in input_combinations(data):
                collector = report.get('collector', None)
                root_timestamp = report.get('timestamp', None)
                data_tags = report.get("data_tags", None)
                version = data.get("version", None)
                try:
                    made_data = make_data(report['data'], data_tags=data_tags, collector=collector,
                                          root_timestamp=root_timestamp, version=version)
                    self.assertIsInstance(made_data, list)
                    self.assertNotEqual(len(made_data), 0)
                    for item in made_data:
                        self.assertIsInstance(item, dict)

                    # Todo validate output properly
                except Exception as e:
                    print(f"Failed for file {file.name} with missing info {combo}")
                    raise

    def test_tags_get_added(self):
        for file, data in get_sucessful_files(data_dir):
            for report, combo in input_combinations(data):
                for remove_all_existing_tags in [False, True]:
                    if remove_all_existing_tags:
                        for entry in data['data']:
                            if entry.get("tags", False):
                                entry.pop("tags")

                    made_data = make_data(data['data'],
                                          data_tags=dict(should_see_this=True), collector="True", root_timestamp=time(),
                                          version="1.2.3.4")
                    for item in made_data:
                        self.assertIn("should_see_this", item['tags'])


class TestMetaGeneration(TestCase):
    def setUp(self) -> None:
        pass

    def test_data_level(self):
        for file, data in get_sucessful_files(data_dir):
            for report, combo in input_combinations(data):
                collector = report.get('collector', None)
                root_timestamp = report.get('timestamp', None)
                data_tags = report.get("data_tags", None)
                version = data.get("version", None)
                made_data = make_data(report['data'], data_tags=data_tags, collector=collector,
                                      root_timestamp=root_timestamp, version=version)
                made_report = make_meta_data_level(made_data, top_level_tags=report.get("meta_tags", None))
                for item in made_report:
                    fields = item['fields']
                    self.assertEqual(
                        fields['meta_text_metrics'] + fields['meta_bool_metrics'] + fields['meta_numeric_metrics'],
                        fields['meta_total_metrics'])

    def test_counts_are_correct_test(self):
        data = [
            dict(
                fields=dict(numeric=1, double=1.1, negdouble=-1.3, text="1", text2="test", booltest=True),
                timestamp=1605361755.1867568,
                tags=dict(foo="bar"))
        ]
        made_data = make_meta_data_level(data, top_level_tags=None)
        for item in made_data:
            fields = item['fields']
            textm = fields['meta_text_metrics']
            boolm = fields['meta_bool_metrics']
            numm = fields['meta_numeric_metrics']
            totalm = fields['meta_total_metrics']
            self.assertEqual(textm, 2)
            self.assertEqual(boolm, 1)
            self.assertEqual(numm, 3)

    def test_top_level(self):
        for file, data in get_sucessful_files(data_dir):
            for report, combo in input_combinations(data):
                collector = report.get('collector', None)
                root_timestamp = report.get('timestamp', None)
                data_tags = report.get("data_tags", None)
                version = data.get("version", None)
                made_data = make_data(report['data'], data_tags=data_tags, collector=collector,
                                      root_timestamp=root_timestamp, version=version)
                report_level_data = make_meta_report_level(data=made_data,
                                                           global_tags=data.get('meta_tags'),
                                                           uptime=data.get('uptime'),
                                                           messages=data.get('messages'),
                                                           collector=collector,
                                                           destination=data.get('destination'),
                                                           language=data.get('language'),
                                                           platform=data.get('platform'),
                                                           timestamp=root_timestamp,
                                                           version=data.get('version'))
                fields = report_level_data['fields']
                self.assertEqual(fields['total_metrics'],
                                 fields['total_bool_metrics'] + fields['total_numeric_metrics'] +
                                 fields['total_text_metrics'])
                self.assertIsNotNone(fields.values())


class TestProcessor(TestCase):
    def test_validation(self):
        for file, data in get_sucessful_files(data_dir):
            for report, combo in input_combinations(data):
                try:
                    self.assertTrue(Processor.report_is_valid(report))
                except Exception:
                    print(f"Failed on {file.name} with variants {combo}")
                    raise

    def test_processor(self):
        for file, data in get_sucessful_files(data_dir):
            for report, combo in input_combinations(data):
                try:
                    P = Processor().process(report)
                    self.assertIsNotNone(P.data)
                    self.assertIsNotNone(P.report_meta_data)
                    self.assertIsNotNone(P.data_meta_data)
                    self.assertIsNotNone(P.meta_data)
                    for item in P.data + P.meta_data:
                        # Todo output validator
                        self.assertIn("timestamp", item)
                        self.assertIsNotNone(item['timestamp'])
                        self.assertIn("collector", item['tags'])

                except Exception:
                    print(f"failed on {file.name} with variants {combo}")
                    print(report)
                    raise

    def test_fields_data(self):
        for file, data in get_sucessful_files(data_dir):
            for report, combo in input_combinations(data):
                try:
                    P = Processor().process(report)
                    for item in P.data:
                        self.assertIn("collector", item['tags'].keys())
                except Exception as e:
                    print(f"Failed with {file} and missing data {combo}")
                    raise
