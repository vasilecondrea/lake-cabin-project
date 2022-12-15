import pandas as pd
import json
import tempfile
from datetime import datetime
import math
import boto3

def lambda_handler(event, context):
    s3 = boto3.client("s3")
    landing_zone_bucket = 'landing_zone_bucket'
    processed_bucket = 'processed_bucket'
    list_objects = s3.list_objects(Bucket=landing_zone_bucket)
    
    for obj_name in list_objects:
        file = retrieve_csv_from_s3_bucket(s3, landing_zone_bucket, obj_name)
        df = convert_csv_to_parquet_data_frame(file)

        if obj_name == 'payment_type.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_payment_type.parquet', create_dim_payment_type(df))
        elif obj_name == 'transaction.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_transaction.parquet', create_dim_transaction(df))
        elif obj_name == 'currency.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'dim_currency.parquet', create_dim_currency(df))
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
        elif obj_name == 'sales_order.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'fact_sales_order.parquet', create_fact_sales_order(df))
        elif obj_name == 'purchase_order.csv':
            save_and_upload_data_frame_as_parquet_file(s3, processed_bucket, 'fact_purchase_orders.parquet', create_fact_purchase_orders(df))

    # write tests
    return 'processing finished!'

def retrieve_csv_from_s3_bucket(s3, bucket, key):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.name = key
        s3.download_file(Bucket=bucket, Key=key, Filename=f.name)
        return f


def convert_csv_to_parquet_data_frame(file):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        df = pd.read_csv(file)
        df.to_parquet(f.name)
        df = pd.read_parquet(f.name)
        return df


def delete_cols_from_df(df, col_list):
    for col in col_list:
        del df[col]
    return df

def create_lookup_from_json(json_file, key, value):
    with open(json_file) as f:
        data = json.load(f)
        lookup = {}
        for element in data:
            lookup[element[key]] = element[value] 
    
    return lookup


def create_dim_counterparty(counterparty_df, address_df):
    dim_counterparty_df = counterparty_df.copy()

    cols_to_delete = ['commercial_contact', 'delivery_contact', 'created_at', 'last_updated']
    dim_counterparty_df = delete_cols_from_df(dim_counterparty_df, cols_to_delete)

    address_df_copy = address_df.copy()
    address_df_copy = address_df_copy.rename(columns={'address_id':'legal_address_id'})
    cols_to_delete = ['created_at', 'last_updated']
    address_df_copy = delete_cols_from_df(address_df_copy, cols_to_delete)

    result = pd.merge(dim_counterparty_df, address_df_copy, on='legal_address_id')
    result = delete_cols_from_df(result, ['legal_address_id']) 

    return result


def create_dim_transaction(transaction_df):
    dim_transaction_df = transaction_df.copy()

    cols_to_delete = ['created_at', 'last_updated']
    dim_transaction_df = delete_cols_from_df(dim_transaction_df, cols_to_delete)

    return dim_transaction_df


def create_dim_payment_type(payment_df):
    dim_payment_type_df = payment_df.copy()
    
    cols_to_delete = ['created_at', 'last_updated']
    dim_payment_type_df = delete_cols_from_df(dim_payment_type_df, cols_to_delete)

    return dim_payment_type_df


def create_dim_currency(currency_df, lookup):
    dim_currency = currency_df.copy()

    cols_to_delete = ['created_at', 'last_updated']
    dim_currency = delete_cols_from_df(dim_currency, cols_to_delete)

    currency_names = [lookup[currency_code] for currency_code in dim_currency['currency_code']]

    dim_currency['currency_name'] = currency_names

    return dim_currency


def create_dim_design(design_df):
    dim_design = design_df.copy()

    cols_to_delete = ['created_at', 'last_updated']
    dim_design = delete_cols_from_df(dim_design, cols_to_delete)

    return dim_design


def create_dim_date(sale_related_df):
    sale_related_copy = sale_related_df.copy()

    cols_to_extract = ['created_at', 'last_updated', 'agreed_delivery_date', 'agreed_payment_date']
    if "agreed_delivery_date" not in sale_related_copy:
        cols_to_extract = ['created_at', 'last_updated', 'payment_date']

    dim_date = pd.DataFrame({
        'date_id': [],
        'year': [],
        'month': [],
        'day': [],
        'day_of_week': [],
        'day_name': [],
        'month_name': [],
        'quarter': []
    })

    index = [0]

    sale_related_copy = sale_related_copy[cols_to_extract]

    for key in sale_related_copy:
        for value in sale_related_copy[key]:
            sep = ' '
            time_string = value
            time_string_stripped = time_string.split(sep, 1)[0]

            time_datetime = datetime.strptime(time_string_stripped, '%Y-%m-%d')
            
            time_exists = False

            if len(dim_date['date_id']) != 0:
                for time in dim_date['date_id']:
                    time_as_string = time.strftime('%Y-%m-%d')
                    if time_as_string == time_string_stripped:
                        time_exists = True
                        break
            
            if time_exists == False:
                df_to_add = pd.DataFrame({
                    'date_id': [time_datetime],
                    'year': [time_datetime.year],
                    'month': [time_datetime.month],
                    'day': [time_datetime.day],
                    'day_of_week': [time_datetime.weekday()],
                    'day_name': [time_datetime.strftime("%A")],
                    'month_name': [time_datetime.strftime("%B")],
                    'quarter': [math.ceil(time_datetime.month / 3)]
                }, index=index)

                frames = [dim_date, df_to_add]
                dim_date = pd.concat(frames)
                index[0] += 1

    dim_date = dim_date.astype({'year':'int', 'month':'int', 'day':'int', 'day_of_week':'int', 'quarter':'int'})
    return dim_date
            

def create_dim_location(address_df):
    dim_location = address_df.copy()

    cols_to_delete = ['created_at', 'last_updated']
    dim_location = delete_cols_from_df(dim_location, cols_to_delete)

    return dim_location


def create_dim_staff(staff_df, department_df):
    dim_staff = staff_df.copy()

    cols_to_delete = ['created_at', 'last_updated']
    dim_staff = delete_cols_from_df(dim_staff, cols_to_delete)

    department_df_copy = department_df.copy()
    cols_to_delete = ['manager', 'created_at', 'last_updated']
    department_df_copy = delete_cols_from_df(department_df_copy, cols_to_delete)

    result = pd.merge(dim_staff, department_df_copy, on='department_id')
    result = delete_cols_from_df(result, ['department_id']) 

    return result[['staff_id', 'first_name', 'last_name', 'department_name', 'location', 'email_address']]


def create_fact_sales_order(sales_order_df):
    fact_sales_order = sales_order_df.copy()

    fact_sales_order['created_date'] = split_datetime_list_to_date_and_time_list(fact_sales_order['created_at'])['dates']
    fact_sales_order['created_time'] = split_datetime_list_to_date_and_time_list(fact_sales_order['created_at'])['times']
    fact_sales_order['last_updated_date'] = split_datetime_list_to_date_and_time_list(fact_sales_order['last_updated'])['dates']
    fact_sales_order['last_updated_time'] = split_datetime_list_to_date_and_time_list(fact_sales_order['last_updated'])['times'] 

    cols_to_delete = ['units_sold', 'unit_price', 'created_at', 'last_updated']
    fact_sales_order = delete_cols_from_df(fact_sales_order, cols_to_delete)

    fact_sales_order = fact_sales_order.rename(columns={'staff_id':'sales_staff_id'})

    return fact_sales_order[['sales_order_id', 'created_date', 'created_time', 'last_updated_date', 'last_updated_time', 'sales_staff_id', \
        'counterparty_id', 'currency_id', 'design_id', 'agreed_delivery_date', 'agreed_payment_date', 'agreed_delivery_location_id']]


def create_fact_payment(payment_df):
    fact_payment = payment_df.copy()

    fact_payment['created_date'] = split_datetime_list_to_date_and_time_list(fact_payment['created_at'])['dates']
    fact_payment['created_time'] = split_datetime_list_to_date_and_time_list(fact_payment['created_at'])['times']
    fact_payment['last_updated_date'] = split_datetime_list_to_date_and_time_list(fact_payment['last_updated'])['dates']
    fact_payment['last_updated_time'] = split_datetime_list_to_date_and_time_list(fact_payment['last_updated'])['times']
    
    cols_to_delete = ['created_at', 'last_updated', 'company_ac_number', 'counterparty_ac_number']
    fact_payment = delete_cols_from_df(fact_payment, cols_to_delete)

    return fact_payment[['payment_id', 'created_date', 'created_time', 'last_updated_date', 'last_updated_time', 'transaction_id', \
        'counterparty_id', 'payment_amount', 'currency_id', 'payment_type_id', 'paid', 'payment_date']]


def create_fact_purchase_orders(purchase_df):
    fact_purchase_orders = purchase_df.copy()

    fact_purchase_orders['created_date'] = split_datetime_list_to_date_and_time_list(fact_purchase_orders['created_at'])['dates']
    fact_purchase_orders['created_time'] = split_datetime_list_to_date_and_time_list(fact_purchase_orders['created_at'])['times']
    fact_purchase_orders['last_updated_date'] = split_datetime_list_to_date_and_time_list(fact_purchase_orders['last_updated'])['dates']
    fact_purchase_orders['last_updated_time'] = split_datetime_list_to_date_and_time_list(fact_purchase_orders['last_updated'])['times'] 
    
    cols_to_delete = ['created_at', 'last_updated']
    fact_purchase_orders = delete_cols_from_df(fact_purchase_orders, cols_to_delete)

    return fact_purchase_orders[['purchase_order_id', 'created_date', 'created_time', 'last_updated_date', 'last_updated_time', \
        'staff_id', 'counterparty_id', 'item_code', 'item_quantity', 'item_unit_price', 'currency_id', 'agreed_delivery_date', \
        'agreed_payment_date', 'agreed_delivery_location_id']]


def save_and_upload_data_frame_as_parquet_file(s3, bucket, key, df):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        df.to_parquet(f.name)
        s3.upload_file(Filename=f.name, Bucket=bucket, Key=key)


def split_datetime_list_to_date_and_time_list(datetime_list):
    sep = ' '

    date_list = [date.split(sep, 1)[0] for date in datetime_list]
    time_list = [time.split(sep, 1)[1] for time in datetime_list]

    return {'dates': date_list, 'times': time_list}