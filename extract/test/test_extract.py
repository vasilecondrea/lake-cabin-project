import boto3
import moto
import unittest

class TestLambdaHandler(unittest.TestCase):
    @moto.mock_s3
    @moto.mock_cloudwatch
    def test_lambda_handler(self):
        # Set up the mock S3 and CloudWatch clients
        s3 = boto3.client("s3")
        cloudwatch = boto3.client("cloudwatch")

        # Set up the mock event and context objects
        event = {}
        context = {}

        # Call the lambda_handler function
        lambda_handler(event, context)

        # Verify that the S3 buckets were created
        self.assertTrue(s3.list_buckets()['Buckets'])
        self.assertIn('ingested-data-bucket-1', [b['Name'] for b in s3.list_buckets()['Buckets']])
        self.assertIn('processed-data-bucket-1', [b['Name'] for b in s3.list_buckets()['Buckets']])

        # Verify that the CloudWatch metrics were logged
        metrics = cloudwatch.list_metrics()['Metrics']
        self.assertIn('IngestionStartTime', [m['MetricName'] for m in metrics])
        self.assertIn('IngestionEndTime', [m['MetricName'] for m in metrics])

        # Verify that the data was ingested to S3
        s3_objects = s3.list_objects(Bucket='ingested-data-bucket-1')['Contents']
        self.assertTrue(s3_objects)
        self.assertEqual(len(s3_objects), 11)  # Number of tables in the database

if __name__ == '__main__':
    unittest.main()
