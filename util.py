import requests
import os


def download_file(url, folder_path, file_name):
    # Make the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded and saved to {file_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")
