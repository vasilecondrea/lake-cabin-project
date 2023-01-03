import json

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

    date_list = [date.split(sep, 1)[0] for date in datetime_list]
    time_list = [time.split(sep, 1)[1] for time in datetime_list]

    return {'dates': date_list, 'times': time_list}