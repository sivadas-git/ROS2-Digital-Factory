# echo_responder.py — single-topic echo responder (refactored from multi-topic version)
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class multi_topic_echo_responder(Node):
    def __init__(self):
        super().__init__('multi_topic_echo_responder')

        # Accept topic index to isolate per topic
        self.index = self.declare_parameter('topic_index', 0).get_parameter_value().integer_value

        self.topic_in = f"rtt_test_topic_{self.index}"
        self.topic_out = f"rtt_test_echo_{self.index}"

        qos_profile = rclpy.qos.QoSProfile(
            depth=10,
            reliability=rclpy.qos.ReliabilityPolicy.RELIABLE
        )

        self.publisher = self.create_publisher(String, self.topic_out, qos_profile)
        self.subscription = self.create_subscription(String, self.topic_in, self.callback, qos_profile)

        self.get_logger().info(f"[✓] Echo responder active: {self.topic_in} → {self.topic_out}")

    def callback(self, msg):
        try:
            self.publisher.publish(msg)
        except Exception as e:
            self.get_logger().warn(f"Echo failed on {self.topic_in}: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = multi_topic_echo_responder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
