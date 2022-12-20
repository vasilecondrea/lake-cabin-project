
import boto3
import botocore
import pandas as pd
import json


# s3 = boto3.client("s3")


def lambda_handler(event, context):
    pass


def list_tables(s3, processed_bucket):

    if not isinstance(s3, botocore.client.BaseClient):
        raise (ValueError)

    if type(processed_bucket) != str:
        raise (ValueError)

    response = s3.list_objects_v2(Bucket=processed_bucket)

    tables = [table["Key"] for table in response["Contents"]]
    return tables


def load_table_from_name(s3, processed_bucket, table_name):

    if not isinstance(s3, botocore.client.BaseClient):
        raise (ValueError)

    if type(processed_bucket) != str:
        raise (ValueError)

    if type(table_name) != str:
        raise (ValueError)

    df = pd.read_parquet(f's3://{processed_bucket}/{table_name}')

    return df


def get_db_credentials(secretsmanager):
    if not isinstance(secretsmanager, botocore.client.BaseClient):
        raise (ValueError)

    response = secretsmanager.get_secret_value('db-creds-destination')

    creds_json = json.loads(response)

    return creds_json


def upload_to_OLAP(rds, dataframe, db_credentials):

    if type(db_credentials) != dict:
        raise (ValueError)
    if not isinstance(dataframe, pd.DataFrame):
        raise (ValueError)
    if not isinstance(rds, botocore.client.BaseClient):
        raise (ValueError)
