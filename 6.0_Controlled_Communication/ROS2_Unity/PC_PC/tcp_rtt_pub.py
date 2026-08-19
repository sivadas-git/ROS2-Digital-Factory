import rclpy
from rclpy.node import Node
import socket
import time
import json
import uuid
import csv
from datetime import datetime
import os
import threading


class TCPRTTPublisherLogger(Node):
    def __init__(self):
        super().__init__('tcpip')

        self.host = self.declare_parameter('host', '192.168.1.4').get_parameter_value().string_value
        self.port = self.declare_parameter('port', 32101).get_parameter_value().integer_value
        self.rate = self.declare_parameter('rate', 10.0).get_parameter_value().double_value

        self.sent_times = {}  # {msg_id: timestamp}
        self.lock = threading.Lock()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(None)  # blocking recv, handled in thread

        self.filename = self._init_log_file()

        try:
            self.socket.connect((self.host, self.port))
            self.get_logger().info(f"Connected to TCP echo server at {self.host}:{self.port}")
        except Exception as e:
            self.get_logger().error(f"TCP connection failed: {e}")
            raise e

        # Create ROS2 timer for sending
        self.timer = self.create_timer(1.0 / self.rate, self.send_message)
        self.get_logger().info(f"TCP RTT Publisher started at {self.rate} Hz on port {self.port}")

        # Start receive thread
        self.receiver_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receiver_thread.start()

        # Start timeout checker thread
        self.timeout_thread = threading.Thread(target=self.check_timeouts_loop, daemon=True)
        self.timeout_thread.start()

    def _init_log_file(self):
        start_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/home/robot/robot_ws/src/new_logs/tcp_rtt_log_port_{self.port}_{start_time_str}.csv"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_now", "msg_id", "rtt_seconds"])
        return filename

    def send_message(self):
        try:
            msg_id = str(uuid.uuid4())
            timestamp = time.time()
            payload = json.dumps({"id": msg_id, "timestamp": timestamp})
            self.socket.sendall(payload.encode('utf-8') + b"\n")

            # Only track msg_id if send was successful
            with self.lock:
                self.sent_times[msg_id] = timestamp

        except Exception as e:
            self.get_logger().warn(f"Send error: {e}")

    def receive_loop(self):
        buffer = ""
        while rclpy.ok():
            try:
                data = self.socket.recv(1024).decode('utf-8')
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self.process_reply(line.strip())
            except Exception as e:
                self.get_logger().warn(f"Receive error: {e}")
                time.sleep(0.1)

    def process_reply(self, data_str):
        try:
            echo = json.loads(data_str)
            msg_id = echo.get("id", "")
            now = time.time()

            with self.lock:
                if msg_id in self.sent_times:
                    sent_time = self.sent_times.pop(msg_id)
                    rtt = now - sent_time
                    self.get_logger().info(f"RTT for {msg_id}: {rtt:.6f} seconds")
                    with open(self.filename, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([now, msg_id, round(rtt, 6)])
                else:
                    self.get_logger().warn(f"Received unmatched msg_id: {msg_id}")
        except Exception as e:
            self.get_logger().warn(f"Error processing reply: {e}")

    def check_timeouts_loop(self):
        while rclpy.ok():
            now = time.time()
            expired_ids = []

            with self.lock:
                for msg_id, ts in list(self.sent_times.items()):
                    if now - ts > 2.0:
                        expired_ids.append(msg_id)

                for msg_id in expired_ids:
                    self.sent_times.pop(msg_id, None)
                    self.get_logger().warn(f"Timeout: No reply for message {msg_id}")
                    with open(self.filename, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([now, msg_id, "timeout"])

            time.sleep(0.5)


def main(args=None):
    rclpy.init(args=args)
    node = TCPRTTPublisherLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
