import urllib.request
import pytest
from http import HTTPStatus
from pathlib import Path

from zakat import (
    ZakatTracker,
    Action,
    start_file_server,
    find_available_port,
    FileType,
)


@pytest.fixture
def data_directory(pytestconfig):
    return Path(pytestconfig.rootdir) / "tests/data"


def read_file(file_path):
    with open(file_path, "rb") as file:  # Open in binary mode
        bytes_object = bytes(file.read())  # Read into BytesIO
    return bytes_object


# Helper callback functions (replace with actual logic if needed)
def mock_database_callback(file_path):
    ZakatTracker(db_path=file_path)  # Simulate database interaction


def mock_csv_callback(file_path, database_path, debug):
    tracker = ZakatTracker(db_path=database_path)
    return tracker.import_csv(file_path, debug=debug)


# Tests
def test_find_available_port():
    port = find_available_port()
    assert 0 < port < 65536  # Ensure it's a valid port


def test_start_file_server_download_and_show_upload_form(data_directory):
    _, download_url, upload_url, server_thread, shutdown_server = start_file_server(
        f'{data_directory}/file.pickle', debug=True
    )
    server_thread.start()

    try:
        response = urllib.request.urlopen(download_url)
        assert response.getcode() == HTTPStatus.OK
        assert response.info()['Content-Disposition'] == f'attachment; filename="file.pickle"'
        response = urllib.request.urlopen(upload_url)
        assert response.getcode() == HTTPStatus.OK
        assert f'<h3>You can download the <a target="__blank" href="{download_url}">database file</a>...</h3>' in str(response.read())
    finally:
        shutdown_server()


# def test_start_file_server_upload_invalid_type(data_directory):
#     file_png_bytes = read_file_to_bytesio(data_directory / 'file.png')
#     _, _, upload_url, server_thread, shutdown_server = start_file_server(
#         f'{data_directory}/file.pickle', debug=True
#     )
#     server_thread.start()
#     try:
#         # Simulate form submission with invalid type
#         response = urllib.request.urlopen(upload_url, data=urllib.parse.urlencode({
#             'file': ('test_file.png', file_png_bytes),
#             'upload_type': 'invalid'
#         }).encode())
#         raise Exception(response.getcode())
#         assert response.getcode() == HTTPStatus.BAD_REQUEST
#     finally:
#         shutdown_server()

# def test_start_file_server_upload_db(data_directory):
#     _, _, upload_url, server_thread, shutdown_server = start_file_server(
#         f'{data_directory}/file.pickle', database_callback=mock_database_callback, debug=True
#     )
#     server_thread.start()
#     try:
#         # Simulate form submission with db file
#         response = urllib.request.urlopen(upload_url, data=urllib.parse.urlencode({
#             'file': ('test_file.db', BytesIO(b'some data')),
#             'upload_type': FileType.Database.value
#         }).encode())
#         assert response.getcode() == HTTPStatus.OK
#     finally:
#         shutdown_server()


# def test_start_file_server_upload_csv(data_directory):
#     _, _, upload_url, server_thread, shutdown_server = start_file_server(
#         f'{data_directory}/file.pickle', csv_callback=mock_csv_callback, debug=True
#     )
#     server_thread.start()
#
#     try:
#         # Simulate form submission with csv file
#         response = urllib.request.urlopen(upload_url, data=urllib.parse.urlencode({
#             'file': ('test_file.csv', BytesIO(b'some data')),
#             'upload_type': FileType.CSV.value
#         }).encode())
#
#         assert response.getcode() == HTTPStatus.OK
#         assert response.read() == b'File uploaded successfully.'
#     finally:
#         shutdown_server()
