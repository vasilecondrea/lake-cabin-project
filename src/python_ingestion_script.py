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
    # Retrieve the database connection details from AWS Secrets Manager
    secrets_manager_client = boto3.client("secretsmanager")
    secret_value_response = secrets_manager_client.get_secret_value(SecretId="Source Database Creds") #Change this to match
    secret_dict = json.loads(secret_value_response["SecretString"])

    host = secret_dict["host"]
    port = secret_dict["port"]
    user = secret_dict["username"]
    password = secret_dict["password"]
    database = secret_dict["database"]

    # Connect to the PostgreSQL database
    conn = pg8000.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()

    try:
        # Retrieve all table names from the totesys database
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        table_names = [row[0] for row in cursor.fetchall()]

        # Save the data from each table in a separate file in the "ingestion" S3 bucket
        for table_name in table_names:
            # Check if the table has been modified since the last time it was ingested
            cursor.execute(f"SELECT max(last_update) FROM {table_name}")
            last_update = cursor.fetchone()[0]
            # If the table has been modified, retrieve and save the updated data
            if last_update > datetime.datetime.utcnow() - datetime.timedelta(hours=0.5): #Change this to what you decide on
                # Retrieve the data from the current table
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                # Save the data to a CSV file in the "ingestion" S3 bucket
                with open(f"{table_name}.csv", "w") as file:
                    for row in rows:
                        file.write(",".join([str(cell) for cell in row]))
                        file.write("\n")
                s3.upload_file(f"{table_name}.csv", "ingested-data-bucket-1", f"{table_name}.csv")
            else:
                # Log a message to CloudWatch indicating that the table has not been modified
                cloudwatch.put_log_events(
                    LogGroupName='Ingestion',
                    LogStreamName=table_name,
                    Events=[{
                        'Timestamp': datetime.datetime.utcnow(),
                        'Message': 'Table has not been modified'
                    }]
                )

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





