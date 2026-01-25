import socket
from datetime import datetime
import os

# Configuration
PI3B_HOST = "192.168.1.7"   # Pi3B's IP
PI3B_PORT = 23007           # Port for communication with Pi3B
SIVA_HOST = "192.168.1.4"  # MSI-Siva's IP
SIVA_PORT = 23008           # Port for communication with MSI-Siva
LOG_FILE_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"/home/vboxuser/Desktop/Inspection/Log/inspection_yap_log_complete.txt"
IMAGE_SAVE_PATH = f"/home/vboxuser/Desktop/Inspection/Images"
DELIMITER = b"\nEND\n" 

# Utility function for logging
def log_event(event, timestamp, duration=None, additional_info=""):
    with open(LOG_FILE, "a") as log_file:
        log_entry = f"{event},{timestamp},{duration if duration else ''},{additional_info}\n"
        log_file.write(log_entry)

# Send request to Pi3B and process response
def request_capture_from_pi3b():
    rtt_start = datetime.now()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as pi3b_socket:
            print(f"Connecting to Pi3B at {PI3B_HOST}:{PI3B_PORT}...")
            pi3b_socket.connect((PI3B_HOST, PI3B_PORT))

            # Log request sent time
            request_start = datetime.now()
            log_event("Request Sent to Pi3B", request_start)

            # Send the capture command
            pi3b_socket.sendall(b"capture")

            # Receive dimensions and image
            dimensions = pi3b_socket.recv(1024).decode("utf-8")
            image_size = int(pi3b_socket.recv(1024).decode("utf-8").strip())
            image_data = b""
            while len(image_data) < image_size:
                chunk = pi3b_socket.recv(4096)
                if not chunk:
                    break
                image_data += chunk
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(IMAGE_SAVE_PATH, f"received_{timestamp}.jpg")
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
            print(f"Image saved to {image_path}")

            # Log when the image is fully received
            image_received_time = datetime.now()
            log_event("Image Received from Pi3B", image_received_time, additional_info=dimensions)

            print(f"Dimensions received: {dimensions}")
            print("Image data received. Forwarding to MSI-Siva...")

            # Forward the data to MSI-Siva
            forward_start = datetime.now()
            # forward_to_siva(image_data, dimensions)
            forward_to_siva(image_data,dimensions)
            forward_end = datetime.now()
            forward_duration = (forward_end - forward_start).total_seconds() * 1000
            log_event("Data Forwarded to MSI-Siva", forward_start, forward_duration)

            # Wait for echo reply from MSI-Siva
            siva_reply_time = datetime.now()
            log_event("Echo Reply from MSI-Siva", siva_reply_time)

            # Send echo reply back to Pi3B
            pi3b_socket.sendall(b"echo_received")
            print("Echo reply sent to Pi3B.")

            rtt_end = datetime.now()
            total_rtt = (rtt_end - rtt_start).total_seconds() * 1000  # Convert to ms
            log_event("RTT Measured", rtt_end, total_rtt, "Total Round-Trip Time")

    except Exception as e:
        print(f"Error communicating with Pi3B: {e}")

# Forward data to MSI-Siva
# def forward_to_siva(image_data, dimensions):

def forward_to_siva(image_data,dimensions):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as siva_socket:
            print(f"Connecting to MSI-Siva at {SIVA_HOST}:{SIVA_PORT}...")
            siva_socket.connect((SIVA_HOST, SIVA_PORT))

            # Send dimensions and image data
            dimensions_encoded = dimensions.encode("utf-8")
            separator = b"\n"
            data_to_send = dimensions_encoded + separator + image_data + DELIMITER
            # siva_socket.sendall(f"{len(dimensions_encoded)}\n".encode("utf-8"))
            # siva_socket.sendall(dimensions_encoded)

            image_size = len(image_data)
            print ("image size = " + str(image_size))
            # siva_socket.sendall(f"{image_size}\n".encode("utf-8"))
            siva_socket.sendall(data_to_send)

            # Wait for echo reply from MSI-Siva
            siva_reply = siva_socket.recv(1024).decode("utf-8")
            if siva_reply == "echo_received":
                print("Echo reply received from MSI-Siva.")
            else:
                print("Unexpected reply from MSI-Siva.")

    except Exception as e:
        print(f"Error forwarding to MSI-Siva: {e}")

# Main function
def main():
    try:
        print("MSI-YAP client starting...")
        # Initialize log file
        with open(LOG_FILE, "a") as log_file:
            log_file.write("Event,Timestamp,Duration(ms),Additional Info\n")

        # Request capture from Pi3B
        request_capture_from_pi3b()

    except KeyboardInterrupt:
        print("Client shutting down...")
    except Exception as e:
        print(f"Error in main function: {e}")

if __name__ == "__main__":
    main()
