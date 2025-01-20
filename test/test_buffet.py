from util import download_file


def test_add():
    url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=1948-01-01&fq=Monthly'
    folder_path = 'c:/Users/yexin/OneDrive/PDAJ/Yexin/Finance/Data'
    file_name = 'unemployment-monthly.csv'

    download_file(url, folder_path, file_name)
