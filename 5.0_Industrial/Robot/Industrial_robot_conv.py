import socket

HOST = ''         # Listen on all interfaces
PORT = 30000      # Match port used in URP
END_MARKER = " END"

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Listening for UR10 on port {PORT}...")
        conn, addr = s.accept()
        print(f"Connected by {addr}")

        buffer = ""

        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data.decode()

                while END_MARKER in buffer:
                    # Split off one complete message
                    full_msg, buffer = buffer.split(END_MARKER, 1)
                    full_msg = full_msg.strip()

                    # ✅ Print the full, raw message exactly as sent
                    print(f"Received: {full_msg}")

                    # Optional: parse components
                    try:
                        parts = full_msg.split(',', 2)  # Only split first two commas
                        di0 = parts[0]
                        di4 = parts[1]
                        tcp_str = parts[2]
                        print(f"DI[0]: {di0}, DI[4]: {di4}, TCP: {tcp_str}")
                    except Exception as e:
                        print(f"⚠️ Parsing error: {e}")

if __name__ == '__main__':
    start_server()
