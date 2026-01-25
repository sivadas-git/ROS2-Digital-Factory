import socket
import cv2
import numpy as np
from datetime import datetime

# Configuration
HOST = "192.168.1.7"  # Pi3B's IP
PORT = 23007          # Communication port
IMAGE_SAVE_PATH = "/home/sivadas/Images/raw/"
PROCESSED_IMAGE_PATH = "/home/sivadas/Images/processed/"
LOG_FILE_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"/home/sivadas//Images/log/inspection_log_{LOG_FILE_TIMESTAMP}.csv"

# Utility function for logging
def log_event(event, timestamp, duration=None, additional_info=""):
    with open(LOG_FILE, "a") as log_file:
        log_entry = f"{event},{timestamp},{duration if duration else ''},{additional_info}\n"
        log_file.write(log_entry)

# Function to capture and process an image
def capture_and_process_image():
    """
    Captures an image using a USB camera, processes it, and logs capture and processing times.
    """
    try:
        cap = cv2.VideoCapture(0)  # 0 is the index for the first USB camera
        capture_start = datetime.now()

        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("Failed to capture image.")
            return None, None

        capture_end = datetime.now()
        capture_duration = (capture_end - capture_start).total_seconds() * 1000
        log_event("Image Capture", capture_start, capture_duration)

        # Save the captured image
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        captured_image_path = f"{IMAGE_SAVE_PATH}captured_{now}.jpg"
        cv2.imwrite(captured_image_path, frame)

        # Process the image
        process_start = datetime.now()
        img_cropped = frame[0:900, 200:1240]  # Cropping the image
        img_gray = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.GaussianBlur(img_gray, (7, 7), 1)
        edges = cv2.Canny(img_blur, 20, 200)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        annotated_image = img_cropped.copy()
        dimensions = "No contours found"

        for cnt in contours:
            if cv2.contourArea(cnt) > 300:
                cv2.drawContours(annotated_image, [cnt], -1, (255, 0, 0), 2)
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(annotated_image, [box], 0, (0, 255, 0), 2)

                width, height = rect[1]
                dimensions = f"Width: {width:.2f}, Height: {height:.2f}"

                x, y = int(rect[0][0]), int(rect[0][1])
                
                cv2.putText(annotated_image, dimensions, (x - 50, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 0), 1, cv2.LINE_AA)
                break

        # Save the processed image
        processed_image_path = f"{PROCESSED_IMAGE_PATH}processed_{now}.jpg"
        cv2.imwrite(processed_image_path, annotated_image)

        process_end = datetime.now()
        process_duration = (process_end - process_start).total_seconds() * 1000
        log_event("Image Processing", process_start, process_duration)

        return annotated_image, dimensions

    except Exception as e:
        print(f"Error during image capture and processing: {e}")
        return None, None

# Function to handle client requests
def handle_client_connection(conn):
    try:
        # Receive command from MSI-YAP
        command = conn.recv(1024).decode("utf-8").strip()
        if command == "capture":
            print("Capture command received, processing image...")
            
            annotated_image, dimensions = capture_and_process_image()
            print (dimensions)
            if annotated_image is None:
                conn.sendall(b"Error: Image capture failed.")
            else:
                # Send processed image dimensions and image to MSI-YAP
                dimensions_str = f"{dimensions}"
                conn.sendall(dimensions_str.encode("utf-8"))
                

                # Encode processed image to JPEG and send
                _, buffer = cv2.imencode(".jpg", annotated_image)
                image_size = len(buffer)
                conn.sendall(f"{image_size} \n".encode("utf-8"))
                conn.sendall(buffer.tobytes())
                print("Processed image and dimensions sent to MSI-YAP.")

                # Wait for echo reply
                echo_start = datetime.now()
                echo_reply = conn.recv(1024)
                echo_end = datetime.now()

                if echo_reply.decode("utf-8") == "echo_received":
                    round_trip_duration = (echo_end - echo_start).total_seconds() * 1000
                    log_event("Echo Reply", echo_end, round_trip_duration, "From MSI-YAP")
                else:
                    print("Unexpected echo reply received.")
    except Exception as e:
        print(f"Error handling client connection: {e}")
    finally:
        conn.close()

# Main server function
def main():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((HOST, PORT))
            server_socket.listen(5)
            print(f"Pi3B server running on {HOST}:{PORT}, waiting for connections...")

            # Initialize log file
            with open(LOG_FILE, "w") as log_file:
                log_file.write("Event,Timestamp,Duration(ms),Additional Info\n")

            while True:
                conn, addr = server_socket.accept()
                print(f"Connection established with {addr}")
                handle_client_connection(conn)
    except KeyboardInterrupt:
        print("Server shutting down...")
    except Exception as e:
        print(f"Error in main server function: {e}")

if __name__ == "__main__":
    main()
