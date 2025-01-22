import requests
import os
from collections import namedtuple

Status = namedtuple('Status', ['success', 'result'])


def download_file_and_compare(url, folder_path, file_name):

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)  # pragma: no cover

    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return Status(success=True, result='New file downloaded')
        else:
            with open(file_path, 'rb') as file:
                file_content = file.read()
                if file_content == response.content:
                    return Status(success=True, result='No Change, skipping file update')
                else:
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    return Status(success=True, result='Change detected, file updated')
    else:
        return Status(success=False, result=f'Failed with status code {response.status_code}')
