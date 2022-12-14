import moto
import boto3

# Test that the two S3 buckets are created correctly
@moto.mock_s3
def test_create_buckets():
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket='ingested-data-bucket-1')
    s3.create_bucket(Bucket='processed-data-bucket-1')

    # Verify that the buckets exist
    response = s3.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response['Buckets']]
    assert 'ingested-data-bucket-1' in bucket_names
    assert 'processed-data-bucket-1' in bucket_names
