import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
import cv2
import numpy as np
from rclpy.qos import QoSProfile, ReliabilityPolicy


class ImageProcessingNode(Node):
    def __init__(self):
        super().__init__('image_processing_node')

        # QoS Profile for reliable communication
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            depth=10  # Queue size
        )

        # ROS2 Subscriptions and Publishers
        self.image_subscription = self.create_subscription(
            CompressedImage,  # Updated to CompressedImage
            '/processed_image',
            self.image_callback,
            qos_profile
        )
        self.contour_publisher = self.create_publisher(String, '/contour', qos_profile)

        # OpenCV Bridge
        self.bridge = CvBridge()

        self.get_logger().info("Image Processing Node initialized and ready.")

    def image_callback(self, msg):
        """
        Callback function to process compressed images received on /processed_image.
        """
        self.get_logger().info("Received a compressed image. Starting processing...")

        try:
            # Decode the compressed image
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if cv_image is None:
                self.get_logger().error("Failed to decode compressed image.")
                return

            # Process the image to detect contours
            result = self.process_image(cv_image)

            # Publish the result to /contour
            self.publish_contour(result)

        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")

    def process_image(self, frame):
        """
        Processes the received image to detect dimensions.
        Returns True if dimensions are found, otherwise False.
        """
        try:
            # Example image processing pipeline
            img_cropped = frame[0:900, 200:1240]  # Cropping the image
            img_gray = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2GRAY)
            img_blur = cv2.GaussianBlur(img_gray, (7, 7), 1)
            edges = cv2.Canny(img_blur, 20, 200)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            # Check if dimensions are found
            for cnt in contours:
                if cv2.contourArea(cnt) > 300:
                    rect = cv2.minAreaRect(cnt)
                    width, height = rect[1]
                    dimensions = f"Width: {width:.2f}, Height: {height:.2f}"
                    self.get_logger().info(f"Dimensions found: {dimensions}")
                    return True

            # No dimensions found
            self.get_logger().info("No contours found.")
            return False

        except Exception as e:
            self.get_logger().error(f"Error during image processing: {e}")
            return False

    def publish_contour(self, result):
        """
        Publishes the contour result (true/false) to the /contour topic.
        """
        try:
            contour_result = "true" if result else "false"
            self.contour_publisher.publish(String(data=contour_result))
            self.get_logger().info(f"Published to /contour: {contour_result}")
        except Exception as e:
            self.get_logger().error(f"Error publishing contour: {e}")


def main(args=None):
    rclpy.init(args=args)
    image_processing_node = ImageProcessingNode()

    try:
        rclpy.spin(image_processing_node)
    except KeyboardInterrupt:
        image_processing_node.get_logger().info("Node interrupted by user.")
    finally:
        image_processing_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
