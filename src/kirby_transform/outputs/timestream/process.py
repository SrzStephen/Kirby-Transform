from boto3 import client, Session
from botocore.config import Config
from kirby_transform.processor import Processor, ProcessedData
from knobs import Knob
from typing import Optional, List, Any
from mypy_boto3_timestream_query.client import TimestreamQueryClient
from mypy_boto3_timestream_write.client import TimestreamWriteClient
from operator import itemgetter


class TimestreamPush(Processor):
    def __init__(self, boto_session: Session, meta_table: str, data_table: str, database: str, region='us-east-1'):
        super(TimestreamPush, self).__init__()
        # AWS keys should be passed in by environment variables
        if not region:
            self.region = boto_session.region_name
        else:
            self.region = region
        self.session = boto_session
        self.database = database
        self.meta_table = meta_table
        self.data_table = data_table
        self.write_client: TimestreamWriteClient = self.session.client(service_name='timestream-write',
                                                                       config=Config(read_timeout=10,
                                                                                     max_pool_connections=100,
                                                                                     retries={'max_attempts': 5}))
        self.read_client: TimestreamQueryClient = self.session.client(service_name='timestream-query')

    def process(self, data: dict) -> Optional[ProcessedData]:
        processed = self._process(data)
        processed.discard_strings()
        return processed

    @staticmethod
    def __generate_data(data: List[dict]) -> Any:
        records = []
        for tags, fields, timestamp in map(itemgetter('tags', 'fields', 'timestamp'), data):
            for field_key, field_value in fields.items():
                records.append(dict(
                    Dimensions=[dict(Name=str(k), Value=str(TimestreamPush.null_to_zero(v))) for k, v in tags.items()],
                    MeasureName=str(field_key),
                    MeasureValue=str(TimestreamPush.null_to_zero(field_value)),
                    Time=str(round(timestamp * 1000))))  # Time needs to be in milis
        return records

    @staticmethod
    def null_to_zero(value: Any):
        return 0 if value is None else value

    def send(self, data: ProcessedData) -> bool:
        dat = self.__generate_data(data.data)
        meta_data = self.__generate_data(data.all_meta_data)
        if len(dat) > 0:
            self.write_client.write_records(DatabaseName=self.database, TableName=self.data_table,
                                            Records=dat)
        if len(meta_data) > 0:
            self.write_client.write_records(DatabaseName=self.database, TableName=self.meta_table,
                                            Records=meta_data)
        return True

    def send_data(self, data: List[dict], **kwargs) -> Optional[bool]:
        if not kwargs.get('table_name'):
            raise KeyError("Missing table_name key")
        if len(self.__generate_data(data)) > 0:
            self.write_client.write_records(DatabaseName=self.database, TableName=kwargs['table_name'],
                                        Records=self.__generate_data(data))
        return True
