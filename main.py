import util

if __name__ == '__main__':
    test = 'hello world'
    url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=1948-01-01&fq=Monthly'
    folder_path = 'c:\\Users\\yexin\\OneDrive\\PDAJ\\Yexin\\Finance\\Data'
    file_name = 'unemployment-monthly.csv'
    util.download_file_and_compare(url, folder_path, file_name)
