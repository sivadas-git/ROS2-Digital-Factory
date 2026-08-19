# file: tcpraw.py
import multiprocessing
import socket
import time
import uuid
import json
import csv
import os

def run_sender(index):
    port = 32101 + index
    host = '192.168.1.101'
    interval = 1.0 / 60  # 60Hz (adjustable)

    filename = f'/home/robot/robot_ws/src/new_logs/tcp_unity_baseline_{port}.csv'
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp_now', 'msg_id', 'rtt_seconds', 'status'])

        total_sent = 0
        received_count = 0
        loss_count = 0

        try:
            with socket.create_connection((host, port)) as s:
                s.settimeout(2.0)  # prevent hang on recv
                while True:
                    msg_id = str(uuid.uuid4())
                    t0 = time.time()
                    payload = json.dumps({'id': msg_id, 'timestamp': t0}) + '\n'

                    try:
                        s.sendall(payload.encode())
                        total_sent += 1

                        data = s.recv(1024).decode().strip()
                        t1 = time.time()

                        if not data:
                            loss_count += 1
                            writer.writerow([t1, msg_id, '', 'LOST'])
                            continue

                        received_count += 1
                        rtt = t1 - t0
                        writer.writerow([t1, msg_id, round(rtt, 6), 'OK'])
                        print(f"[Port {port}] RTT: {rtt:.6f}s")

                    except (socket.timeout, socket.error, json.JSONDecodeError) as e:
                        loss_count += 1
                        writer.writerow([time.time(), msg_id, '', 'ERROR'])
                        print(f"[Port {port}] Loss/Error: {e}")

                    f.flush()
                    time.sleep(interval)

        except Exception as e:
            print(f"[Port {port}] Connection error: {e}")

        print(f"[Port {port}] Completed. Sent: {total_sent}, Received: {received_count}, Lost: {loss_count}")

if __name__ == '__main__':
    procs = []
    for i in range(10):  # 10 parallel senders 
        p = multiprocessing.Process(target=run_sender, args=(i,))
        p.start()
        procs.append(p)

    for p in procs:
        p.join()
