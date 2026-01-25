import socket
import time
from datetime import datetime

# ================= CONFIG =================
# Inspection Pi3B
PI3_HOST = "192.168.1.102"
PI3_PORT = 23001        

# Robot PC
ROBOT_HOST = "192.168.1.103"
ROBOT_PORT = 24020

# Safety Pi
SAFETY_HOST = "192.168.1.101"
SAFETY_PORT = 23011

# VR
VR_HOST = "192.168.1.4"
VR_PORT = 25050

DELIMITER = b"\nEND\n"
LOG_FILE = "uc4b_tcpip_rtt_log.csv"
# =========================================


def recv_until(sock, delimiter):
    buf = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Socket closed")
        buf.extend(chunk)
        idx = buf.find(delimiter)
        if idx != -1:
            return bytes(buf[:idx])


def recv_line(sock):
    buf = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Socket closed")
        buf.extend(chunk)
        nl = buf.find(b"\n")
        if nl != -1:
            return buf[:nl].decode().strip()


def log_rtt(rtt_ms):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()},{rtt_ms:.3f}\n")


def uc4b_once():
    # ================= TRIGGER =================
    t_start = time.perf_counter()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_pi3:
        s_pi3.connect((PI3_HOST, PI3_PORT))
        s_pi3.sendall(b"TRIGGER\n")

        payload = recv_until(s_pi3, DELIMITER)

    dimensions, image_bytes = payload.split(b"\n", 1)

    # ================= ROBOT =================
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_robot:
        s_robot.connect((ROBOT_HOST, ROBOT_PORT))
        s_robot.sendall(dimensions + b"\n" + image_bytes + DELIMITER)
        contour = recv_line(s_robot)  # "true" or "false"

    # ================= SAFETY =================
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_safety:
        s_safety.connect((SAFETY_HOST, SAFETY_PORT))
        s_safety.sendall((contour + "\n").encode())
        counter = recv_line(s_safety)

    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_vr:
        s_vr.connect((VR_HOST, VR_PORT))
        s_vr.sendall((counter + "\n").encode())
        echo = recv_line(s_vr)

    
    t_end = time.perf_counter()
    rtt_ms = (t_end - t_start) * 1000
    log_rtt(rtt_ms)

    print(f"[UC4b TCP] RTT={rtt_ms:.2f} ms | contour={contour} | counter={counter}")


if __name__ == "__main__":
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,rtt_ms\n")

    while True:
        try:
            uc4b_once()
            time.sleep(0.5)   # on-demand / operator-driven
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Error:", e)
            time.sleep(1)
