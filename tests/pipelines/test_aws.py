from kirby_transform.pipelines.aws import LambdaHelpers
from kirby_transform.test import get_sucessful_files
from unittest import TestCase
from moto import mock_sqs
from mypy_boto3_sqs.client import SQSClient
import boto3
from os import environ
from pathlib import Path
from kirby_transform import Processor
from importlib.machinery import SourceFileLoader
from ..test_influx2.test_influx2 import IntegrationTest
from time import sleep

data_dir = Path(__file__).parent.parent.absolute() / 'data'
from kirby_transform.outputs import InfluxAPI


class FakeContext:
    def __init__(self):
        self.function_name = "foo"
        self.function_version = "1.0.0"


class TestLambdaHelper(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        region = environ.get("AWS_DEFAULT_REGION", "us-east-1")
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


class TestInflux(IntegrationTest):
    @classmethod
    def setUpClass(cls) -> None:
        # It'll rerun the tests but I need the classmethod from IntegrationTest to be init'd
        # Todo multi class inheretence with the test_influx2 so that I dont need to do this.
        super(TestInflux, cls).setUpClass()
        cls.influx_path = Path(__file__).parent.parent.parent / "lambda" / "src" / "influx2.py"
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

        for _ in range(0, 50):  # 2.5s
            sleep(0.05)
            results = self.influx_api.client.query_api().query(query=query, org=environ['INFLUX_ORG'])
            if len(results) > 0:
                passed = True
                break
        self.assertTrue(passed, msg="The influx query failed to find data tagged with the lambda")
