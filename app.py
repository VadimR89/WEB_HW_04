from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from threading import Thread
import urllib.parse
import pathlib
import mimetypes
import json
import socket

BASE_DIR = pathlib.Path()


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(200)
        self.send_header('Location', '/')
        self.end_headers()
        send_data_by_socket(data)

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        path = pr_url.path

        match path:
            case '/':
                self.index_html()
            case '/message':
                self.message_html()
            case _:
                if path:
                    file = BASE_DIR.joinpath(pr_url.path[1:])
                    if file.exists():
                        self.send_static(file)
                    else:
                        self.error_html()

    def send_static(self, file):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(file, 'rb') as f:
            self.wfile.write(f.read())

    def message_html(self):
        self.send_html_file('message.html')

    def error_html(self):
        self.send_html_file('error.html', status=404)

    def index_html(self):
        self.send_html_file('index.html')

    def send_html_file(self, filename, status=200):
        with open(filename, 'rb') as f:
            response_content = f.read()
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(response_content)))
        self.end_headers()
        self.wfile.write(response_content)


def send_data_by_socket(message):
    host = socket.gethostname()
    port = 5000

    client_socket = socket.socket()
    client_socket.connect((host, port))

    try:
        while True:
            client_socket.send(message)
            message = client_socket.recv(1024)
            if not message:
                break
    finally:
        client_socket.close()


def json_adapter(data) -> dict:
    data_parse = urllib.parse.unquote_plus(data.decode())
    data_dict = {datetime.now().strftime('%d/%m/%y %H:%M:%S.%f'): dict([el.split('=') for el in data_parse.split('&')
                                                                        if '=' in el])}
    return data_dict


def json_saver(data):
    with open(BASE_DIR.joinpath('storage/data.json'), 'r', encoding='utf-8') as f:
        loaded_dict = json.load(f)
    data_dict = json_adapter(data)
    loaded_dict.update(data_dict)
    with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as f:
        json.dump(loaded_dict, f, ensure_ascii=False)
        f.write('\n')


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    print('http server started')
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_socket_server():
    print('socket server started')
    host = socket.gethostname()
    port = 5000

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(1000)
    conn, address = server_socket.accept()
    print(f'Connection from {address}')
    while True:
        data = conn.recv(1024)
        json_saver(data)
        if not data:
            break
    conn.close()


if __name__ == '__main__':
    Thread_1 = Thread(target=run_socket_server)
    Thread_2 = Thread(target=run_http_server)
    Thread_1.start()
    Thread_2.start()
