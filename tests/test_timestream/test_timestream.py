from kirby_transform.outputs import TimestreamPush
from kirby_transform.test import get_sucessful_files
from unittest import TestCase
from knobs import Knob
from boto3.session import Session
from time import time, mktime
from datetime import datetime, timezone, timedelta, tzinfo
import pytz
from pathlib import Path

data_dir = Path(__file__).parent.parent.absolute() / 'data'


def get_current_timezone() -> tzinfo:
    return datetime.now(timezone(timedelta(0))).astimezone().tzinfo


class TestIntegration(TestCase):
    def setUp(self) -> None:
        fields = dict(single_write_test=1)
        tags = dict(collector="test_timestream",
                    some_tag="tag2")
        self.dummy_payload = [dict(tags=tags, fields=fields, timestamp=time())]
        self.AWS_Session = Session(region_name='us-east-1')
        self.client = TimestreamPush(boto_session=self.AWS_Session, meta_table='testtable', data_table='testtable',
                                     database='testdb')
        self.test_query = """
            SELECT time FROM "testdb"."testtable"
            where measure_name = 'single_write_test'
            ORDER BY time DESC LIMIT 1 
        """

    def test_stuff_exists(self):
        try:
            self.client.write_client.describe_database(DatabaseName=self.client.database)
        except Exception as e:
            self.fail(msg=f"Didn't find database {self.client.database} got error {e}")
        try:
            self.client.write_client.describe_table(DatabaseName=self.client.database, TableName=self.client.data_table)
            self.client.write_client.describe_table(DatabaseName=self.client.database, TableName=self.client.meta_table)
        except Exception as e:
            self.fail(
                f"Failed to find one of table {self.client.meta_table}, {self.client.data_table} in database {self.client.database} with error {e}")

    def test_data_generation(self):
        # write some data
        self.client.send_data(self.dummy_payload, table_name=self.client.data_table)
        # Read it back, check the timestamp to see that it's the same
        test_query = self.client.read_client.query(QueryString=self.test_query)
        self.assertEqual(len(test_query['Rows']), 1, msg=f"Didn't return enough data from {test_query}")
        dt = datetime.strptime(test_query['Rows'][0]['Data'][0]['ScalarValue'][:-3], '%Y-%m-%d %H:%M:%S.%f')
        dt: datetime = pytz.timezone('UTC').localize(dt, is_dst=True)  # Localise to UTC
        self.assertEqual(round(dt.timestamp(), 0), round(self.dummy_payload[0]['timestamp'], 0))
        pass

    def test_basic_write(self):
        for file, data in get_sucessful_files(data_dir):
            processed_data = self.client.process(data)
            try:
                self.client.send_data(processed_data.all_meta_data, table_name=self.client.data_table)
                self.client.send_data(processed_data.data, table_name=self.client.data_table)
            except:
                raise

    def test_behaviour_only_string(self):
        # This is a case where it's failing
        failing_file = [data for file, data in get_sucessful_files(data_dir) if 'all_strings' in file.name][0]
        processed_data = self.client.process(failing_file)
        self.client.send_data(processed_data.data, table_name=self.client.data_table)

    def test_full(self):
        test_data = [data for file, data in get_sucessful_files(data_dir)]
        self.client.send(self.client.process(test_data[0]))
        pass
