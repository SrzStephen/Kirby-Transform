from datetime import datetime
from operator import itemgetter
from pathlib import Path
from time import sleep, time
from unittest import TestCase

import docker
import requests
from influxdb_client import Point, WritePrecision

from kirby_transform.outputs import InfluxAPI
from kirby_transform.test import get_sucessful_files

data_dir = Path(__file__).parent.parent.absolute() / 'data'
CONTAINER_TO_RUN = "quay.io/influxdb/influxdb:v2.0.1"
TIME_TO_WAIT_FOR_CONTAINER_RESPONSE = 180
INFLUX_CI_CONFIG = dict(
    b="data_bucket",
    o="org",
    u="someUser",
    p="somecipass",
    t="sometoken"
)
config_string = "influx setup"
for key, value in INFLUX_CI_CONFIG.items():
    config_string += f" -{key} {value}"
config_string += " --force"

# TODO make this class variables
INFLUX_API_CONFIG = dict(
    url="http://127.0.0.1:8086",
    token=INFLUX_CI_CONFIG['t'],
    org=INFLUX_CI_CONFIG['o'],
    data_bucket=INFLUX_CI_CONFIG['b'],
    meta_bucket=INFLUX_CI_CONFIG['b']
)


class ContainerHelpers(object):
    @classmethod
    def run_container(cls, docker_client: docker.DockerClient, container_name: str, timeout: int):
        image = cls.client.images.pull(container_name)
        port = {'8086/tcp': ('127.0.0.1', 8086)}
        for container in docker_client.containers.list():
            if any(container_name in x for x in container.image.tags):
                container.stop()
                print(f"Stopping running influx container")
                sleep(5)
            elif any('8086' in x for x in docker_client.containers.list()[0].ports):
                raise OSError(f"Container {container.image} is already running with ports {container.ports}, "
                              f"I need 8086")

        running_container = docker_client.containers.run(image=container_name, ports=port, detach=True)
        start_time = time()
        config_has_been_run = False
        while (time() - start_time) < timeout and not config_has_been_run:
            # check that port is responding before trying to exec into container and running config execution
            try:
                req = requests.get('http://127.0.0.1:8086')
                if req.status_code == 200:
                    if "influxdb" not in req.text.lower():
                        raise ValueError(f"Something else seems to be running on port 8086, got {req.content}")
                    print(f"Setting up influx with {config_string}")
                    print(running_container.exec_run(config_string)[1])
                    config_has_been_run = True
            except Exception:
                # Don't care about http errors
                pass
        return running_container
    @classmethod
    def tear_down_container(cls):
        try:
            if cls.running_container is not None:
                print(f"Tearing down container {cls.running_container.image}")
                cls.running_container.stop()
                cls.client.close()
            else:
                print("Influx container not running")
        except AttributeError:
            pass

    @classmethod
    def start_container(cls) -> None:
        try:
            cls.client = docker.from_env()
            cls.running_container = cls.run_container(cls.client, CONTAINER_TO_RUN,
                                                        timeout=TIME_TO_WAIT_FOR_CONTAINER_RESPONSE)
            cls.influx_ci_config = INFLUX_API_CONFIG
        except Exception:
            if cls.running_container is not None:
                print(f"Tearing down container {cls.running_container.image}")
                cls.running_container.stop()
                cls.client.close()
            raise




class IntegrationTest(TestCase, ContainerHelpers):

    @classmethod
    def setUpClass(cls) -> None:
        super(IntegrationTest, cls).start_container()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tear_down_container()

    def setUp(self) -> None:
        # because InfluxClient can be mutated, reset it every time we run a test
        self.InfluxClient = InfluxAPI(**INFLUX_API_CONFIG)
        self.bucket = INFLUX_CI_CONFIG['b']

    def test_basic_write(self):
        """Basically from docs"""
        _point1 = Point("test_measure").tag("sometag", "sometagvalue") \
            .field("somefield", 25.3) \
            .time(datetime.utcnow(), write_precision=WritePrecision.S)
        # This is also a pretty good test for "Did I get timezones right"
        self.InfluxClient.api.write(bucket=self.bucket, record=[_point1])
        query_string = f'from(bucket:"{self.bucket}")\
        |> range(start: -10m)\
        |> filter(fn:(r) => r._measurement == "test_measure")\
        |> filter(fn: (r) => r.sometag == "sometagvalue")\
        |> filter(fn:(r) => r._field == "somefield" )'
        query_api = self.InfluxClient.client.query_api()
        start_time = time()
        query_result = list
        while time() - start_time < 10:
            sleep(1)

            query_result = query_api.query(query=query_string, org=INFLUX_CI_CONFIG['o'])
            if len(query_result) != 0:
                break

        self.assertEqual(len(query_result), 1)
        self.assertEqual(query_result[0].records[0].values['_value'], 25.3)

    def test_bucket_exists(self) -> None:
        "Also a good sanity check for contaienr running"
        self.assertTrue(self.InfluxClient.check_bucket_exists(bucket_name=INFLUX_CI_CONFIG['b']))

    def test_data_generation(self):
        for file, data in get_sucessful_files(data_dir):
            proc_data = self.InfluxClient.process(data)
            data = self.InfluxClient._generate_data(proc_data.data)
            self.assertGreaterEqual(len(data), 1, msg=f"File {file} failed")
            for item in data:
                self.assertIsInstance(item, Point)

    def test_send_single(self):
        fields = dict(single_write_test=1)
        tags = dict(collector="test_influx_collector",
                    some_tag="tag2")

        self.assertTrue(self.InfluxClient.send_data(data=[dict(tags=tags, fields=fields, timestamp=time())],
                                                    bucket=self.InfluxClient.data_bucket))
        query_api = self.InfluxClient.client.query_api()
        bucket = INFLUX_CI_CONFIG['b']
        query_string = f'from(bucket:"{bucket}")|> range(start: -10m)\
        |> filter(fn:(r) => r._measurement == "test_influx_collector")'
        start_time = time()
        query_result = list
        while time() - start_time < 10:
            sleep(0.01)
            query_result = query_api.query(query=query_string, org=INFLUX_CI_CONFIG['o'])
            if len(query_result) != 0:
                break
        self.assertEqual(len(query_result), 1)

    def test_write(self) -> None:
        for file, data in get_sucessful_files(data_dir):
            prod_data = self.InfluxClient.process(data)
            self.InfluxClient.send(prod_data)
            query_api = self.InfluxClient.client.query_api()
            bucket = INFLUX_CI_CONFIG['b']
            collector = data['collector']
            query_string = f'from(bucket:"{bucket}")|> range(start: -100y)|> filter(fn:(r) => r._measurement == "{collector}")'
            start_time = time()
            query_result = 0
            while time() - start_time < 10:
                sleep(0.01)
                query_result = query_api.query(query=query_string, org=INFLUX_CI_CONFIG['o'])
                if len(query_result) != 0:
                    break
            self.assertNotEqual(len(query_result), 0)
            records = [x.records[0].values for x in query_result]
            fields = list(map(itemgetter('_field'), records))
            self.assertIn("meta_total_tags", fields)  # from data_level
            self.assertIn("total_reports", fields)  # from report_level
