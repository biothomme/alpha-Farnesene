# collections of functions that might be useful
import csv
import os
import requests

def run_request(url):
    '''Run buffered request online.
    '''
    from requests.exceptions import HTTPError

    try:
        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as err : print(f'We had an issue. {err}')
    else:
        return response.text
    return None

def run_request_sneaky(url):
    '''Run buffered request online.
    '''
    from requests.exceptions import HTTPError
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except HTTPError as err : print(f'We had an issue. {err}')
    else:
        return response.text
    return None

def init_csvwriter(csv_file, header, force=False, extend=False):
    '''Initialize a csv.DictWriter.
    '''
    make_csv_writer = lambda x : csv.DictWriter(x, fieldnames=header)

    # make csv_file
    if not os.path.exists(csv_file) or force:
        file_handle = open(csv_file, "w")
        csv_writer = make_csv_writer(file_handle)
        csv_writer.writeheader()
    elif extend:
        file_handle = open(csv_file, "a")
        csv_writer = make_csv_writer(file_handle)
    else : raise FileExistsError(csv_file)
    return file_handle, csv_writer