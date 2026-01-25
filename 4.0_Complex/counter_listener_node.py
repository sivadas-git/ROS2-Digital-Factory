import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import socket

# ---------------- CONFIG ----------------
VR_HOST = "192.168.1.4"   
VR_PORT = 25050            
# ---------------------------------------


class CounterListenerNode(Node):
    """
    UC4b Counter Listener (Central PC):
    - Subscribes to /counter (ROS2)
    - Forwards counter value to VR over TCP/IP (one-way, no echo)
    - No RTT logging (RTT is handled by UC1–UC3 sources)
    """
    def __init__(self):
        super().__init__('counter_listener_node')

        self.counter_sub = self.create_subscription(
            String, '/counter', self.counter_callback, 100
        )

        self.get_logger().info(
            f"CounterListenerNode started. Forwarding /counter -> VR {VR_HOST}:{VR_PORT} (TCP, no-echo)."
        )

    def counter_callback(self, msg: String):
        counter_value = msg.data.strip()
        if not counter_value:
            return

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((VR_HOST, VR_PORT))
                # newline-terminated for easy parsing on VR side
                s.sendall((counter_value + "\n").encode("utf-8"))
        except Exception as e:
            self.get_logger().error(f"Failed to send counter to VR: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = CounterListenerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
