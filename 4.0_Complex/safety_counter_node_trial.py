import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ---------------- CONFIG ----------------
CONTOUR_TOPIC = "/contour"      # published by image_processing_node (Robot PC)
COUNTER_TOPIC = "/counter"      # consumed by counter_listener_node (Central PC)
# ---------------------------------------


class SafetyCounterNode(Node):
    """
    UC4b Safety Counter Node (Safety Pi):
    - Subscribes to /contour (String: "true"/"false" or "True"/"False")
    - Increments an internal counter ONLY when contour is detected
    - Publishes /counter (String integer) whenever it increments
    """

    def __init__(self):
        super().__init__("safety_counter_node")

        self.counter = 0

        self.counter_pub = self.create_publisher(String, COUNTER_TOPIC, 50)
        self.contour_sub = self.create_subscription(
            String, CONTOUR_TOPIC, self.contour_callback, 50
        )

        self.get_logger().info(
            f"SafetyCounterNode started. Subscribing {CONTOUR_TOPIC}, publishing {COUNTER_TOPIC}."
        )

    def contour_callback(self, msg: String):
        val = msg.data.strip().lower()

        # Accept common truthy values
        contour_detected = val in ("true", "1", "yes", "y", "t")

        if contour_detected:
            self.counter += 1
            out = String()
            out.data = str(self.counter)
            self.counter_pub.publish(out)
            self.get_logger().info(f"Contour detected -> counter incremented to {self.counter}")
        else:
            # No contour -> no increment. Silence to avoid spamming.
            pass


def main(args=None):
    rclpy.init(args=args)
    node = SafetyCounterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
