import pandas as pd
import tempfile

def retrieve_csv_from_s3_bucket(s3, bucket, key, path=""):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.name = path + key
        s3.download_file(Bucket=bucket, Key=key, Filename=f.name)
        return f


def convert_csv_to_parquet_data_frame(file):
    with open(file.name, 'r') as orig_f:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            df = pd.read_csv(orig_f)
            df.to_parquet(f.name)
            df = pd.read_parquet(f.name)
            return df