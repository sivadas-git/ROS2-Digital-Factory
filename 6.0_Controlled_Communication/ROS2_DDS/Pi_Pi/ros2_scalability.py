# Step 1: Updated ros2_scalability.py with sent tracker
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time
import json
import uuid

class RTTMessagePublisher(Node):
    def __init__(self):
        super().__init__('ros2_scalability_publisher')

        # Parameters
        self.topic = self.declare_parameter('topic', 'rtt_test_topic').get_parameter_value().string_value
        self.rate = self.declare_parameter('rate', 10.0).get_parameter_value().double_value

        # Sent tracking topic
        self.sent_topic = self.topic.replace('rtt_test_topic', 'rtt_sent')

        # Reliable QoS
        qos_profile = rclpy.qos.QoSProfile(depth=10, reliability=rclpy.qos.ReliabilityPolicy.RELIABLE)

        # Publishers
        self.publisher_ = self.create_publisher(String, self.topic, qos_profile)
        self.sent_logger_ = self.create_publisher(String, self.sent_topic, qos_profile)

        # Timer
        self.timer = self.create_timer(1.0 / self.rate, self.publish_message)

        self.get_logger().info(f"Publishing to {self.topic} at {self.rate} Hz")
        self.get_logger().info(f"Sent log publishing to {self.sent_topic}")

    def publish_message(self):
        msg_id = str(uuid.uuid4())
        timestamp = time.time()
        payload = {"id": msg_id, "timestamp": timestamp}

        msg = String()
        msg.data = json.dumps(payload)

        self.publisher_.publish(msg)
        self.sent_logger_.publish(msg)  # Send to rtt_sent_X


def main(args=None):
    rclpy.init(args=args)
    node = RTTMessagePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
