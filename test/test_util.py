from util import download_file_and_compare
import os


def test_download_success(mocker):
    with open('./test/unemployment.csv', mode='rb') as file:
        csv_content = file.read()
    mocker.patch('requests.get', return_value=mocker.Mock(status_code=200, content=csv_content))
    status = download_file_and_compare('', './test', 'temp-unemployment.csv')
    assert status.success
    assert status.result == 'New file downloaded'

    status = download_file_and_compare('', './test', 'temp-unemployment.csv')
    assert status.success
    assert status.result == 'No Change, skipping file update'

    with open('./test/unemployment2.csv', mode='rb') as file:
        csv_content = file.read()
    mocker.patch('requests.get', return_value=mocker.Mock(status_code=200, content=csv_content))
    status = download_file_and_compare('', './test', 'temp-unemployment.csv')
    assert status.success
    assert status.result == 'Change detected, file updated'
    os.remove('./test/temp-unemployment.csv')


def test_download_failure(mocker):
    mocker.patch('requests.get', return_value=mocker.Mock(status_code=503, content=None))
    status = download_file_and_compare('', './temp', 'unemployment-monthly.csv')

    assert not status.success
    assert status.result == 'Failed with status code 503'
