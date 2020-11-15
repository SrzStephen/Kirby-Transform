from ..baseclass import BaseOutputClass
class TimeStream(BaseOutputClass):
    def __init__(self, report: dict, url: str, token: str, org: str, bucket: str,workers:int=4):
        super().__init__(report)
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = InfluxDBClient(url=url, token=token, org=org)
        # write with batch api with sane looking defaults
        self.api = self.client.write_api(write_options=WriteOptions(batch_size=200,
                                                                    flush_interval=2000,
                                                                    jitter_interval=100,
                                                                    retry_interval=2000,
                                                                    write_scheduler=ThreadPoolScheduler(workers=4)))
        self.points = []

    def generate_output(self):
        def trim_text_fields(self)
        self.points = []
        for item in self.processed_report['data']:
            measurement = item['tags']['source']
            item['tags'].pop('source')
            value_dict = item['fields']
            p = Point.measurement(measurement)
            for k, v in item['tags'].items():
                p.tag(key=k, value=v)
            for k, v in value_dict.items():
                p.field(field=k, value=v)
            p.time(item['timestamp'], write_precision=WritePrecision.S)
            self.points.append(p)

    def send(self):
        if len(self.points) > 0:
            self.api.write(bucket=self.bucket, record=self.points)
