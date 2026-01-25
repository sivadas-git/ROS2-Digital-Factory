import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SafetyCounterNode(Node):
    def __init__(self):
        super().__init__('safety_counter_node')

        # Initialize counter with a starting value of 10
        self.counter = 0

        # ROS2 Subscription to /contour
        self.contour_subscription = self.create_subscription(
            String,
            '/contour',
            self.contour_callback,
            10
        )

        # ROS2 Publisher for /counter
        self.counter_publisher = self.create_publisher(
            String,
            '/counter',
            10
        )

        self.get_logger().info("Safety Counter Node initialized with counter = 0.")

    def contour_callback(self, msg):
        """
        Callback to process messages from the /contour topic.
        Updates the counter based on the contour status.
        """
        contour_result = msg.data.lower()  # Expecting "true" or "false"
        self.get_logger().info(f"Received contour result: {contour_result}")

        if contour_result == "true":
            self.counter += 1  # Increment counter if contour is true
            self.get_logger().info("Contour detected. Incremented counter.")
        else:
            self.counter += 0
            self.get_logger().info("No contour detected. Counter unchanged.")

        # Publish the updated counter to /counter
        self.publish_counter()

    def publish_counter(self):
        """
        Publishes the current counter value to the /counter topic.
        """
        counter_message = String()
        counter_message.data = str(self.counter)
        self.counter_publisher.publish(counter_message)
        self.get_logger().info(f"Published counter: {self.counter}")


def main(args=None):
    rclpy.init(args=args)
    safety_counter_node = SafetyCounterNode()

    try:
        rclpy.spin(safety_counter_node)
    except KeyboardInterrupt:
        safety_counter_node.get_logger().info("Node interrupted by user.")
    finally:
        safety_counter_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()