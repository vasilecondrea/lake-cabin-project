
import boto3
import botocore


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

    response = s3.get_object(Bucket=processed_bucket, Key=table_name)

    print(response)


# def

def upload_to_OLAP():
    pass
