import RPi.GPIO as GPIO
import socket
import uuid
import queue
import threading
import time
from time import time as wall_time  # keep your original 'time()' usage if you want
from datetime import datetime

# Initialize GPIO pins (UNCHANGED)
DARK_CHANNEL, BRIGHT_CHANNEL, SPEAKER_CHANNEL = 19, 20, 26
GPIO.setmode(GPIO.BCM)
GPIO.setup([DARK_CHANNEL, BRIGHT_CHANNEL, SPEAKER_CHANNEL], GPIO.IN)
GPIO.setwarnings(False)

# Establish TCP connection to MSI-YAP (UNCHANGED names)
HOST, PORT = "192.168.1.5", 23001
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
s.connect((HOST, PORT))

# Log file setup (UNCHANGED names)
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = "Log_Safety_Def_Dev_" + str(now)

# -----------------------------
# Buffered logging (flush at 10 Hz)
# -----------------------------
log_q = queue.Queue(maxsize=200000)
stop_evt = threading.Event()

def _logger_thread_fn(path: str, flush_hz: float = 10.0):
    period = 1.0 / flush_hz
    with open(path, 'a', buffering=1) as log_file:
        while not stop_evt.is_set():
            t_deadline = time.perf_counter() + period
            batch = []
            while True:
                try:
                    batch.append(log_q.get_nowait())
                except queue.Empty:
                    break
            if batch:
                log_file.write("\n".join(batch) + "\n")
            sleep_time = t_deadline - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)

threading.Thread(target=_logger_thread_fn, args=(filename, 10.0), daemon=True).start()

def log_data(message):
    """Log data with timestamp to a file. (Function name unchanged)"""
    try:
        log_q.put_nowait(f"{datetime.now()}, {message}")
    except queue.Full:
        # never block the RTT loop due to disk logging
        pass

# -----------------------------
# Newline framing (prevents partial recv issues)
# -----------------------------
_rx_buf = bytearray()

def _recv_line(sock: socket.socket) -> str:
    while True:
        nl = _rx_buf.find(b"\n")
        if nl != -1:
            line = _rx_buf[:nl].decode("utf-8", errors="replace")
            del _rx_buf[:nl+1]
            return line
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Socket closed while waiting for newline")
        _rx_buf.extend(chunk)

def communicate_and_measure_rtt(sensor_data):
    """
    Send sensor data with UUID; wait for echoed UUID; compute RTT at SOURCE ONLY.
    Function name unchanged.
    """
    msg_id = str(uuid.uuid4())
    payload = f"{msg_id};{sensor_data}\n"

    send_time = wall_time()
    s.sendall(payload.encode('utf-8'))
    response = _recv_line(s)  # expects "uuid;light,sound"
    rtt = wall_time() - send_time

    # Validate echo UUID
    echoed_id = response.split(";", 1)[0] if ";" in response else ""
    ok = (echoed_id == msg_id)

    # Log: keep your original style (seconds), but add UUID + ok flag
    log_data(f"{sensor_data}, uuid={msg_id}, echoed={echoed_id}, ok={ok}, rtt={rtt}")

try:
    PROBE_HZ = 10.0
    period = 1.0 / PROBE_HZ

    while True:
        # Read sensor states (UNCHANGED logic)
        light_state = 'dark' if GPIO.input(DARK_CHANNEL) else 'bright' if GPIO.input(BRIGHT_CHANNEL) else 'none'
        sound_state = GPIO.input(SPEAKER_CHANNEL)
        sensor_data = f"{light_state},{sound_state}"

        # Communicate sensor states and measure RTT
        t0 = time.perf_counter()
        communicate_and_measure_rtt(sensor_data)

        # Probe pacing (10 Hz)
        elapsed = time.perf_counter() - t0
        sleep_time = period - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

finally:
    stop_evt.set()
    try:
        s.close()
    except:
        pass
    GPIO.cleanup()
