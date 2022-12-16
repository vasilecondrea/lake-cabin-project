import boto3
import pg8000
import datetime

# Create an S3 client
s3 = boto3.client('s3')

# Create a CloudWatch client
cloudwatch = boto3.client('cloudwatch')

def create_s3_buckets():
    # Create the two S3 buckets
    s3.create_bucket(Bucket='ingested-data-bucket-1')
    s3.create_bucket(Bucket='processed-data-bucket-1')


def ingest_database_to_s3():
    try:
        # Connect to the PostgreSQL database
        conn = pg8000.connect(
            host="nc-data-eng-totesys-production.chpsczt8h1nu.eu-west-2.rds.amazonaws.com",
            port=5432,
            user="project_user_4",
            password="ZUr7UMAkA3mPQgrQ2jckFDfa",
            database="totesys"
            )
        cursor = conn.cursor()

        # Retrieve all table names from the totesys database
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        table_names = [row[0] for row in cursor.fetchall()]

        # Save the data from each table in a separate file in the "ingestion" S3 bucket
        for table_name in table_names:
            # Retrieve the data from the current table
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Save the data to a CSV file in the "ingestion" S3 bucket
            with open(f"{table_name}.csv", "w") as file:
                for row in rows:
                    file.write(",".join([str(cell) for cell in row]))
                    file.write("\n")
            s3.upload_file(f"{table_name}.csv", "ingested-data-bucket-1", f"{table_name}.csv")

        # Close the database connection
        cursor.close()
        conn.close()

    except Exception as e:
        # Log the error message to CloudWatch
        cloudwatch.put_metric_data(
            MetricData=[{
                'MetricName': 'IngestionError',
                'Timestamp': datetime.datetime.utcnow(),
                'Value': 1
            }],
            Namespace='Ingestion'
        )
        cloudwatch.put_log_


def lambda_handler(event, context):
    # Log the start time of the function execution
    cloudwatch.put_metric_data(
        MetricData=[{
            'MetricName': 'IngestionStartTime',
            'Timestamp': datetime.datetime.utcnow(),
            'Value': 1
        }],
        Namespace='Ingestion'
    )

    # Create the S3 buckets
    create_s3_buckets()

    # Ingest the database to S3
    ingest_database_to_s3()

    # Log the end time of the function execution
    cloudwatch.put_metric_data(
        MetricData=[{
            'MetricName': 'IngestionEndTime',
            'Timestamp': datetime.datetime.utcnow(),
            'Value': 1
        }],
        Namespace='Ingestion'
    )





