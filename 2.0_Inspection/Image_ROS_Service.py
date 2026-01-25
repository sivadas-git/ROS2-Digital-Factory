import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import socket
import numpy as np
import cv2
# from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy


class ImageProcessRequestNode(Node):
    def __init__(self):
        super().__init__('image_process_request_node')

        # ROS2 Service
        self.srv = self.create_service(Trigger, '/image_process_request_service', self.handle_request)

        # ROS2 Publishers
        self.image_publisher = self.create_publisher(Image, '/processed_image', 100)
        self.dimensions_publisher = self.create_publisher(String, '/image_dimensions', 100)

        # TCP Configuration
        self.tcp_host = "192.168.1.7"  # Pi3B IP
        self.tcp_port = 23007
        self.bridge = CvBridge()

        self.get_logger().info("Image Process Request Node is ready.")

    def handle_request(self, request, response):
        self.get_logger().info("Received 'capture' request. Forwarding to Pi3B...")

        try:
            # Connect to Pi3B's TCP server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((self.tcp_host, self.tcp_port))
                client_socket.sendall(b"capture")

                # Receive dimensions
                dimensions = client_socket.recv(1024).decode('utf-8').strip()
                self.get_logger().info(f"Received dimensions from Pi3B: {dimensions}")

                # Publish dimensions
                self.dimensions_publisher.publish(String(data=dimensions))

                # Receive image size
                image_size_str = client_socket.recv(1024).decode('utf-8').strip()
                image_size = int(image_size_str)
                self.get_logger().info(f"Image size: {image_size} bytes")

                # Receive image data
                image_data = b''
                while len(image_data) < image_size:
                    packet = client_socket.recv(8192)
                    if not packet:
                        break
                    image_data += packet
                self.get_logger().info(f"Image fully received")

                # Decode and publish the image
                np_arr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if image is None:
                    self.get_logger().error("Failed to decode image")
                    response.success = False
                    response.message = "Failed to decode image"
                    return response

                ros_image = self.bridge.cv2_to_imgmsg(image, encoding="bgr8")
                self.get_logger().info("image converted")
                self.image_publisher.publish(ros_image)
                self.get_logger().info("Published processed image and dimensions")

                # Respond to the service client with the dimensions
                response.success = True
                response.message = dimensions
                return response

        except Exception as e:
            self.get_logger().error(f"Failed to communicate with Pi3B: {e}")
            response.success = False
            response.message = f"Error: {str(e)}"
            return response


def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessRequestNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
