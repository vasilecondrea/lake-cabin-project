import boto3
from src.data_transformation_code.transformation_retrieve import retrieve_csv_from_s3_bucket, convert_csv_to_parquet_data_frame
from src.data_transformation_code.transformation_upload import save_and_upload_data_frame_as_parquet_file
from src.data_transformation_code.transformation_tables import create_dim_counterparty, create_dim_transaction, create_dim_payment_type, create_dim_currency, create_dim_design, create_dim_date, create_dim_location, create_dim_staff, create_fact_sales_order, create_fact_payment, create_fact_purchase_orders
from src.data_transformation_code.transformation_helper import create_lookup_from_json

def lambda_handler(event, context):

    s3 = boto3.client("s3")
    landing_zone_bucket = event['ingested_bucket']
    processed_bucket = event['processed_bucket']
    list_objects = [object['Key'] for object in s3.list_objects(Bucket=landing_zone_bucket)['Contents']]

    lookup = create_lookup_from_json('currency-symbols.json', 'abbreviation', 'currency')

    for obj_name in list_objects:
        file = retrieve_csv_from_s3_bucket(s3, landing_zone_bucket, obj_name)
        df = convert_csv_to_parquet_data_frame(file)

        if obj_name == 'payment_type.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_payment_type.parquet', create_dim_payment_type(df))
        elif obj_name == 'transaction.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_transaction.parquet', create_dim_transaction(df))
        elif obj_name == 'currency.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_currency.parquet', create_dim_currency(df, lookup))
        elif obj_name == 'design.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_design.parquet', create_dim_design(df))
        elif obj_name == 'staff.csv':
            department_file = retrieve_csv_from_s3_bucket(s3, landing_zone_bucket, 'department.csv')
            department_df = convert_csv_to_parquet_data_frame(department_file)
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_staff.parquet', create_dim_staff(df, department_df))
        elif obj_name == 'counterparty.csv':
            address_file = retrieve_csv_from_s3_bucket(s3, landing_zone_bucket, 'address.csv')
            address_df = convert_csv_to_parquet_data_frame(address_file)
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_counterparty.parquet', create_dim_counterparty(df, address_df))
        elif obj_name == 'payment.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'fact_payment.parquet', create_fact_payment(df))
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_date_payment.parquet', create_dim_date(df))
        elif obj_name == 'sales_order.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'fact_sales_order.parquet', create_fact_sales_order(df))
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_date_sales_order.parquet', create_dim_date(df))
        elif obj_name == 'purchase_order.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'fact_purchase_orders.parquet', create_fact_purchase_orders(df))
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_date_purchase_orders.parquet', create_dim_date(df))
        elif obj_name == 'address.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_location.parquet', create_dim_location(df))

    message = 'Finished processing!'
    return { 
        'message' : message
    }