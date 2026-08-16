#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
from rclpy.qos import qos_profile_sensor_data
import math

class LidarObstacleDetector(Node):
    def __init__(self):
        super().__init__('lidar_obstacle_detector')

        # Parameters
        self.threshold_distance = 2.0  # meters
        self.angle_range_deg = 15.0    # degrees to each side of center
        self.angle_range_rad = math.radians(self.angle_range_deg)

        # Publisher: Boolean result of obstacle check
        self.obstacle_pub = self.create_publisher(Bool, '/lidar/obstacle_status', 10)

        # Subscriber: LaserScan from LiDAR
        self.subscription = self.create_subscription(
            LaserScan,
            '/pf/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )

        self.get_logger().info("LidarObstacleDetector started. Monitoring frontal zone ±15°.")

    def scan_callback(self, msg: LaserScan):
        obstacle_detected = False

        for i, distance in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment

            if abs(angle) <= self.angle_range_rad and 0.01 < distance < self.threshold_distance:
                obstacle_detected = True
                self.get_logger().info(
                    f"⚠️ Obstacle at {distance:.2f} m, angle {math.degrees(angle):.1f}°")
                break

        msg_out = Bool()
        msg_out.data = obstacle_detected
        self.obstacle_pub.publish(msg_out)

def main(args=None):
    rclpy.init(args=args)
    node = LidarObstacleDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
