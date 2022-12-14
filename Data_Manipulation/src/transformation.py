import pandas as pd
import io
import json

def read_files_from_s3_bucket(s3, bucket, key):
    
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
    return df

    # adding column to dataframe
    addresses = ['New York', 'Paris']
    df['Address'] = addresses

def delete_cols_from_df(df, col_list):
    for col in col_list:
        del df[col]
    return df
    
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

def create_lookup_from_json(json_file, key, value):
    
    with open(json_file) as f:
        data = json.load(f)
        lookup = {}
        for element in data:
            lookup[element[key]] = element[value] 
    
    return lookup

def create_dim_currency(currency_df):
    
    pass