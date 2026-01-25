import socket
from threading import Thread, Lock
import time

YAP_HOST = '192.168.1.5'
YAP_PORT = 28009

SIVA_HOST = '192.168.1.4'
SIVA_PORT = 23009

def recv_line(sock: socket.socket, buf: bytearray) -> str:
    while True:
        nl = buf.find(b"\n")
        if nl != -1:
            line = buf[:nl].decode("utf-8", errors="replace")
            del buf[:nl+1]
            return line
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Socket closed while waiting for newline")
        buf.extend(chunk)

class PersistentVR:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.buf = bytearray()
        self.lock = Lock()

    def connect(self):
        self.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.connect((self.host, self.port))
        self.sock = s
        self.buf = bytearray()

    def close(self):
        if self.sock:
            try: self.sock.close()
            except: pass
        self.sock = None
        self.buf = bytearray()

    def send_and_echo(self, line: str) -> str:
        with self.lock:
            if self.sock is None:
                self.connect()

            msg = (line.rstrip("\n") + "\n").encode("utf-8")
            try:
                self.sock.sendall(msg)
                return recv_line(self.sock, self.buf)
            except Exception:
                # reconnect once
                time.sleep(0.2)
                self.connect()
                self.sock.sendall(msg)
                return recv_line(self.sock, self.buf)

vr = PersistentVR(SIVA_HOST, SIVA_PORT)

def handle_robot_connection(robot_socket, address):
    print(f"Robot connected from {address}")
    rx_buf = bytearray()
    try:
        while True:
            line = recv_line(robot_socket, rx_buf)  # one angles message
            echoed = vr.send_and_echo(line)         # forward to VR and get echo
            robot_socket.sendall((echoed + "\n").encode("utf-8"))
    except Exception as e:
        print(f"Robot connection error {address}: {e}")
    finally:
        try:
            robot_socket.close()
        except:
            pass
        print(f"Closed robot connection {address}")

def start_yap_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((YAP_HOST, YAP_PORT))
    server_socket.listen(5)
    print(f"MSI-YAP server listening on {YAP_HOST}:{YAP_PORT}")

    try:
        while True:
            robot_socket, address = server_socket.accept()
            Thread(target=handle_robot_connection, args=(robot_socket, address), daemon=True).start()
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_yap_server()
