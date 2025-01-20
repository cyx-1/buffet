import requests
import os
from collections import namedtuple

Status = namedtuple('Status', ['success', 'reason'])


def download_file(url, folder_path, file_name):

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)  # pragma: no cover

    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return Status(success=True, reason=None)
    else:
        return Status(success=False, reason=f'Failed with status code {response.status_code}')
