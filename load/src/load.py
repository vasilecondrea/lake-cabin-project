import boto3
import botocore
import pandas as pd
import json
import sqlalchemy
from sqlalchemy import create_engine


def lambda_handler(event, context):

    try:
        print('[LOADING] STARTED')
        s3 = boto3.client("s3")
        sm = boto3.client("secretsmanager")

        processed_bucket = event["processed_bucket"]
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

        print(f'[LOADING] COMPLETE -- tables_updated: {len(tables)}')

    except Exception as e:
        print(f'ERROR: Failed lambda_handler' + str(e))


def list_tables(s3, processed_bucket):
    try:
        if not isinstance(s3, botocore.client.BaseClient):
            raise (ValueError)

        if type(processed_bucket) != str:
            raise (ValueError)

        response = s3.list_objects_v2(Bucket=processed_bucket)
        tables = []

        if 'Contents' in response:
            tables = [table["Key"] for table in response["Contents"]]
        else:
            print(f"[LOADING] No data inside {processed_bucket}...")
        return tables
    except Exception as e:
        print("ERROR: Failed list_tables: " + str(e))


def load_table_from_name(s3, processed_bucket, table_name):
    try:
        if not isinstance(s3, botocore.client.BaseClient):
            raise (ValueError)

        if type(processed_bucket) != str:
            raise (ValueError)

        if type(table_name) != str:
            raise (ValueError)

        df = pd.read_parquet(f's3://{processed_bucket}/{table_name}')
        return df
    except Exception as e:
        print("ERROR: Failed load_table_from_name: " + str(e))


def get_db_credentials(secretsmanager):
    try:
        if not isinstance(secretsmanager, botocore.client.BaseClient):
            raise (ValueError)

        response = secretsmanager.get_secret_value(
            SecretId='db-creds-destination')

        creds_json = json.loads(response['SecretString'])
        print(creds_json)
        return creds_json
    except Exception as e:
        print("ERROR: Failed get_db_credentials: " + str(e))


def upload_to_OLAP(dataframe, db_credentials, table_name):
    try:
        if type(db_credentials) != dict or 'host' not in db_credentials or 'database' not in db_credentials or 'schema' not in db_credentials or 'port' not in db_credentials or 'username' not in db_credentials or 'password' not in db_credentials:
            raise (ValueError)

        if not isinstance(dataframe, pd.DataFrame):
            raise (ValueError)

        table = table_name.replace('.parquet', '')

        db_url = f"postgresql+pg8000://{db_credentials['username']}:{db_credentials['password']}@{db_credentials['host']}:{db_credentials['port']}/{db_credentials['database']}"

        engine = sqlalchemy.create_engine(db_url)
        conn = engine.connect()

        conn.execute(
            f"DELETE FROM {table}; GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO project_team_4;")

        dataframe.to_sql(table, conn, if_exists='append', index=False)

        print(f"[LOADING] Updated table '{table}'...")
    except Exception as e:
        print("ERROR: Failed upload_to_olap: " + str(e))


lambda_handler({"ingested_bucket": "ingestion-bucket-030125",
               "processed_bucket": "processed-bucket-030125"}, {})
