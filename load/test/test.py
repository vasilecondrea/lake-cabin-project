from moto import mock_s3, mock_secretsmanager
import moto
import boto3
from unittest.mock import MagicMock
from unittest import mock
import pytest
import pandas as pd
import sqlalchemy
import testing.postgresql
from sqlalchemy import create_engine


from OLAP_load.script import lambda_handler, list_tables, load_table_from_name, upload_to_OLAP, get_db_credentials


def test_lambda_handler():
    pass


@mock_s3
def test_list_table_calls_the_object_v2_with_bucket_name():

    s3 = boto3.client("s3")
    bucket = "test_bucket"
    s3.list_objects_v2 = MagicMock()

    list_tables(s3, bucket)
    s3.list_objects_v2.assert_called_with(Bucket=bucket)


@mock_s3
def test_list_tables_returns_error_when_passed_invalid_args():
    s3 = boto3.client("s3")

    with pytest.raises(ValueError):
        list_tables(3, "valid_bucket_name")

    with pytest.raises(ValueError):
        list_tables(s3, 4)


# @mock_s3
# def test_list_tables_catches_boto3_errors():

#     valid_bucket = "valid_bucket"
#     invalid_bucket = "invalid_bucket"
#     s3 = boto3.client("s3")

#     s3.create_bucket(Bucket=valid_bucket)

#     with pytest.raises(ValueError):
#         list_tables(s3, invalid_bucket)


@mock_s3
def test_list_tables():

    file = "OLAP_load/test/test_parquet.parquet"
    bucket = "test_bucket"
    key = "test_parquet"

    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=bucket)
    s3.upload_file(Filename=file, Bucket=bucket, Key=key)

    result = list_tables(s3, bucket)

    assert result == ['test_parquet']


# @mock_s3
# def test_list_updated_table_ignores_unchanged_files():

#     file = "OLAP_load/test/test_parquet.parquet"
#     bucket = "test_bucket"
#     key = "test_parquet"

#     s3 = boto3.client("s3")
#     s3.create_bucket(Bucket=bucket)
#     s3.upload_file(Filename=file, Bucket=bucket, Key=key)

#     old_time_five_min = datetime.now() - timedelta(minutes=5)

#     moto.s3.models.s3_backends['123456789012']['global'].buckets[bucket].keys[key].last_modified = old_time_five_min

#     print(moto.s3.models.s3_backends['123456789012']['global'].buckets[bucket].keys[key].last_modified)

#     print(s3.list_objects(Bucket=bucket)['Contents'])

#     assert False

@mock_s3
def test_load_table_from_name_raises_ValueError_when_passed_invalid_args():
    with pytest.raises(ValueError):
        load_table_from_name(boto3.client("s3"), 4, 'table_name')

    with pytest.raises(ValueError):
        load_table_from_name(boto3.client("s3"), 'bucket_name', 3)

    with pytest.raises(ValueError):
        load_table_from_name(4, 'bucket_name', 'table_name')


# @mock_s3
# def test_load_from_name_calls_get_objects_with_correct_args():

#     s3 = boto3.client("s3")
#     bucket = "test_bucket"

#     key = "test_table"
#     s3.get_object = MagicMock()

#     load_table_from_name(s3, bucket, key)
#     s3.get_object.assert_called_with(Bucket=bucket, Key=key)


@mock_s3
@mock.patch('pandas.read_parquet')
def test_load_table_from_name_calls_pandas_read_parquet_with_bucket_name(read_parquet):

    s3 = boto3.client("s3")
    bucket = "test_bucket"
    file = "OLAP_load/test/test_parquet.parquet"
    key = "test_parquet"

    s3.create_bucket(Bucket=bucket)
    s3.upload_file(Filename=file, Bucket=bucket, Key=key)

    load_table_from_name(s3, bucket, key)
    read_parquet.assert_called_with(f's3://{bucket}/{key}')


@mock_s3
@mock.patch('pandas.read_parquet')
def test_load_table_from_name_returns_pandas_dataframe(read_parquet):
    s3 = boto3.client("s3")
    bucket = "test_bucket"
    file = "OLAP_load/test/test_parquet.parquet"
    key = "test_parquet"
    df = pd.read_parquet(file)

    s3.create_bucket(Bucket=bucket)
    s3.upload_file(Filename=file, Bucket=bucket, Key=key)
    response = load_table_from_name(s3, bucket, key)

    assert pd.DataFrame.equals(df, response)


@mock_secretsmanager
def test_get_db_credentials():
    with pytest.raises(ValueError):
        get_db_credentials("hello")


@mock_secretsmanager
def test_get_db_credentials_calls_get_secret_value_with_correct_args():
    sm = boto3.client('secretsmanager')
    sm.get_secret_value = MagicMock()

    sm.get_secret_value.return_value = '{"host": "changeme", "database": "changeme", "schema": "changeme", "port": "changeme", "username": "changeme", "password": "changeme"}'

    get_db_credentials(sm)

    sm.get_secret_value.assert_called_with('db-creds-destination')


@mock_secretsmanager
def test_get_db_credentials_returns_credentials_as_json():

    sm = boto3.client('secretsmanager')
    sm.get_secret_value = MagicMock()

    sm.get_secret_value.return_value = '{"host": "changeme", "database": "changeme", "schema": "changeme", "port": "changeme", "username": "changeme", "password": "changeme"}'

    output = get_db_credentials(sm)

    assert type(output) == dict


@mock_secretsmanager
def test_get_db_credentials_contains_relevant_keys():
    sm = boto3.client('secretsmanager')
    sm.get_secret_value = MagicMock()

    sm.get_secret_value.return_value = '{"host": "changeme", "database": "changeme", "schema": "changeme", "port": "changeme", "username": "changeme", "password": "changeme"}'

    output = get_db_credentials(sm)

    assert 'host' in output
    assert 'database' in output
    assert 'schema' in output
    assert 'port' in output
    assert 'username' in output
    assert 'password' in output


def test_upload_to_OLAP_raises_value_errors():
    db_credentials = {"host": "changeme", "database": "changeme", "schema": "changeme",
                      "port": "changeme", "username": "changeme", "password": "changeme"}

    with pytest.raises(ValueError):
        upload_to_OLAP('', '', '')
    with pytest.raises(ValueError):
        upload_to_OLAP(2, db_credentials, '')


@mock.patch('sqlalchemy.create_engine')
@mock.patch('pandas.DataFrame.to_sql')
def test_upload_to_OLAP_calls_createEngine_with_db_credentials(mock_create_engine, mock_to_sql):

    df = pd.DataFrame()
    db_credentials = {"host": "changeme", "database": "changeme", "schema": "changeme",
                      "port": "changeme", "username": "changeme", "password": "changeme"}
    db_url = f"postgresql+pg8000://{db_credentials['username']}:{db_credentials['password']}@{db_credentials['host']}:{db_credentials['port']}/{db_credentials['database']}"

    upload_to_OLAP(df, db_credentials, "")

    sqlalchemy.create_engine.assert_called_with(db_url)


@mock.patch('pandas.DataFrame.to_sql')
@mock.patch('sqlalchemy.engine.Engine.connect')
def test_upload_to_OLAP_call_with_correct_arguments(to_sql, connect):

    df = pd.read_parquet('OLAP_load/test/test_parquet.parquet')

    db_credentials = {"host": "changeme", "database": "changeme", "schema": "changeme",
                      "port": 5432, "username": "changeme", "password": "changeme"}

    table_name = "test_table"

    upload_to_OLAP(df, db_credentials, table_name)

    assert table_name in df.to_sql.call_args.args
