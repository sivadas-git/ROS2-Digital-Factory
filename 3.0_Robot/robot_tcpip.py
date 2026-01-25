import time
import socket
from threading import Thread
from pymycobot import MyCobot280
from datetime import datetime

mc = MyCobot280("/dev/ttyUSB0")

LOG_FILE = "mycobot_rtt_log.txt"
rest = 2

def log_rtt(sent_message, rtt):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{timestamp} - Message: {sent_message} - RTT: {rtt:.6f} seconds\n")

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

def home():
    mc.send_angles([0, 0, 0, 0, 0, 0], 20)
    time.sleep(rest)

def movement_1():
    mc.send_angles([30, 60, 30, 30, 120, 30], 20)
    time.sleep(rest)
    mc.send_angles([-30, -60, -30, -30, -120, -30], 20)
    time.sleep(rest)

def full_sequence():
    while True:
        try:
            home()
            movement_1()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in sequence: {e}")
            break

def read_and_send_angles():
    print("Angle reading and RTT measurement started")

    server_ip = "192.168.1.5"
    server_port = 28009

    rx_buf = bytearray()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        client_socket.connect((server_ip, server_port))
        print(f"Connected to MSI-YAP at {server_ip}:{server_port}")

        while True:
            try:
                angles = mc.get_angles()
                if angles:
                    angles_data = ','.join(map(str, angles))

                    t0 = time.perf_counter()
                    client_socket.sendall((angles_data + "\n").encode('utf-8'))

                    response = recv_line(client_socket, rx_buf)  # newline-framed reply
                    t1 = time.perf_counter()

                    rtt = t1 - t0
                    log_rtt(angles_data, rtt)
                    print(f"Sent: {angles_data}, Received: {response}, RTT: {rtt:.6f} s")

                # optional pacing:
                # time.sleep(0.05)  # ~20Hz
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error reading/sending angles: {e}")
                break

    except Exception as e:
        print(f"Failed to connect to MSI-YAP: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass
        print("Connection closed")

if __name__ == "__main__":
    try:
        t1 = Thread(target=full_sequence, daemon=True)
        t2 = Thread(target=read_and_send_angles, daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        pass
