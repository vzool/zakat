"""
This module provides a file server for managing database and CSV uploads and downloads
in a Zakat application.

It defines enumerations for file types and actions, and provides functions to:

- Find an available TCP port on the local machine.
- Start a multi-purpose WSGI server for file interactions.

The server supports:

- Downloading a database file.
- Uploading a new database file to replace the existing one.
- Uploading a CSV file to import data into the existing database.

The module also includes a main function for example usage and testing.

Classes:
- FileType (enum.Enum): Enumeration for file types (Database, CSV).
- Action (enum.Enum): Enumeration for various actions (CREATE, TRACK, etc.).

Functions:
- find_available_port() -> int: Finds and returns an available TCP port.
- start_file_server(database_path: str, database_callback: Optional[callable] = None,
                      csv_callback: Optional[callable] = None, debug: bool = False) -> tuple:
        Starts a WSGI server for file uploads and downloads.
- main(): Example usage and testing of the file server.
"""
import socketserver
import threading
import os
import uuid
import shutil
import json
import enum
import io
from wsgiref.simple_server import make_server
from typing import Optional


@enum.unique
class FileType(enum.Enum):
    """
    Enumeration representing file types.

    Members:
    - Database: Represents a database file ('db').
    - CSV: Represents a CSV file ('csv').
    """
    Database = 'db'
    CSV = 'csv'


# SAFE Circular Imports (Duplicated class again)
@enum.unique
class Action(enum.Enum):
    """
    Enumeration representing various actions that can be performed.

    Members:
    - CREATE: Represents the creation action ('CREATE').
    - TRACK: Represents the tracking action ('TRACK').
    - LOG: Represents the logging action ('LOG').
    - SUBTRACT: Represents the subtract action ('SUBTRACT').
    - ADD_FILE: Represents the action of adding a file ('ADD_FILE').
    - REMOVE_FILE: Represents the action of removing a file ('REMOVE_FILE').
    - BOX_TRANSFER: Represents the action of transferring a box ('BOX_TRANSFER').
    - EXCHANGE: Represents the exchange action ('EXCHANGE').
    - REPORT: Represents the reporting action ('REPORT').
    - ZAKAT: Represents a Zakat related action ('ZAKAT').
    """
    CREATE = 'CREATE'
    TRACK = 'TRACK'
    LOG = 'LOG'
    SUBTRACT = 'SUBTRACT'
    ADD_FILE = 'ADD_FILE'
    REMOVE_FILE = 'REMOVE_FILE'
    BOX_TRANSFER = 'BOX_TRANSFER'
    EXCHANGE = 'EXCHANGE'
    REPORT = 'REPORT'
    ZAKAT = 'ZAKAT'


def find_available_port() -> int:
    """
    Finds and returns an available TCP port on the local machine.

    This function utilizes a TCP server socket to bind to port 0, which
    instructs the operating system to automatically assign an available
    port. The assigned port is then extracted and returned.

    Returns:
    - int: The available TCP port number.

    Raises:
    - OSError: If an error occurs during the port binding process, such
            as all ports being in use.

    Example:
    ```python
    port = find_available_port()
    print(f"Available port: {port}")
    ```
    """
    with socketserver.TCPServer(("localhost", 0), None) as s:
        return s.server_address[1]


def start_file_server(database_path: str, database_callback: Optional[callable] = None, csv_callback: Optional[callable] = None,
                      debug: bool = False) -> tuple:
    """
    Starts a multi-purpose WSGI server to manage file interactions for a Zakat application.

    This server facilitates the following functionalities:

    1. GET `/{file_uuid}/get`: Download the database file specified by `database_path`.
    2. GET `/{file_uuid}/upload`: Display an HTML form for uploading files.
    3. POST `/{file_uuid}/upload`: Handle file uploads, distinguishing between:
        - Database File (.db): Replaces the existing database with the uploaded one.
        - CSV File (.csv): Imports data from the CSV into the existing database.

    Parameters:
    - database_path (str): The path to the camel database file.
    - database_callback (callable, optional): A function to call after a successful database upload.
                                                It receives the uploaded database path as its argument.
    - csv_callback (callable, optional): A function to call after a successful CSV upload. It receives the uploaded CSV path,
                                           the database path, and the debug flag as its arguments.
    - debug (bool, optional): If True, print debugging information. Defaults to False.

    Returns:
    - Tuple[str, str, str, threading.Thread, Callable[[], None]]: A tuple containing:
        - file_name (str): The name of the database file.
        - download_url (str): The URL to download the database file.
        - upload_url (str): The URL to access the file upload form.
        - server_thread (threading.Thread): The thread running the server.
        - shutdown_server (Callable[[], None]): A function to gracefully shut down the server.

    Example:
    ```python
    _, download_url, upload_url, server_thread, shutdown_server = start_file_server("zakat.db")
    print(f"Download database: {download_url}")
    print(f"Upload files: {upload_url}")
    server_thread.start()
    # ... later ...
    shutdown_server()
    ```
    """
    file_uuid = uuid.uuid4()
    file_name = os.path.basename(database_path)

    port = find_available_port()
    download_url = f"http://localhost:{port}/{file_uuid}/get"
    upload_url = f"http://localhost:{port}/{file_uuid}/upload"

    # Upload directory
    upload_directory = "./uploads"
    os.makedirs(upload_directory, exist_ok=True)

    # HTML templates
    upload_form = f"""
    <html lang="en">
        <head>
            <title>Zakat File Server</title>
        </head>
    <body>
    <h1>Zakat File Server</h1>
    <h3>You can download the <a target="__blank" href="{download_url}">database file</a>...</h3>
    <h3>Or upload a new file to restore a database or import `CSV` file:</h3>
    <form action="/{file_uuid}/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" required><br/>
        <input type="radio" id="{FileType.Database.value}" name="upload_type" value="{FileType.Database.value}" required>
        <label for="database">Database File</label><br/>
        <input type="radio"id="{FileType.CSV.value}" name="upload_type" value="{FileType.CSV.value}">
        <label for="csv">CSV File</label><br/>
        <input type="submit" value="Upload"><br/>
    </form>
    </body></html>
    """

    # WSGI application
    def wsgi_app(environ, start_response):
        path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', 'GET')

        if path == f"/{file_uuid}/get" and method == 'GET':
            # GET: Serve the existing file
            try:
                with open(database_path, "rb") as f:
                    file_content = f.read()
                    
                start_response('200 OK', [
                    ('Content-type', 'application/octet-stream'),
                    ('Content-Disposition', f'attachment; filename="{file_name}"'),
                    ('Content-Length', str(len(file_content)))
                ])
                return [file_content]
            except FileNotFoundError:
                start_response('404 Not Found', [('Content-type', 'text/plain')])
                return [b'File not found']
                
        elif path == f"/{file_uuid}/upload" and method == 'GET':
            # GET: Serve the upload form
            start_response('200 OK', [('Content-type', 'text/html')])
            return [upload_form.encode()]
            
        elif path == f"/{file_uuid}/upload" and method == 'POST':
            # POST: Handle file uploads
            try:
                # Get content length
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                
                # Get content type and boundary
                content_type = environ.get('CONTENT_TYPE', '')
                
                # Read the request body
                request_body = environ['wsgi.input'].read(content_length)
                
                # Create a file-like object from the request body
                # request_body_file = io.BytesIO(request_body)
                
                # Parse the multipart form data using WSGI approach
                # First, detect the boundary from content_type
                boundary = None
                for part in content_type.split(';'):
                    part = part.strip()
                    if part.startswith('boundary='):
                        boundary = part[9:]
                        if boundary.startswith('"') and boundary.endswith('"'):
                            boundary = boundary[1:-1]
                        break
                
                if not boundary:
                    start_response('400 Bad Request', [('Content-type', 'text/plain')])
                    return [b"Missing boundary in multipart form data"]
                
                # Process multipart data
                parts = request_body.split(f'--{boundary}'.encode())
                
                # Initialize variables to store form data
                upload_type = None
                # file_item = None
                file_data = None
                filename = None
                
                # Process each part
                for part in parts:
                    if not part.strip():
                        continue
                    
                    # Split header and body
                    try:
                        headers_raw, body = part.split(b'\r\n\r\n', 1)
                        headers_text = headers_raw.decode('utf-8')
                    except ValueError:
                        continue
                    
                    # Parse headers
                    headers = {}
                    for header_line in headers_text.split('\r\n'):
                        if ':' in header_line:
                            name, value = header_line.split(':', 1)
                            headers[name.strip().lower()] = value.strip()
                    
                    # Get content disposition
                    content_disposition = headers.get('content-disposition', '')
                    if not content_disposition.startswith('form-data'):
                        continue
                    
                    # Extract field name
                    field_name = None
                    for item in content_disposition.split(';'):
                        item = item.strip()
                        if item.startswith('name='):
                            field_name = item[5:].strip('"\'')
                            break
                    
                    if not field_name:
                        continue
                    
                    # Handle upload_type field
                    if field_name == 'upload_type':
                        # Remove trailing data including the boundary
                        body_end = body.find(b'\r\n--')
                        if body_end >= 0:
                            body = body[:body_end]
                        upload_type = body.decode('utf-8').strip()
                    
                    # Handle file field
                    elif field_name == 'file':
                        # Extract filename
                        for item in content_disposition.split(';'):
                            item = item.strip()
                            if item.startswith('filename='):
                                filename = item[9:].strip('"\'')
                                break
                        
                        if filename:
                            # Remove trailing data including the boundary
                            body_end = body.find(b'\r\n--')
                            if body_end >= 0:
                                body = body[:body_end]
                            file_data = body
                
                if debug:
                    print('upload_type', upload_type)
                    
                if debug:
                    print('upload_type:', upload_type)
                    print('filename:', filename)
                
                if not upload_type or upload_type not in [FileType.Database.value, FileType.CSV.value]:
                    start_response('400 Bad Request', [('Content-type', 'text/plain')])
                    return [b"Invalid upload type"]
                
                if not filename or not file_data:
                    start_response('400 Bad Request', [('Content-type', 'text/plain')])
                    return [b"Missing file data"]
                
                if debug:
                    print(f'Uploaded filename: {filename}')
                
                # Save the file
                file_path = os.path.join(upload_directory, upload_type)
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                # Process based on file type
                if upload_type == FileType.Database.value:
                    try:
                        # Verify database file
                        if database_callback is not None:
                            database_callback(file_path)
                        
                        # Copy database into the original path
                        shutil.copy2(file_path, database_path)
                        
                        start_response('200 OK', [('Content-type', 'text/plain')])
                        return [b"Database file uploaded successfully."]
                    except Exception as e:
                        start_response('400 Bad Request', [('Content-type', 'text/plain')])
                        return [str(e).encode()]
                
                elif upload_type == FileType.CSV.value:
                    try:
                        if csv_callback is not None:
                            result = csv_callback(file_path, database_path, debug)
                            if debug:
                                print(f'CSV imported: {result}')
                            if len(result[2]) != 0:
                                start_response('200 OK', [('Content-type', 'application/json')])
                                return [json.dumps(result).encode()]
                        
                        start_response('200 OK', [('Content-type', 'text/plain')])
                        return [b"CSV file uploaded successfully."]
                    except Exception as e:
                        start_response('400 Bad Request', [('Content-type', 'text/plain')])
                        return [str(e).encode()]
            
            except Exception as e:
                start_response('500 Internal Server Error', [('Content-type', 'text/plain')])
                return [f"Error processing upload: {str(e)}".encode()]
        
        else:
            # 404 for anything else
            start_response('404 Not Found', [('Content-type', 'text/plain')])
            return [b'Not Found']
    
    # Create and start the server
    httpd = make_server('localhost', port, wsgi_app)
    server_thread = threading.Thread(target=httpd.serve_forever)
    
    def shutdown_server():
        nonlocal httpd, server_thread
        httpd.shutdown()
        server_thread.join()  # Wait for the thread to finish
    
    return file_name, download_url, upload_url, server_thread, shutdown_server


def main():
    from zakat_tracker import ZakatTracker, Action  # SAFE Circular Imports
    # Example usage (replace with your file path)
    file_to_share = f"{uuid.uuid4()}.{ZakatTracker.ext()}"  # Or any other file type

    def database_callback(file_path):
        ZakatTracker(db_path=file_path)

    def csv_callback(file_path, database_path, debug):
        x = ZakatTracker(db_path=database_path)
        return x.import_csv(file_path, debug=debug)

    file_name, download_url, upload_url, server_thread, shutdown_server = start_file_server(
        file_to_share,
        database_callback=database_callback,
        csv_callback=csv_callback,
        debug=True,
    )

    print(f"\nTo download '{file_name}', use this URL:")
    print(download_url)

    print(f"\nTo upload a new '{file_name}', use this URL:")
    print(upload_url)
    print("(The uploaded file will replace the existing one.)")

    print("\nStarting the server...")
    server_thread.start()
    print("The server started.")

    input("\nPress Enter to stop the server...")
    shutdown_server()


if __name__ == "__main__":
    main()