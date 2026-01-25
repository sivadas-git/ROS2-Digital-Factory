import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import uuid
import time

# Topics (keep simple and explicit)
TOPIC_IN_COORDS = "/robot_coordinates"        # from robot_controller_node
TOPIC_OUT_TO_CENTRAL = "/robot_to_central_out" # to MSI-YAP bridge
TOPIC_IN_ECHO = "/robot_echo_back"            # from MSI-YAP bridge (echoed)
TOPIC_OUT_RTT = "/robot_rtt_result"           # to robot_to_siva logger


class RobotToCentral(Node):
    """
    Robot PC comms node (ROS2):
      - subscribes to /robot_coordinates (angles)
      - attaches UUID, sends to central via /robot_to_central_out
      - receives echo (UUID;angles) from /robot_echo_back
      - computes RTT locally (perf_counter)
      - publishes RTT result to /robot_rtt_result for logging by robot_to_siva
    """

    def __init__(self):
        super().__init__("robot_to_central")

        self.pub_to_central = self.create_publisher(String, TOPIC_OUT_TO_CENTRAL, 200)
        self.pub_rtt = self.create_publisher(String, TOPIC_OUT_RTT, 200)

        self.sub_coords = self.create_subscription(String, TOPIC_IN_COORDS, self.on_coords, 200)
        self.sub_echo = self.create_subscription(String, TOPIC_IN_ECHO, self.on_echo, 200)

        # uuid -> (t_start, angles_str)
        self.pending = {}

        # Optional: avoid flooding if robot_controller publishes very fast
        # Set to None to allow max rate.
        self.min_send_interval_s = 0.0  # set e.g. 0.0167 for ~60Hz cap, or 0.0 for uncapped
        self._last_send_t = 0.0

        self.get_logger().info("robot_to_central started.")

    def on_coords(self, msg: String):
        angles_str = msg.data.strip()
        if not angles_str:
            return

        # Optional pacing
        now = time.perf_counter()
        if self.min_send_interval_s > 0.0 and (now - self._last_send_t) < self.min_send_interval_s:
            return
        self._last_send_t = now

        msg_id = str(uuid.uuid4())
        payload = f"{msg_id};{angles_str}"

        # Record RTT start time at source (Robot PC)
        self.pending[msg_id] = (time.perf_counter(), angles_str)

        out = String()
        out.data = payload
        self.pub_to_central.publish(out)

    def on_echo(self, msg: String):
        data = msg.data.strip()
        if ";" not in data:
            return
        echoed_id, echoed_angles = data.split(";", 1)

        if echoed_id not in self.pending:
            # echo for unknown/expired id
            return

        t0, sent_angles = self.pending.pop(echoed_id)
        rtt_ms = (time.perf_counter() - t0) * 1000.0

        # Publish to logger node (robot_to_siva)
        # Format: uuid;rtt_ms;angles
        out = String()
        out.data = f"{echoed_id};{rtt_ms:.6f};{echoed_angles}"
        self.pub_rtt.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = RobotToCentral()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
