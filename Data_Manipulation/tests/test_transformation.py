from Data_Manipulation.src.transformation import connect_to_db, extract_date
from unittest.mock import Mock, patch
import pytest
from datetime import date, datetime

def test_throws_exception_if_unsuccessful_connection():
    with pytest.raises(Exception):
        connect_to_db('fake_database', 'fake_user', 'fake_password', 'fake_host', '9999')

def test_opens_database_link_if_successful_connection():
    # don't put the credentials in plaintext
    #conn = connect_to_db('---', '---', '---', '---', '5432')
    #assert conn.status == 1
    pass

def test_execute_returns_data():
    pass