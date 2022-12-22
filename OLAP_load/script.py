import boto3
import botocore
import pandas as pd
import json
import sqlalchemy
from sqlalchemy import create_engine


def lambda_handler(event, context):
    s3 = boto3.client("s3")
    sm = boto3.client("secretsmanager")

    processed_bucket = event["processed_table"]
    db_creds = get_db_credentials(sm)
    tables = list_tables(s3, processed_bucket)
    dims = [dim for dim in tables if 'dim' in dim]
    facts = [fact for fact in tables if "fact" in fact]

    for dim_table in dims:
        df = load_table_from_name(s3, processed_bucket, dim_table)
        upload_to_OLAP(df, db_creds, dim_table)

    for fact_table in facts:
        df = load_table_from_name(s3, processed_bucket, fact_table)
        upload_to_OLAP(df, db_creds, fact_table)


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


def upload_to_OLAP(dataframe, db_credentials, table_name):

    if type(db_credentials) != dict or 'host' not in db_credentials or 'database' not in db_credentials or 'schema' not in db_credentials or 'port' not in db_credentials or 'username' not in db_credentials or 'password' not in db_credentials:
        raise (ValueError)

    if not isinstance(dataframe, pd.DataFrame):
        raise (ValueError)

    db_url = f"postgresql+pg8000://{db_credentials['username']}:{db_credentials['password']}@{db_credentials['host']}:{db_credentials['port']}/{db_credentials['database']}"

    engine = sqlalchemy.create_engine(db_url)
    conn = engine.connect()
    dataframe.to_sql(table_name, conn)
