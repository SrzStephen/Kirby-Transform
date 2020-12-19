from abc import abstractmethod
from logging import getLogger
from numbers import Number
from time import time
# from kirby_transform.schema. import OutputDataSchema, OutputMetaSchema
from typing import Any, List, Optional, Type, Union

from marshmallow import ValidationError

from kirby_transform import __version__
from kirby_transform.schema.input.schema import CommonInput, NestedInputData

logger = getLogger(__name__)


class ProcessedData(object):
    def __init__(self, data_level_metadata: List[dict], report_level_metadata: List[dict], data: List[dict]) -> None:
        self.__data = data
        self.__data_level_meta_data = data_level_metadata
        self.__report_level_meta_data = report_level_metadata

    @property
    def all_meta_data(self) -> List[dict]:
        return self.__data_level_meta_data.copy() + self.__report_level_meta_data.copy()

    @property
    def data(self) -> List[dict]:
        return self.__data.copy()

    @property
    def report_level_meta_data(self) -> List[dict]:
        return self.__report_level_meta_data.copy()

    @property
    def data_level_meta_data(self) -> List[dict]:
        return self.__data_level_meta_data.copy()

    def discard_strings(self) -> None:
        def trim_dict(data: dict) -> dict:
            return {k: v for k, v in data['fields'].items() if type(v) is not str}

        """Discards string fields in the ProcessedData object. Useful for things like OTSDB & Timestream"""

        def trim_from(data: list) -> List:
            if type(data) is list:
                for item in data:
                    if item.get('fields', None):
                        item['fields'] = trim_dict(item)
                return data

        self.__data = trim_from(self.__data)
        self.__data_level_meta_data = trim_from(self.__data_level_meta_data)
        self.__report_level_meta_data = trim_from(self.__report_level_meta_data)


class Processor(object):
    def __init__(self):
        self.ReportLevelSchema = CommonInput()
        self.DataLevelSchema = NestedInputData()
        self.OutputSchema = None

    @staticmethod
    def get_version() -> str:
        return __version__

    def _process(self, data: dict) -> Optional[ProcessedData]:
        valid_data = self.__valid_data(data.copy())
        if valid_data:
            # Mutate
            data = make_data(
                data=valid_data.get('data'),
                data_tags=valid_data.get('data_tags'),
                collector=valid_data.get('collector'),
                root_timestamp=valid_data.get('timestamp'),
                version=valid_data.get('version'))

            report_meta = make_meta_report_level(data=data,
                                                 global_tags=valid_data.get('meta_tags'),
                                                 uptime=valid_data.get('uptime'),
                                                 messages=valid_data.get('messages'),
                                                 collector=valid_data.get('collector'),
                                                 destination=valid_data.get('destination'),
                                                 language=valid_data.get('language'),
                                                 platform=valid_data.get('platform'),
                                                 timestamp=valid_data.get('timestamp'),
                                                 version=valid_data.get('version'))

            data_meta = make_meta_data_level(data, valid_data.get("meta_tags"))
            return ProcessedData(data_level_metadata=data_meta,
                                 report_level_metadata=report_meta,
                                 data=data)


        else:
            return None

    def process(self, data: dict) -> Optional[ProcessedData]:
        """Used in case inherited classes need to overwrite this (eg dropping all strings)"""
        return self._process(data)

    def report_is_valid(self, report: dict) -> bool:
        # Also checks whether there is _any_ valid data, so will reject no valid data fields
        valid_data = self.__valid_data(report.copy())
        return valid_data is not None and len(valid_data.get('data', 0)) != 0

    def __valid_data(self, data: dict) -> Optional[dict]:
        "Will return the report if correct and pull out  "
        try:
            d = data.copy()
            validated_data = self.ReportLevelSchema.load(d)
        except ValidationError:
            logger.exception("Failure in root level report")
            return None
        return_reports = []
        # Iterate through and return a list of good reports
        for index, report in enumerate(validated_data['data']):
            try:
                return_reports.append(self.DataLevelSchema.load(report).copy())
            except ValidationError as e:
                logger.info(f"skipping entry {index} of {report['collector']} because {e}")
                logger.debug(f"{report}")
                continue
        validated_data['data'] = return_reports
        return validated_data

    @staticmethod
    @abstractmethod
    def __generate_data(data: List[dict]) -> Any:
        """Takes in an input and gets it in the defined format"""

    @abstractmethod
    def send(self, data: ProcessedData) -> bool:
        """Used for sending everything"""

    @abstractmethod
    def send_data(self, data: List[dict], **kwargs) -> Optional[bool]:
        """Sending specific data. Assumes its in the common format"""


def count_text(d: dict) -> int:
    return [isinstance(x, str) for x in d.values()].count(True)


def count_numeric(d: dict) -> int:
    return [isinstance(x, Number) and not isinstance(x, bool) for x in d.values()].count(True)


def count_bool(d: dict) -> int:
    return [isinstance(x, bool) for x in d.values()].count(True)


def make_data(data: List[dict], data_tags: dict, collector: str, version: str,
              root_timestamp: Union[None, float] = None) -> List[dict]:
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
        assert (item['timestamp'] is not None)
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
                           timestamp: [float, None]) -> List[dict]:
    """should be called after on the data from make_data"""
    d = data.copy()
    numeric_metrics = 0
    bool_metrics = 0
    total_metrics = 0
    text_metrics = 0
    total_tags = 0
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
    # returning a list of single dict here because everything else is a list of dict, so makes manipulation a lot easier
    return [dict(
        fields=top_level_metrics,
        tags=top_level_tags,
        timestamp=report_time
    )]


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


def remove_type(d: dict, type_to_remove: Union[Type[str], Type[None]]):
    if isinstance(d, dict):
        for key in list(d.keys()):
            if type(key) is type(type_to_remove):  # Can't figure out a better NoneType
                del d[key]
            else:
                remove_type(d[key], type_to_remove)
