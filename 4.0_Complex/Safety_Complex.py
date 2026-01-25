import RPi.GPIO as GPIO
import socket
from time import sleep, time
from datetime import datetime
from threading import Thread, Lock

# Initialize GPIO pins
DARK_CHANNEL, BRIGHT_CHANNEL, SPEAKER_CHANNEL = 19, 20, 26
GPIO.setmode(GPIO.BCM)
GPIO.setup([DARK_CHANNEL, BRIGHT_CHANNEL, SPEAKER_CHANNEL], GPIO.IN)
GPIO.setwarnings(False)

# Establish TCP connection to MSI-YAP (for sensor data)
HOST, PORT = "192.168.1.5", 23001
sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sensor_socket.connect((HOST, PORT))

# Server configuration for listening to MSI-YAP messages
LISTEN_HOST = "192.168.1.101"  # Replace with Pi4-Safety's IP
LISTEN_PORT = 23011

counter = 0 

# Log file
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = "Log_Safety_Def_Dev_" + str(now)

# Shared counter and lock for thread-safe operations
counter = 0
lock = Lock()

def log_data(message):
    """Log data with timestamp to a file."""
    with open(filename, 'a') as log_file:
        log_file.write(f"{datetime.now()}, {message}\n")

def communicate_and_measure_rtt(sensor_data):
    """Send sensor data to server and measure RTT."""
    send_time = time()
    sensor_socket.sendall(sensor_data.encode('utf-8'))
    response = sensor_socket.recv(1024).decode('utf-8')
    rtt = time() - send_time
    log_data(f"{sensor_data}, {rtt}")  # in seconds

def handle_msi_yap_connection(conn):
    """Handle incoming messages (true/false) from MSI-YAP."""
    global counter
    try:
        while True:
            # Receive message from MSI-YAP
            message = conn.recv(1024).decode("utf-8").strip()
            if not message:
                break

            print(f"Received from MSI-YAP: {message}")
            log_data(f"Received from MSI-YAP: {message}")

            with lock:
                if message == "true":
                    counter += 1  # Increment counter
                # Reply with the current counter value
                conn.sendall(f"{counter}".encode("utf-8") + b"\n")
                print(f"Replied to MSI-YAP: {counter}")
                log_data(f"Replied to MSI-YAP: {counter}")

    except Exception as e:
        print(f"Error handling MSI-YAP connection: {e}")
    finally:
        conn.close()

def listen_for_msi_yap():
    """Start a server to listen for incoming true/false messages from MSI-YAP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((LISTEN_HOST, LISTEN_PORT))
            server_socket.listen(5)
            print(f"Listening for MSI-YAP on {LISTEN_HOST}:{LISTEN_PORT}")

            while True:
                conn, addr = server_socket.accept()
                print(f"Connection established with MSI-YAP: {addr}")
                Thread(target=handle_msi_yap_connection, args=(conn,), daemon=True).start()

    except Exception as e:
        print(f"Error starting server for MSI-YAP: {e}")

try:
    # Start thread to listen for MSI-YAP messages
    Thread(target=listen_for_msi_yap, daemon=True).start()

    while True:
        # Read sensor states
        light_state = (
            "dark" if GPIO.input(DARK_CHANNEL) else
            "bright" if GPIO.input(BRIGHT_CHANNEL) else
            "none"
        )
        sound_state = GPIO.input(SPEAKER_CHANNEL)
        sensor_data = f"{light_state},{sound_state}"
        print(sensor_data)
        log_data(sensor_data)

        # Communicate sensor states and measure RTT
        communicate_and_measure_rtt(sensor_data)
        

finally:
    sensor_socket.close()
    GPIO.cleanup()
