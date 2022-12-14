from moto import mock_s3
import boto3
from Data_Manipulation.src.transformation import read_files_from_s3_bucket
import pandas as pd

@mock_s3
def test_read_from_parquet_file():

    df = pd.DataFrame({
        'sales_order_id': [1, 2],
        'created_at': ['2022-11-03 14:20:52.186', '2022-11-03 14:20:52.186'],
        'last_updated': ['2022-11-03 14:20:52.186', '2022-11-03 14:20:52.186'],
        'design_id': [9, 3],
        'staff_id': [16, 19],
        'counterparty_id': [18, 8],
        'units_sold': [84754, 42972],
        'unit_price': [2.43, 3.94],
        'currency_id': [3, 2],
        'agreed_delivery_date': ['2022-11-10', '2022-11-07'],
        'agreed_payment_date': ['2022-11-03', '2022-11-08'],
        'agreed_delivery_location_id': [4, 8]
    })

    file = "test_parquet.parquet"
    bucket = "test_bucket"

    df.to_parquet(file)

    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=bucket)
    s3.upload_file(Filename=file, Bucket=bucket, Key=file)

    result = read_files_from_s3_bucket(s3, bucket, file)

    pd.testing.assert_frame_equal(result, df)

def test_modify_data_for_dim_counterparty_table():

    counterparty_df = pd.DataFrame({
        'counterparty_id': [1, 2],
        'counterparty_legal_name': ['Fahey and Sons', 'Leannon, Predovic and Morar'],
        'legal_address_id': [15, 28],
        'commercial_contact': ['Micheal Toy', 'Melba Sanford'],
        'delivery_contact': ['Mrs. Lucy Runolfsdottir', ' Jean Hane III'],
        'created_at': ['2022-11-03 14:20:51.563', '2022-11-03 14:20:51.563'],
        'last_updated': ['2022-11-03 14:20:51.563', '2022-11-03 14:20:51.563'],
    })

    address_df = pd.DataFrame({
        'counterparty_id': [1, 2],
        'counterparty_legal_name': ['Fahey and Sons', 'Leannon, Predovic and Morar'],
        'legal_address_id': [15, 28],
        'commercial_contact': ['Micheal Toy', 'Melba Sanford'],
        'delivery_contact': ['Mrs. Lucy Runolfsdottir', ' Jean Hane III'],
        'created_at': ['2022-11-03 14:20:51.563', '2022-11-03 14:20:51.563'],
        'last_updated': ['2022-11-03 14:20:51.563', '2022-11-03 14:20:51.563'],
    })

    pass

# ensure that we can read the file in the landing zone bucket
# convert the parquet file into readable python format
# prepare that data to be used for the processed bucket
# convert back to parquet
# store data in processed bucket
# upload processed bucket data into warehouse