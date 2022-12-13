import pandas as pd
import io

def read_files_from_s3_bucket(s3, bucket, key):
    
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
    return df

    # adding column to dataframe
    addresses = ['New York', 'Paris']
    df['Address'] = addresses
