from importlib.machinery import SourceFileLoader
from os import environ
from pathlib import Path
from random import randint
from time import sleep
from unittest import TestCase

import boto3
from moto import mock_sqs
from mypy_boto3_sqs.client import SQSClient

from kirby_transform import Processor, ValidationError
from kirby_transform.outputs import InfluxAPI, TimestreamPush
from kirby_transform.pipelines.aws import LambdaHelpers
from kirby_transform.pipelines.aws.env_vars import (UNKNOWN_ERROR_SQS,
                                                    VALIDATION_FAILED_SQS)
from kirby_transform.test import get_sucessful_files

data_dir = Path(__file__).parent.parent.absolute() / 'data'
base_lambda_path = Path(__file__).parent.parent.parent / "lambda" / "src"

# Import tests from Lambdas file
# Required because they're not part of any module, they're just python files that get invoked.
influx2_test = SourceFileLoader(fullname='test_fixtures_influx2',
                                path=str(data_dir.parent / "test_influx2" / "test_influx2.py")).load_module()
InfluxIntegration = influx2_test.ContainerHelpers

timestream_test = SourceFileLoader(fullname='test_fixtures_timestream',
                                   path=str(data_dir.parent / "test_timestream" / "test_timestream.py")).load_module()
TimestreamIntegration = timestream_test.TimestreamTest

region = environ.get("AWS_DEFAULT_REGION", "us-east-1")


class FakeContext:
    def __init__(self):
        self.function_name = "foo"
        self.function_version = "1.0.0"


class TestLambdaHelper(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sqs: SQSClient = boto3.resource('sqs', region_name=region)

    @mock_sqs
    def test_write(self):
        self.sqs.create_queue(QueueName="test")  # for testing purposes create a fake queue
        self.sqs.create_queue(QueueName="test")
        LambdaHelpers(dict(), FakeContext()).write_message_to_sqs(queue_name="test")

    @mock_sqs
    def test_pipeline(self):
        self.sqs.create_queue(QueueName="test")  # for testing purposes create a fake queue
        for filename, data in list(get_sucessful_files(data_dir)):
            enriched_event = LambdaHelpers(data, FakeContext()).parse_mqtt()
            self.assertIsNotNone(Processor().process(enriched_event))

    @mock_sqs
    def test_failure(self):
        self.sqs.create_queue(QueueName=VALIDATION_FAILED_SQS())
        self.sqs.create_queue(QueueName=UNKNOWN_ERROR_SQS())  # for testing purposes create a fake queue
        with self.assertRaises(ValidationError):
            LambdaHelpers(dict(), FakeContext()).parse_mqtt()


class TestInflux(InfluxIntegration, TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(TestInflux, cls).start_container()
        cls.influx_path = base_lambda_path / "influx2.py"
        # set environment variables before loading in the lambda module
        environ['INFLUX_URL'] = cls.influx_ci_config['url']
        environ['INFLUX_TOKEN'] = cls.influx_ci_config['token']
        environ['INFLUX_ORG'] = cls.influx_ci_config['org']
        environ['INFLUX_DATA_BUCKET'] = cls.influx_ci_config['data_bucket']
        environ['INFLUX_META_BUCKET'] = cls.influx_ci_config['meta_bucket']
        try:
            cls.influx_module = SourceFileLoader(fullname='influx_lambda',
                                                 path=str(cls.influx_path.absolute())).load_module()
            cls.influx_lambda = cls.influx_module.TestHelper
            cls.influx_api: InfluxAPI = cls.influx_lambda.get_influx_instance()
        except Exception:
            print("SERIOUS FAILURE. Couldn't load Lambda into test suite")
            raise

    def test_file_exists(self):
        self.assertTrue(self.influx_path.exists())
        self.assertTrue(self.influx_path.is_file())

    def test_lambda(self):
        passed = False
        # function name tag gets added based on whatever is in the context object (FakeContext)
        query = f"""
        from(bucket: "{environ['INFLUX_DATA_BUCKET']}")
          |> range(start: -100y)
          |> filter(fn: (r) => r["function_name"] == "foo")
          |> yield(name: "mean")
  """
        for filename, data in list(get_sucessful_files(data_dir)):
            self.influx_lambda(data, FakeContext())

        for _ in range(0, 100):  # 5s
            sleep(0.05)  # Influx isn't strongly read write consistent, it takes a while
            # (seconds) after writing the data before it appears
            results = self.influx_api.client.query_api().query(query=query, org=environ['INFLUX_ORG'])
            if len(results) > 0:
                passed = True
                break
        self.assertTrue(passed, msg="The influx query failed to find data tagged with the lambda")

    @mock_sqs
    def test_lambda_fails(self):
        sqs: SQSClient = boto3.resource('sqs', region_name=region)
        sqs.create_queue(QueueName=VALIDATION_FAILED_SQS())
        sqs.create_queue(QueueName=UNKNOWN_ERROR_SQS())
        with self.assertRaises(ValidationError):
            self.influx_lambda(event=dict(), context=FakeContext())


class TestTimestream(TimestreamIntegration, TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(TestTimestream, cls).setup_timestream()  # Add some pre init test code
        cls.timestream_path = base_lambda_path / "timestream.py"
        # Not secret
        environ['TIMESTREAM_META_TABLE'] = "testtable"
        environ['TIMESTREAM_DATA_TABLE'] = "testtable"
        environ['TIMESTREAM_DATABASE'] = "testdb"
        environ['AWS_TIMESTREAM_REGION'] = 'us-east-1'

        cls.timestream_module = SourceFileLoader(fullname='timestream_lambda',
                                                 path=str(cls.timestream_path.absolute())).load_module()
        cls.timestream_lambda = cls.timestream_module.TestHelper
        cls.timestream: TimestreamPush = cls.timestream_lambda.get_timestream_instance()

    def test_lambda(self):
        context = FakeContext()
        context.function_name = f"foo{randint(0, 9999)}"
        for filename, data in list(get_sucessful_files(data_dir)):
            self.timestream_lambda(event=data, context=context)
        results = self.timestream.read_client.query(
            QueryString=f"""
        SELECT * FROM "testdb"."testtable" WHERE function_name = '{context.function_name}' ORDER BY time DESC LIMIT 1 
                        """)
        self.assertTrue(len(results['Rows']) == 1)

    @mock_sqs
    def test_lambda_fails(self):
        sqs: SQSClient = boto3.resource('sqs', region_name=region)
        sqs.create_queue(QueueName=VALIDATION_FAILED_SQS())
        sqs.create_queue(QueueName=UNKNOWN_ERROR_SQS())
        with self.assertRaises(ValidationError):
            self.timestream_lambda(event=dict(), context=FakeContext())
