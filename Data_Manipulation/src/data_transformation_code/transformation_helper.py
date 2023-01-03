import json
from datetime import datetime
import dateutil.parser as parser

def delete_cols_from_df(df, col_list):
    for col in col_list:
        del df[col]
    return df


def create_lookup_from_json(json_file, key, value, path="tests/"):
    configPath = path + json_file

    with open(configPath) as f:
        data = json.load(f)
        lookup = {}
        for element in data:
            lookup[element[key]] = element[value] 
    
    return lookup


def split_datetime_list_to_date_and_time_list(datetime_list):
    sep = ' '

    # for time in datetime_list:
    #     if '.' in time.split(sep, 1)[1]:
    # date_list = [parser.parse(datet).strftime('%Y-%m-%d') for datet in datetime_list]
    # time_list = [parser.parse(datet).strftime('%H:%M:%S.%f') for datet in datetime_list]

    date_list = [datetime.strptime(date.split(sep, 1)[0], '%Y-%m-%d') for date in datetime_list]
    time_list = [datetime.strptime(time.split(sep, 1)[1], '%H:%M:%S.%f') if '.' in time.split(sep, 1)[1] else datetime.strptime(time.split(sep, 1)[1], '%H:%M:%S') for time in datetime_list]

    return {'dates': date_list, 'times': time_list}