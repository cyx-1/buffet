import requests
import os


def download_file(url, folder_path, file_name):  # pragma: no cover
    # Make the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Download the file
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded and saved to {file_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")


# url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=1948-01-01&coed=2026-12-01&fq=Monthly"
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=1948-01-01&fq=Monthly"
folder_path = "c:/Users/yexin/OneDrive/PDAJ/Yexin/Finance/Data"
file_name = "unemployment-monthly.csv"

download_file(url, folder_path, file_name)
