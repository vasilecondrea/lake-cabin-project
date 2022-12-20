import boto3
import moto
import unittest
from moto import mock_s3
from unittest import TestCase
from src.python_ingestion_script import create_s3_buckets
from src.python_ingestion_script import ingest_database_to_s3


@mock_s3
class TestCreateS3BucketsAndIngestDatabaseToS3(TestCase):
    def test_create_s3_buckets(self):
        create_s3_buckets()

        # Verify that the two S3 buckets were created
        s3 = boto3.client("s3")
        buckets = s3.list_buckets()["Buckets"]
        bucket_names = [bucket["Name"] for bucket in buckets]
        self.assertIn("ingested-data-bucket-1", bucket_names)
        self.assertIn("processed-data-bucket-1", bucket_names)

    def test_ingest_database_to_s3(self):
        # Connect to the mock PostgreSQL database
        conn = pg8000.connect(
            host="nc-data-eng-totesys-production.chpsczt8h1nu.eu-west-2.rds.amazonaws.com",
            port=5432,
            user="project_user_4",
            password="ZUr7UMAkA3mPQgrQ2jckFDfa",
            database="totesys"
            )
        cursor = conn.cursor()

        # Create some mock tables in the database
        cursor.execute("CREATE TABLE table1 (col1 INT, col2 INT)")
        cursor.execute("CREATE TABLE table2 (col1 INT, col2 INT)")
        cursor.execute("CREATE TABLE table3 (col1 INT, col2 INT)")

        # Add some mock data to the tables
        cursor.execute("INSERT INTO table1 VALUES (1, 2)")
        cursor.execute("INSERT INTO table2 VALUES (3, 4)")
        cursor.execute("INSERT INTO table3 VALUES (5, 6)")

        # Close the database connection
        cursor.close()
        conn.close()

        # Ingest the mock database to the S3 bucket
        ingest_database_to_s3()

        # Verify that the CSV files were created and uploaded to the "ingested-data-bucket-1" bucket
        s3 = boto3.client("s3")
        bucket = s3.list_objects(Bucket="ingested-data-bucket-1")
        self.assertEqual(bucket["KeyCount"], 3)
        self.assertIn("table1.csv", bucket["Contents"])
        self.assertIn("table2.csv", bucket["Contents"])
        self.assertIn("table3.csv", bucket["Contents"])


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
