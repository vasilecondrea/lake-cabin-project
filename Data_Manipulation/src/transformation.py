import pandas as pd
import json
import tempfile
from datetime import datetime
import math

def retrieve_csv_from_s3_bucket(s3, bucket, key):
    with tempfile.NamedTemporaryFile(delete=False) as f:
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


def create_dim_counterparty(counterparty_df, address_df=None):
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
    # an if statement to extract different columns for payment

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

def create_dim_staff():
    pass