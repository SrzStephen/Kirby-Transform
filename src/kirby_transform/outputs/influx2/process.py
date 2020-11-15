from kirby_transform.processor import Processor
from influxdb_client import WritePrecision, InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import PointSettings
from rx.scheduler import ThreadPoolScheduler
from multiprocessing import cpu_count
from typing import List
from logging import getLogger
from operator import itemgetter
from datetime import datetime, timezone

logger = getLogger(__name__)


class InfluxAPI(Processor):
    def check_bucket_exists(self, bucket_name: str) -> bool:
        self.client: InfluxDBClient  # type hinting for autocomplete
        return self.client.buckets_api().find_bucket_by_name(bucket_name=bucket_name)

    def __init__(self, url: str, token: str, org: str, data_bucket: str, meta_bucket: str,
                 workers: int = cpu_count()):
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
        self.points = []
        self.api = self.client.write_api(write_options=WriteOptions(batch_size=200,
                                                                    flush_interval=2000,
                                                                    jitter_interval=100,
                                                                    retry_interval=2000,
                                                                    write_scheduler=ThreadPoolScheduler(
                                                                        max_workers=workers)))
        self.banned_types = [type(None)]

    def process_report(self, report) -> None:
        self.process_report(report)

    def generate_output(self, data: List[dict]):
        self.points = []
        for tags, fields, timestamp in map(itemgetter('tags', 'fields', 'timestamp'), data):
            collector = tags['collector']
            # Every measurement goes against what collected it
            p = Point.measurement(collector)
            # which makes the collector tag not needed, remove to reduce dimensionality
            [p.tag(key, value) for key, value in tags.items() if
             key != 'collector' and not isinstance(value, type(None))]
            [p.field(key, value) for key, value in fields.items() if not isinstance(value, type(None))]
            p.time(datetime.fromtimestamp(timestamp, tz=timezone.utc), write_precision=WritePrecision.S)
            self.points.append(p)
        return self

    def send(self, report: List[dict], bucket: str) -> bool:
        self.generate_output(report)
        if len(self.points) > 0:
            self.api.write(bucket=bucket, record=self.points, org=self.org)
            return True
        return False

    def send_all(self) -> bool:
        self.generate_output(self.data)
        data_points = self.points.copy()
        self.generate_output(self.meta_data)
        meta_points = self.points.copy()
        if len(data_points) > 0 and len(meta_points) > 0:
            logger.debug(f"Writing {len(data_points)} to {self.data_bucket} at {self.url}")
            self.api.write(bucket=self.data_bucket, record=data_points)
            logger.debug(f"Writing {len(meta_points)} to {self.meta_bucket} at {self.url}")
            self.api.write(bucket=self.meta_bucket, record=meta_points)
            return True
        logger.debug(f"One of meta reports, len:{len(meta_points)} data reports len:{len(data_points)} was 0")
        return False
