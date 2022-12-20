from moto import mock_s3
import moto
import boto3
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import pytest


from OLAP_load.script import lambda_handler, list_tables, load_table_from_name, upload_to_OLAP


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


@mock_s3
def test_load_from_name_calls_get_objects_with_correct_args():

    s3 = boto3.client("s3")
    bucket = "test_bucket"

    key = "test_table"
    s3.get_object = MagicMock()

    load_table_from_name(s3, bucket, key)
    s3.get_object.assert_called_with(Bucket=bucket, Key=key)
