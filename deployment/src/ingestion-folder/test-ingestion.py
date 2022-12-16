import logging
import boto3

logger = logging.getLogger("lambdaLogger")
logger.setLevel = logging.info


def ingestion_handler(event, context):
    logger.info("testing the ingestion function for deployment")
