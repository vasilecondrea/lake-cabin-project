import tempfile

def save_and_upload_data_frame_as_parquet_file(s3, bucket, key, df):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        df.to_parquet(f.name)
        s3.upload_file(Filename=f.name, Bucket=bucket, Key=key)