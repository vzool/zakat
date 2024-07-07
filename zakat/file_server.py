import http.server
import socketserver
import threading
import os
import uuid
import cgi
from enum import Enum
from zakat_tracker import ZakatTracker, Action
import shutil
import json


class FileType(Enum):
    Database = 'db'
    CSV = 'csv'


def find_available_port():
    with socketserver.TCPServer(("localhost", 0), None) as s:
        return s.server_address[1]


def start_file_server(database_path: str, debug: bool = False):
    """
    Starts an HTTP server to serve a file (GET) and accept file uploads (POST) with UUID-based URIs.
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
                            ZakatTracker(db_path=file_path)

                            # 7. Copy database into the original path
                            shutil.copy2(file_path, database_path)
                        except Exception as e:
                            self.send_error(400, str(e))
                            return

                    case FileType.CSV.value:
                        # 6. Verify CSV file
                        try:
                            x = ZakatTracker(db_path=database_path)
                            result = x.import_csv(file_path, debug=debug)
                            if debug:
                                print(f'CSV imported: {result}')
                            if len(result[2]) != 0:
                                self.send_response(200)
                                self.end_headers()
                                self.wfile.write(json.dumps(result).encode())
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

    server_thread.start()

    return file_name, download_url, upload_url, shutdown_server


def main():
    # Example usage (replace with your file path)
    file_to_share = "your_file.txt"  # Or any other file type
    file_name, download_url, upload_url, shutdown_server = start_file_server(file_to_share, debug=True)

    print(f"\nTo download '{file_name}', use this URL:")
    print(download_url)

    print(f"\nTo upload a new '{file_name}', use this URL:")
    print(upload_url)
    print("(The uploaded file will replace the existing one.)")

    input("\nPress Enter to stop the server...")

    shutdown_server()


if __name__ == "__main__":
    main()
