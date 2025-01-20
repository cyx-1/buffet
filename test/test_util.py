from util import download_file


def test_add(mocker):
    with open('./test/unemployment.csv', mode='rb') as file:
        csv_content = file.read()
    mocker.patch('requests.get', return_value=mocker.Mock(status_code=200, content=csv_content))
    status = download_file('', './temp', 'unemployment-monthly.csv')
    assert status.success


def test_download_failure(mocker):
    mocker.patch('requests.get', return_value=mocker.Mock(status_code=503, content=None))
    status = download_file('', './temp', 'unemployment-monthly.csv')

    assert not status.success
    assert status.reason == 'Failed with status code 503'
