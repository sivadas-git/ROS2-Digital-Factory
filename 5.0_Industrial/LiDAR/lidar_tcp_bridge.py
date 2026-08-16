#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
import socket
import time

class LidarTCPBridge(Node):
    def __init__(self):
        super().__init__('lidar_tcp_bridge')

        # Unity server settings
        self.unity_ip = '192.168.1.4'  # Replace with your Unity PC IP
        self.unity_port = 31003          # Set Unity port for LiDAR (separate from UR10)

        self.sock = None
        self.connect_to_unity()

        # Subscribe to processed obstacle status
        self.subscription = self.create_subscription(
            Bool,
            '/lidar/obstacle_status',
            self.listener_callback,
            10
        )

        self.get_logger().info("LiDAR TCP client bridge node started.")

    def connect_to_unity(self):
        """Establish TCP connection to Unity server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.unity_ip, self.unity_port))
            self.get_logger().info(f"Connected to Unity at {self.unity_ip}:{self.unity_port}")
        except Exception as e:
            self.get_logger().error(f" Failed to connect to Unity: {e}")
            self.sock = None

    def listener_callback(self, msg: Bool):
        if not self.sock:
            self.get_logger().warn("Unity connection not active. Retrying...")
            self.connect_to_unity()
            if not self.sock:
                return

        try:
            payload = ("True" if msg.data else "False") + "\n"
            self.sock.sendall(payload.encode('utf-8'))
            self.get_logger().info(f"Sent to Unity: {payload.strip()}")
        except Exception as e:
            self.get_logger().error(f"Send failed: {e}")
            self.sock.close()
            self.sock = None

def main(args=None):
    rclpy.init(args=args)
    node = LidarTCPBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
