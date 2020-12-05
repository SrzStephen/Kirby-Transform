from kirby_transform.processor import Processor
from kirby_transform import ProcessedData
from typing import Optional
from influxdb_client import WritePrecision, InfluxDBClient, Point, WriteOptions
from rx.scheduler import ThreadPoolScheduler
from multiprocessing import cpu_count
from typing import List
from logging import getLogger
from operator import itemgetter
from datetime import datetime, timezone

logger = getLogger(__name__)


class InfluxAPI(Processor):
    def __init__(self, url: str, token: str, org: str, data_bucket: str, meta_bucket: str,
                 workers: int = cpu_count()):
        super().__init__()
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.url = url
        self.token = token
        self.org = org

        if not self.check_bucket_exists(data_bucket):
            raise KeyError(f"Data bucket {data_bucket} as does not exist")
        if not self.check_bucket_exists(meta_bucket):
            raise KeyError(f"Meta bucket {meta_bucket} as does not exist")

        self.data_bucket = data_bucket
        self.meta_bucket = meta_bucket

        # write with batch api with sane looking defaults
        self.api = self.client.write_api(write_options=WriteOptions(batch_size=200,
                                                                    flush_interval=2000,
                                                                    jitter_interval=100,
                                                                    retry_interval=2000,
                                                                    write_scheduler=ThreadPoolScheduler(
                                                                        max_workers=workers)))

    def check_bucket_exists(self, bucket_name: str) -> bool:
        return self.client.buckets_api().find_bucket_by_name(bucket_name=bucket_name)

    @staticmethod
    def _generate_data(data: List[dict]) -> List[Point]:
        points = []
        for tags, fields, timestamp in map(itemgetter('tags', 'fields', 'timestamp'), data):
            collector = tags['collector']
            # Every measurement goes against what collected it
            p = Point.measurement(collector)
            # which makes the collector tag not needed, remove to reduce dimensionality
            [p.tag(key, value) for key, value in tags.items() if
             key != 'collector' and not isinstance(value, type(None))]
            [p.field(key, value) for key, value in fields.items() if not isinstance(value, type(None))]
            p.time(datetime.fromtimestamp(timestamp, tz=timezone.utc), write_precision=WritePrecision.S)
            points.append(p)
        return points

    def process(self, data: dict) -> Optional[ProcessedData]:
        p = self._process(data)
        p.discard_strings()
        return p

    def send_data(self, data: List[dict], **kwargs) -> bool:
        """Sending specific data. Assumes its in the common format"""
        if not kwargs.get('bucket', None):
            raise KeyError("Expected to have bucket name passed in")
        self.api.write(bucket=kwargs['bucket'], record=self._generate_data(data))
        return True

    def send(self, data: ProcessedData) -> bool:
        self.api.write(bucket=self.data_bucket, record=self._generate_data(data.data))
        self.api.write(bucket=self.data_bucket, record=self._generate_data(data.all_meta_data))
        return True
