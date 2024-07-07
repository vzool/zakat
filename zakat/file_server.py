import http.server
import socketserver
import threading
import os
import uuid
import cgi
from enum import Enum, auto
import shutil
import json


class FileType(Enum):
    Database = 'db'
    CSV = 'csv'


# SAFE Circular Imports (Duplicated class again)
class Action(Enum):
    CREATE = auto()
    TRACK = auto()
    LOG = auto()
    SUB = auto()
    ADD_FILE = auto()
    REMOVE_FILE = auto()
    BOX_TRANSFER = auto()
    EXCHANGE = auto()
    REPORT = auto()
    ZAKAT = auto()


def find_available_port() -> int:
    """
    Finds and returns an available TCP port on the local machine.

    This function utilizes a TCP server socket to bind to port 0, which
    instructs the operating system to automatically assign an available
    port. The assigned port is then extracted and returned.

    Returns:
        int: The available TCP port number.

    Raises:
        OSError: If an error occurs during the port binding process, such
            as all ports being in use.

    Example:
        port = find_available_port()
        print(f"Available port: {port}")
    """
    with socketserver.TCPServer(("localhost", 0), None) as s:
        return s.server_address[1]


def start_file_server(database_path: str, database_callback: callable = None, csv_callback: callable = None,
                      debug: bool = False) -> tuple:
    """
    Starts a multi-purpose HTTP server to manage file interactions for a Zakat application.

    This server facilitates the following functionalities:

    1. GET /{file_uuid}/get: Download the database file specified by `database_path`.
    2. GET /{file_uuid}/upload: Display an HTML form for uploading files.
    3. POST /{file_uuid}/upload: Handle file uploads, distinguishing between:
        - Database File (.db): Replaces the existing database with the uploaded one.
        - CSV File (.csv): Imports data from the CSV into the existing database.

    Args:
        database_path (str): The path to the pickle database file.
        database_callback (callable, optional): A function to call after a successful database upload.
                                                It receives the uploaded database path as its argument.
        csv_callback (callable, optional): A function to call after a successful CSV upload. It receives the uploaded CSV path,
                                           the database path, and the debug flag as its arguments.
        debug (bool, optional): If True, print debugging information. Defaults to False.

    Returns:
        Tuple[str, str, str, threading.Thread, Callable[[], None]]: A tuple containing:
            - file_name (str): The name of the database file.
            - download_url (str): The URL to download the database file.
            - upload_url (str): The URL to access the file upload form.
            - server_thread (threading.Thread): The thread running the server.
            - shutdown_server (Callable[[], None]): A function to gracefully shut down the server.

    Example:
        _, download_url, upload_url, server_thread, shutdown_server = start_file_server("zakat.db")
        print(f"Download database: {download_url}")
        print(f"Upload files: {upload_url}")
        server_thread.start()
        # ... later ...
        shutdown_server()
    """
    file_uuid = uuid.uuid4()
    file_name = os.path.basename(database_path)

    port = find_available_port()
    download_url = f"http://localhost:{port}/{file_uuid}/get"
    upload_url = f"http://localhost:{port}/{file_uuid}/upload"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == f"/{file_uuid}/get":
                # GET: Serve the existing file
                try:
                    with open(database_path, "rb") as f:
                        self.send_response(200)
                        self.send_header("Content-type", "application/octet-stream")
                        self.send_header("Content-Disposition", f'attachment; filename="{file_name}"')
                        self.end_headers()
                        self.wfile.write(f.read())
                except FileNotFoundError:
                    self.send_error(404, "File not found")
            elif self.path == f"/{file_uuid}/upload":
                # GET: Serve the upload form
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f"""
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
                """.encode())
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path == f"/{file_uuid}/upload":
                # POST: Handle request
                # 1. Get the Form Data
                form_data = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                upload_type = form_data.getvalue("upload_type")

                if debug:
                    print('upload_type', upload_type)

                if upload_type not in [FileType.Database.value, FileType.CSV.value]:
                    self.send_error(400, "Invalid upload type")
                    return

                # 2. Extract File Data
                file_item = form_data['file']  # Assuming 'file' is your file input name

                # 3. Get File Details
                filename = file_item.filename
                file_data = file_item.file.read()  # Read the file's content

                if debug:
                    print(f'Uploaded filename: {filename}')

                # 4. Define Storage Path for CSV
                upload_directory = "./uploads"  # Create this directory if it doesn't exist
                os.makedirs(upload_directory, exist_ok=True)
                file_path = os.path.join(upload_directory, upload_type)

                # 5. Write to Disk
                with open(file_path, 'wb') as f:
                    f.write(file_data)

                match upload_type:
                    case FileType.Database.value:

                        try:
                            # 6. Verify database file
                            # ZakatTracker(db_path=file_path) # FATAL, Circular Imports Error
                            if database_callback is not None:
                                database_callback(file_path)

                            # 7. Copy database into the original path
                            shutil.copy2(file_path, database_path)
                        except Exception as e:
                            self.send_error(400, str(e))
                            return

                    case FileType.CSV.value:
                        # 6. Verify CSV file
                        try:
                            # x = ZakatTracker(db_path=database_path) # FATAL, Circular Imports Error
                            # result = x.import_csv(file_path, debug=debug)
                            if csv_callback is not None:
                                result = csv_callback(file_path, database_path, debug)
                                if debug:
                                    print(f'CSV imported: {result}')
                                if len(result[2]) != 0:
                                    self.send_response(200)
                                    self.end_headers()
                                    self.wfile.write(json.dumps(result).encode())
                                    return
                        except Exception as e:
                            self.send_error(400, str(e))
                            return

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"File uploaded successfully.")

    httpd = socketserver.TCPServer(("localhost", port), Handler)
    server_thread = threading.Thread(target=httpd.serve_forever)

    def shutdown_server():
        nonlocal httpd, server_thread
        httpd.shutdown()
        httpd.server_close()  # Close the socket
        server_thread.join()  # Wait for the thread to finish

    return file_name, download_url, upload_url, server_thread, shutdown_server


def main():
    from zakat_tracker import ZakatTracker, Action  # SAFE Circular Imports
    # Example usage (replace with your file path)
    file_to_share = f"{uuid.uuid4()}.pickle"  # Or any other file type

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

    print("\nString the server...")
    server_thread.start()
    print("The server started.")

    input("\nPress Enter to stop the server...")
    shutdown_server()


if __name__ == "__main__":
    main()
