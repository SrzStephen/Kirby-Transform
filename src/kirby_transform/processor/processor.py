from kirby_transform.schema.input.schema import NestedInputData, CommonInput
from kirby_transform.schema.output.schema import OutputDataSchema, OutputMetaSchema
from typing import List, Optional
from time import time
from kirby_transform import __version__
from numbers import Number
from marshmallow import ValidationError
from logging import getLogger
from typing import Union
from io import TextIOWrapper
from abc import abstractmethod
from dataclasses import dataclass

logger = getLogger(__name__)


def count_text(d: dict) -> int:
    return [isinstance(x, str) for x in d.values()].count(True)


def count_numeric(d: dict) -> int:
    return [isinstance(x, Number) and not isinstance(x, bool) for x in d.values()].count(True)


def count_bool(d: dict) -> int:
    return [isinstance(x, bool) for x in d.values()].count(True)


def make_data(data: List[dict], data_tags: dict, collector: str, version: str,
              root_timestamp: Union[None, float] = None) -> List[
    dict]:
    def inplace_add_tags(data: dict, collector: str, data_tags: Union[dict, None], version: str):
        """Add all the required tags to the data"""
        if type(data_tags) is dict:
            dtag = data_tags.copy()

        else:
            dtag = dict(collector=collector)
        if not data.get("tags", False):
            data['tags'] = dtag
        else:
            data['tags'].update(dtag)
        if "collector" not in data['tags'].keys():
            dtag.update(dict(collector=collector))
        data['tags']['version'] = version

    data_copy = data.copy()
    for item in data_copy:
        item['timestamp'] = root_timestamp if root_timestamp is not None else time()
        inplace_add_tags(data=item, collector=collector, data_tags=data_tags, version=version)
        assert(item['timestamp'] is not None)
    return data_copy


def make_meta_report_level(data: List[dict],
                           global_tags: Union[dict, None],
                           uptime: Union[float, None],
                           messages: Union[int, None],
                           collector: str,
                           destination: str,
                           language: str,
                           platform: str,
                           version: str,
                           timestamp: [float, None]) -> dict:
    """should be called after on the data from make_data"""
    d = data.copy()
    numeric_metrics = 0
    bool_metrics = 0
    total_metrics = 0
    text_metrics = 0
    total_tags = 0
    return_items = list
    report_time = timestamp if timestamp is not None else time()
    for item in d:
        fields: dict = item['fields']
        tags: dict = item['tags']
        total_tags += len(tags.keys())
        numeric_metrics += count_numeric(fields)
        bool_metrics += count_bool(fields)
        text_metrics += count_text(fields)
        total_metrics += len(fields.keys())

    top_level_metrics = dict(
        uptime=uptime,
        continous_messages=messages,
        total_text_metrics=text_metrics,
        total_numeric_metrics=numeric_metrics,
        total_bool_metrics=bool_metrics,
        total_metrics=total_metrics,
        total_tags=total_tags,
        total_reports=len(d)
    )
    for metric in ['uptime, continuous_messages']:
        if top_level_metrics.get(metric, None) is not None:
            top_level_metrics.pop(metric)
    top_level_tags = dict(
        collector=collector,
        destination=destination,
        language=language,
        platform=platform,
        version=version,
        processor_version=__version__
    )
    if global_tags is not None:
        top_level_tags.update(global_tags)

    return dict(
        fields=top_level_metrics,
        tags=top_level_tags,
        timestamp=report_time
    )


def make_meta_data_level(data: List[dict], top_level_tags: Union[dict, None]) -> List[dict]:
    d = data.copy()
    return_data = []
    for item in d:
        tags = item['tags']
        fields = item['fields']
        timestamp = item['timestamp']
        data_metrics = dict(
            meta_text_metrics=count_text(fields),
            meta_numeric_metrics=count_numeric(fields),
            meta_bool_metrics=count_bool(fields),
            meta_total_metrics=len(fields.keys()),
            meta_total_tags=len(tags.keys()),
        )
        if top_level_tags is not None:
            tags.update(top_level_tags)
        return_data.append(dict(
            fields=data_metrics,
            tags=tags,
            timestamp=timestamp
        ))
    return return_data


class Processor(object):
    """I have a chicken and egg probkem. I would like to include the report in the initing of the processor
    But then it becomes a giant pain for anything inheriting it to expose funtions
    So I'm splitting out the actual processor and its processing"""

    def __init__(self):

        self.InputSchema = CommonInput()
        self.processed = False
        # Placeholders, get populated when process is called
        self.__data: [List[dict]] = []
        self.__meta_data: [List[dict]] = []
        self.__report_level_meta: dict = {}
        self.__data_level_meta: List[dict] = []

    def process(self, report: dict):  # TODO support filepaths + IO + string dicts
        try:
            self.__original_report = report.copy()
            self.__converted_report = CommonInput().load(self.__original_report)
        except ValidationError as e:
            logger.error(f"Failed to generate a proper report \n {self.__original_report} \n {e}")
            raise

        self.generate_data()
        self.generate_meta()
        self.processed = True
        return self

    def generate_data(self):
        d = self.__converted_report
        data = make_data(
            data=d.get('data'),
            data_tags=d.get('data_tags'),
            collector=d.get('collector'),
            root_timestamp=d.get('timestamp'),
            version=d.get('version'))
        self.__data = data

    def generate_meta(self):
        d = self.__converted_report
        self.__report_level_meta = make_meta_report_level(data=self.__data,
                                                          global_tags=d.get('meta_tags'),
                                                          uptime=d.get('uptime'),
                                                          messages=d.get('messages'),
                                                          collector=d.get('collector'),
                                                          destination=d.get('destination'),
                                                          language=d.get('language'),
                                                          platform=d.get('platform'),
                                                          timestamp=d.get('timestamp'),
                                                          version=d.get('version'))

        self.__data_level_meta = make_meta_data_level(self.__data, d.get("meta_tags"))

    @property
    def data(self):
        if not self.processed:
            raise ValueError("You need to call process before trying to get data")
        return self.__data.copy()

    @property
    def meta_data(self):
        if not self.processed:
            raise ValueError("You need to call process before trying to get data")
        return_data = self.__data_level_meta.copy()
        return_data.append(self.__report_level_meta.copy())
        return return_data

    @property
    def report_meta_data(self):
        if not self.processed:
            raise ValueError("You need to call process before trying to get data")
        return self.__report_level_meta.copy()

    @property
    def data_meta_data(self):
        if not self.processed:
            raise ValueError("You need to call process before trying to get data")
        return self.__data_level_meta.copy()

    @property
    def parsed_report(self):
        if not self.processed:
            raise ValueError("You need to call process before trying to get data")
        return self.__converted_report.copy()

    @staticmethod
    def get_input_validator():
        return CommonInput()

    @staticmethod
    def get_output_data_validator():
        return OutputDataSchema()

    @staticmethod
    def get_metadata_schemas():
        return OutputMetaSchema()

    @staticmethod
    def report_is_valid(data: dict):
        try:
            Processor.get_input_validator().load(data)
            return True
        except Exception as e:
            logger.warning(f"Failed to parse with error {e}")
            return False

    @abstractmethod
    def generate_output(self, data: List[dict]):
        raise NotImplementedError

    @abstractmethod
    def send_all(self) -> bool:
        raise NotImplementedError
