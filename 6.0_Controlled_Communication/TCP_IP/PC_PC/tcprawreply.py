import socket
import threading
import json

BASE_PORT = 32101
HOST = '0.0.0.0'  # listen on all interfaces

def handle_client(conn, addr, port):
    print(f"[Port {port}] Connection from {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                msg = data.decode().strip()
                try:
                    obj = json.loads(msg)
                    conn.sendall((json.dumps(obj) + '\n').encode())
                except json.JSONDecodeError:
                    print(f"[Port {port}] Invalid JSON: {msg}")
            except Exception as e:
                print(f"[Port {port}] Error: {e}")
                break
    print(f"[Port {port}] Disconnected {addr}")

def start_server(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, port))
        s.listen()
        print(f"[Port {port}] Echo server listening...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr, port), daemon=True).start()

def launch_echo_receivers(num_ports):
    for i in range(num_ports):
        port = BASE_PORT + i
        threading.Thread(target=start_server, args=(port,), daemon=True).start()
    print(f"Started {num_ports} echo servers on ports {BASE_PORT} to {BASE_PORT + num_ports - 1}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_ports', type=int, default=10, help='Number of echo ports to open starting from 32101')
    args = parser.parse_args()

    launch_echo_receivers(args.num_ports)

    try:
        while True:
            pass  # keep main thread alive
    except KeyboardInterrupt:
        print("Shutting down servers.")
