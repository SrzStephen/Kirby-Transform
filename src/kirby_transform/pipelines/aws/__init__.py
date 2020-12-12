from kirby_transform import Processor, ValidationError
from kirby_transform.pipelines.aws.env_vars import UNKNOWN_ERROR_SQS, VALIDATION_FAILED_SQS
from typing import Optional
from aws_lambda_context import LambdaContext
from mypy_boto3_sqs.client import SQSClient
from mypy_boto3_sqs.type_defs import MessageAttributeValueTypeDef as SQSAttribute
from boto3 import client
from json import dumps
from logging import getLogger

logger = getLogger(__name__)


class LambdaHelpers:
    def __init__(self, event: dict, context: LambdaContext):
        self.context = context
        self.event = event

    def write_message_to_sqs(self, queue_name: str, region_name: str = 'us-east-1') -> None:
        attributes = dict(
            function_name=SQSAttribute(DataType="String", StringValue=self.context.function_name),
            function_version=SQSAttribute(DataType="String", StringValue=self.context.function_version)
        )
        sqs_client: SQSClient = client('sqs',region_name=region_name)
        queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
        sqs_client.send_message(QueueUrl=queue_url, MessageBody=dumps(self.event), MessageAttributes=attributes)
        logger.info(f"Wrote failure to {queue_name}")

    def event_with_metadata(self) -> dict:
        event = self.event.copy()
        data_to_add = dict(
            processor_version=Processor.get_version(),
            lambda_version=self.context.function_version,
            function_name=self.context.function_name
        )
        if self.event.get('meta_tags', False):
            event['meta_tags'] = data_to_add
        else:
            for k, v in data_to_add.items():
                event['meta_tags'] = dict()
                event['meta_tags'][k] = v
        return event

    def parse_mqtt(self) -> Optional[dict]:
        """Base parser that runs deals with the AWS side of things"""
        logger.debug(msg=f"Got context \n {self.context} \n Event \n {self.event}")
        try:
            Processor().process(data=self.event)
        except ValidationError as e:
            logger.info(f"failed to parse message {self.event} \n from {self.context}")
            self.write_message_to_sqs(queue_name=VALIDATION_FAILED_SQS())
            raise

        except Exception as e:
            logger.info(f"Programming error detected in Processor")
            self.write_message_to_sqs(queue_name=UNKNOWN_ERROR_SQS())
            raise
        return self.event_with_metadata()
