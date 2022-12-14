import pandas as pd
import io

def read_files_from_s3_bucket(s3, bucket, key):
    
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
    return df

    # adding column to dataframe
    addresses = ['New York', 'Paris']
    df['Address'] = addresses

def create_dim_counterparty(counterparty_df, address_df=None):
    dim_counterparty_df = counterparty_df.copy()
    del dim_counterparty_df['commercial_contact']
    del dim_counterparty_df['delivery_contact']
    del dim_counterparty_df['created_at']
    del dim_counterparty_df['last_updated']
    address_df_copy = address_df.copy()
    address_df_copy = address_df_copy.rename(columns={'address_id':'legal_address_id'})
    del address_df_copy['created_at']
    del address_df_copy['last_updated']
    result = pd.merge(dim_counterparty_df, address_df_copy, on='legal_address_id')
    del result['legal_address_id']
    return result

def create_dim_transaction(transaction_df):
    dim_transaction_df = transaction_df.copy()
    del dim_transaction_df['created_at']
    del dim_transaction_df['last_updated']
    return dim_transaction_df

def create_dim_payment_type(payment_df):
    dim_payment_type_df = payment_df.copy()
    del dim_payment_type_df['created_at']
    del dim_payment_type_df['last_updated']
    return dim_payment_type_df