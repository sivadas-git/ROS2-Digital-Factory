import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import socket
import time
from datetime import datetime
import os
import cv2

# -----------------------------
# Configuration (kept consistent with your original)
# -----------------------------
PI4_HOST = "192.168.1.102"   # (not strictly needed for ROS service discovery, kept as-is)
SIVA_HOST = "192.168.1.4"    # MSI-Siva / VR host
SIVA_PORT = 23008            # Port for communication with MSI-Siva / VR
LOG_FILE = "/home/vboxuser/Desktop/Inspection/Log/inspection_yap_log.txt"
IMAGE_SAVE_PATH = "/home/vboxuser/Desktop/Inspection/Images"
DELIMITER = b"\nEND\n"

SERVICE_NAME = "/image_process_request_service"
TOPIC_IMAGE = "/processed_image"
TOPIC_DIM = "/image_dimensions"


class MSIYAPClientNode(Node):
    """
    UC2 (ROS2) Initiator Node (YAP/Central-PC role):
      - Triggers image capture/processing via ROS2 Trigger service (RPC, on-demand)
      - Waits for /processed_image and /image_dimensions
      - Forwards to VR (MSI-Siva) over TCP
      - Waits for VR echo ('echo_received')
      - Computes end-to-end RTT at THIS node only and logs ONE RTT line to disk
    """

    def __init__(self):
        super().__init__('msi_yap_client_node')

        # Tools
        self.bridge = CvBridge()
        self.received_image = None
        self.received_dimensions = None

        # ROS2 Subscribers (same topic names)
        self.image_sub = self.create_subscription(
            Image, TOPIC_IMAGE, self.image_callback, 100
        )
        self.dimensions_sub = self.create_subscription(
            String, TOPIC_DIM, self.dimensions_callback, 100
        )

        # ROS2 Service Client
        self.client = self.create_client(Trigger, SERVICE_NAME)

        # Ensure directories exist
        os.makedirs(IMAGE_SAVE_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

        self.get_logger().info("MSI-YAP Client Node initialized (UC2 ROS2 RPC).")

    # -----------------------------
    # Main on-demand workflow
    # -----------------------------
    def run_once(self):
        """
        Runs one complete UC2 cycle:
          1) call ROS service (Trigger)
          2) wait for topics
          3) forward to VR
          4) wait echo
          5) compute RTT and log
        """
        # Wait for service availability
        while not self.client.wait_for_service(timeout_sec=5.0):
            self.get_logger().warn(f"Waiting for service {SERVICE_NAME}...")

        # Reset any stale data from previous executions
        self.received_image = None
        self.received_dimensions = None

        # RTT start (initiator-side)
        rtt_start = time.perf_counter()
        self.get_logger().info("Sending inspection request (Trigger service)...")

        # Call service (RPC / on-demand)
        request = Trigger.Request()
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        # Validate service response
        if future.result() is None or not future.result().success:
            self.get_logger().error("Service call failed.")
            return

        self.get_logger().info(f"Service response: {future.result().message}")

        # Wait for image + dimensions via topics (published by the service node)
        self.get_logger().info("Waiting for /processed_image and /image_dimensions ...")
        while self.received_image is None or self.received_dimensions is None:
            rclpy.spin_once(self, timeout_sec=0.2)

        # Save received image
        image_path = self.save_received_image()
        if not image_path:
            self.get_logger().error("Failed to save received image.")
            return

        # Forward to VR and wait for echo
        ok = self.forward_to_siva(image_path, self.received_dimensions)
        if not ok:
            self.get_logger().error("Forwarding to VR failed or echo not received.")
            return

        # RTT end
        rtt_end = time.perf_counter()
        rtt_ms = (rtt_end - rtt_start) * 1000.0

        # RTT-only log (one line per trigger)
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now()}, UC2_ROS2_RTT_ms={rtt_ms:.3f}\n")

        self.get_logger().info(f"UC2 ROS2 RTT: {rtt_ms:.3f} ms (logged to {LOG_FILE})")

    # -----------------------------
    # Helpers
    # -----------------------------
    def save_received_image(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(IMAGE_SAVE_PATH, f"received_{timestamp}.jpg")

            cv_image = self.bridge.imgmsg_to_cv2(self.received_image, desired_encoding='bgr8')
            cv2.imwrite(image_path, cv_image)

            self.get_logger().info(f"Image saved to {image_path}")
            return image_path

        except Exception as e:
            self.get_logger().error(f"Error saving image: {e}")
            return None

    def forward_to_siva(self, image_path, dimensions):
        """
        Sends: dimensions + newline + image bytes + DELIMITER
        Expects: 'echo_received' from VR server
        """
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as siva_socket:
                self.get_logger().info(f"Connecting to VR at {SIVA_HOST}:{SIVA_PORT}...")
                siva_socket.connect((SIVA_HOST, SIVA_PORT))

                dimensions_encoded = dimensions.encode("utf-8")
                data_to_send = dimensions_encoded + b"\n" + image_data + DELIMITER
                siva_socket.sendall(data_to_send)

                siva_reply = siva_socket.recv(1024).decode("utf-8", errors="replace").strip()
                if siva_reply == "echo_received":
                    self.get_logger().info("Echo reply received from VR.")
                    return True

                self.get_logger().error(f"Unexpected reply from VR: '{siva_reply}'")
                return False

        except Exception as e:
            self.get_logger().error(f"Error forwarding to VR: {e}")
            return False

    # -----------------------------
    # Topic callbacks
    # -----------------------------
    def image_callback(self, msg):
        self.received_image = msg

    def dimensions_callback(self, msg):
        self.received_dimensions = msg.data


def main(args=None):
    rclpy.init(args=args)
    node = MSIYAPClientNode()

    try:
        # Run exactly once (on-demand RPC workflow)
        node.run_once()
    except KeyboardInterrupt:
        node.get_logger().info("MSI-YAP Client Node shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
