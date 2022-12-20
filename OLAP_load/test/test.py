from moto import mock_s3
import moto
import boto3
from datetime import datetime, timedelta

from OLAP_load.script import lambda_handler, list_tables, load_parquet_file, upload_to_OLAP

# from src.script import list_updated_tables


def test_lambda_handler():
    pass


@mock_s3
def test_list_tables():

    file = "OLAP_load/test/test_parquet.parquet"
    bucket = "test_bucket"
    key = "test_parquet"

    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=bucket)
    s3.upload_file(Filename=file, Bucket=bucket, Key=key)

    result=0# = list_updated_tables(bucket)

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
