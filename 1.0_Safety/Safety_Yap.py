import socket

# Device -> YAP
HOST_PC_TWO = '192.168.1.5'
PORT_PC_ONE_TO_TWO = 23001

# YAP -> Unity (VR)
HOST_PC_THREE = '192.168.1.4'
PORT_PC_TWO_TO_THREE = 23002

def recv_line_bytes(sock: socket.socket, buf: bytearray) -> bytes:
    """Receive one newline-terminated line (bytes without newline)."""
    while True:
        nl = buf.find(b"\n")
        if nl != -1:
            line = bytes(buf[:nl])
            del buf[:nl + 1]
            return line
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Socket closed while waiting for newline")
        buf.extend(chunk)

class UnityClient:
    """Persistent client to Unity; reconnect once on failure."""
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self.buf = bytearray()

    def connect(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.connect((self.host, self.port))
        self.buf = bytearray()

    def send_and_wait_echo(self, line_bytes: bytes) -> bytes:
        if not self.sock:
            self.connect()
        try:
            self.sock.sendall(line_bytes + b"\n")
            return recv_line_bytes(self.sock, self.buf)
        except Exception:
            # reconnect once
            self.connect()
            self.sock.sendall(line_bytes + b"\n")
            return recv_line_bytes(self.sock, self.buf)

unity = UnityClient(HOST_PC_THREE, PORT_PC_TWO_TO_THREE)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST_PC_TWO, PORT_PC_ONE_TO_TWO))
    server_socket.listen()
    print(f"[YAP TCP] Forwarder listening on {HOST_PC_TWO}:{PORT_PC_ONE_TO_TWO}")

    while True:
        conn, addr = server_socket.accept()
        print(f"[YAP TCP] Connected from {addr}")
        conn_buf = bytearray()

        with conn:
            while True:
                try:
                    line = recv_line_bytes(conn, conn_buf)  # bytes without '\n'
                except ConnectionError:
                    print("[YAP TCP] Client disconnected")
                    break

                echoed = unity.send_and_wait_echo(line)

                try:
                    conn.sendall(echoed + b"\n")
                except Exception:
                    print("[YAP TCP] Failed to send echo upstream")
                    break
