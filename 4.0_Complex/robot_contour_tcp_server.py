import socket
import cv2
import numpy as np

# =========================
# CONFIG (Robot PC)
# =========================
ROBOT_HOST = "0.0.0.0"
ROBOT_PORT = 24020           
DELIMITER = b"\nEND\n"        # must match Central sender
MIN_CONTOUR_AREA = 300        # keep consistent with your ROS contour logic


def recv_until(sock: socket.socket, delimiter: bytes, max_bytes: int = 50_000_000) -> bytes:
    """Receive data until delimiter appears; returns payload (delimiter removed)."""
    buf = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Socket closed before delimiter received")
        buf.extend(chunk)

        if len(buf) > max_bytes:
            raise ValueError("Payload too large (framing error / wrong delimiter)")

        idx = buf.find(delimiter)
        if idx != -1:
            return bytes(buf[:idx])  # exclude delimiter


def detect_contour(image_bytes: bytes) -> bool:
    """Decode JPEG/PNG bytes and run simple contour detection."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return False

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) > MIN_CONTOUR_AREA:
            return True
    return False


def handle_client(conn: socket.socket, addr):
    try:
        payload = recv_until(conn, DELIMITER)

        # payload format: b"<dimensions>\\n<image bytes>"
        if b"\n" in payload:
            dims_line, image_bytes = payload.split(b"\n", 1)
            dims_text = dims_line.decode("utf-8", errors="replace")
        else:
            dims_text = ""
            image_bytes = payload

        contour_found = detect_contour(image_bytes)

        # OPTIONAL: trigger robot action here if contour_found
        # e.g., call your robot driver / motion code

        reply = "true\n" if contour_found else "false\n"
        conn.sendall(reply.encode("utf-8"))

        print(f"[RobotContour] {addr} contour={contour_found} dims='{dims_text[:80]}'")

    except Exception as e:
        print(f"[RobotContour] Error handling {addr}: {e}")
        try:
            conn.sendall(b"false\n")
        except:
            pass
    finally:
        try:
            conn.close()
        except:
            pass


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((ROBOT_HOST, ROBOT_PORT))
    server.listen(5)
    print(f"[RobotContour] Listening on {ROBOT_HOST}:{ROBOT_PORT}")

    while True:
        conn, addr = server.accept()
        handle_client(conn, addr)


if __name__ == "__main__":
    main()
