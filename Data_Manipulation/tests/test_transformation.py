from moto import mock_s3
import boto3
from Data_Manipulation.src.transformation import read_files_from_s3_bucket, create_dim_counterparty, create_dim_transaction, create_dim_payment_type, delete_cols_from_df, create_dim_currency, create_lookup_from_json
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

def test_delete_cols_from_df():
    
    test_df = pd.DataFrame({
        'col_1': [1, 2],
        'col_2': [1, 2]
    })
    
    expected_df = pd.DataFrame({
        'col_2': [1, 2]
    })

    result = delete_cols_from_df(test_df, ['col_1'])

    pd.testing.assert_frame_equal(result, expected_df)

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
        'address_id': [15, 28],
        'address_line_1': ['605 Haskell Trafficway', '079 Horacio Landing'],
        'address_line_2': ['Axel Freeway', None],
        'district': [None, None],
        'city': ['East Bobbie', 'Utica'],
        'postal_code': ['88253-4257', '93045'],
        'country':['Heard Island and McDonald Islands', 'Austria'],
        'phone':['9687 937447', '7772 084705'],
        'created_at': ['2022-11-03 14:20:49.962', '2022-11-03 14:20:49.962'],
        'last_updated': ['2022-11-03 14:20:49.962', '2022-11-03 14:20:49.962'],
    })
   
    dim_counterparty_df = pd.DataFrame({
        'counterparty_id': [1, 2],
        'counterparty_legal_name': ['Fahey and Sons', 'Leannon, Predovic and Morar'],
        'address_line_1': ['605 Haskell Trafficway', '079 Horacio Landing'],
        'address_line_2': ['Axel Freeway', None],
        'district': [None, None],
        'city': ['East Bobbie', 'Utica'],
        'postal_code': ['88253-4257', '93045'],
        'country':['Heard Island and McDonald Islands', 'Austria'],
        'phone':['9687 937447', '7772 084705']
    })

    result = create_dim_counterparty(counterparty_df, address_df)

    pd.testing.assert_frame_equal(result, dim_counterparty_df) 

def test_modify_data_for_dim_transaction_table():
        
    transaction_df = pd.DataFrame({
        'transaction_id': [1, 2],
        'transaction_type': ['PURCHASE', 'PURCHASE'],
        'sales_order_id': [None, None],
        'purchase_order_id': [2, 3],
        'created_at': ['2022-11-03 14:20:52.186', '2022-11-03 14:20:52.187'],
        'last_updated': ['2022-11-03 14:20:52.18', '2022-11-03 14:20:52.187']
    })

    dim_transaction_df = pd.DataFrame({
        'transaction_id': [1, 2],
        'transaction_type': ['PURCHASE', 'PURCHASE'],
        'sales_order_id': [None, None],
        'purchase_order_id': [2, 3]
    })

    result = create_dim_transaction(transaction_df)

    pd.testing.assert_frame_equal(result, dim_transaction_df)

def test_modify_data_for_dim_payment_type():

    payment_type_df = pd.DataFrame({
        'payment_type_id': [1, 2],
        'payment_type_name': ['SALES_RECEIPT', 'SALES_REFUND'],
        'created_at': ['2022-11-03 14:20:49.962', '2022-11-03 14:20:49.962'],
        'last_updated': ['2022-11-03 14:20:49.962', '2022-11-03 14:20:49.962']
    })

    dim_payment_type = pd.DataFrame({
        'payment_type_id': [1, 2],
        'payment_type_name': ['SALES_RECEIPT', 'SALES_REFUND'],
    })

    result = create_dim_payment_type(payment_type_df)

    pd.testing.assert_frame_equal(result, dim_payment_type)

def test_create_lookup_from_json():
    
    test_json_file = 'lookup_test.json'
    
    expected_lookup = {
        "ALL": "Albania Lek",
        "AFN": "Afghanistan Afghani",
        "ARS": "Argentina Peso"
    }

    result = create_lookup_from_json(test_json_file, 'abbreviation', 'currency')

    assert result == expected_lookup

def test_modify_data_for_dim_currency():

    currency_df = pd.DataFrame({
        'currency_id': [1, 2],
        'currency_code': ['GBP', 'USD'],
        'created_at': ['2022-11-03 14:20:49.962', '2022-11-03 14:20:49.962'],
        'last_updated': ['2022-11-03 14:20:49.962', '2022-11-03 14:20:49.962']
    })

    dim_currency = pd.DataFrame({
        'currency_id': [1, 2],
        'currency_code': ['GBP', 'USD'],
        'currency_name': ['British Pound Sterling', 'United States Dollar']
    })

    result = create_dim_currency(currency_df)

    # pd.testing.assert_frame_equal(result, dim_currency)


# ensure that we can read the file in the landing zone bucket
# convert the parquet file into readable python format
# prepare that data to be used for the processed bucket
# convert back to parquet
# store data in processed bucket
# upload processed bucket data into warehouse