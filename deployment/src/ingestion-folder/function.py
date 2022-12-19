import logging
import boto3

logger = logging.getLogger("lambdaLogger")
logger.setLevel = logging.info


def lambda_handler(event, context):
    print(event)
