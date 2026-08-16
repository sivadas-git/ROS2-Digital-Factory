#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
import socket

class LidarRTTClient(Node):
    def __init__(self):
        super().__init__('lidar_rtt_logger')

        self.server_ip = '192.168.1.4'  # Replace with Unity PC IP
        self.server_port = 31010
        self.obstacle_detected = False   # Default value

        # Subscriber to LiDAR obstacle detection topic
        self.subscriber = self.create_subscription(
            Bool,
            '/lidar/obstacle_status',  # Topic publishing LiDAR boolean output
            self.lidar_callback,
            10
        )

        self.get_logger().info("Subscribed to /pf/obstacle_detected")

        # Start the TCP client connection
        self.connect_and_respond()

    def lidar_callback(self, msg: Bool):
        self.obstacle_detected = msg.data

    def connect_and_respond(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_ip, self.server_port))
            self.get_logger().info(f"✅ Connected to Unity at {self.server_ip}:{self.server_port}")

            while rclpy.ok():
                data = sock.recv(128).decode('utf-8').strip()
                if data.startswith("REQ"):
                    # Compose and send reply
                    reply = f"{data}|{str(self.obstacle_detected)}\n"
                    sock.sendall(reply.encode('utf-8'))
                    self.get_logger().info(f"📤 Sent to Unity: {reply.strip()}")

        except Exception as e:
            self.get_logger().error(f" Error in TCP communication: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = LidarRTTClient()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
