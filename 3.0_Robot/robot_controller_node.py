import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pymycobot import MyCobot280
import time
import threading
from datetime import datetime

class RobotControllerNode(Node):
    def __init__(self):
        super().__init__('robot_controller_node')

        # Initialize MyCobot
        self.mc = MyCobot280("/dev/ttyUSB0")

        # Publisher for /robot_coordinates
        self.publisher = self.create_publisher(String, '/robot_coordinates', 120)

        # Logging configuration
        self.log_file = "mycobot_rtt_log.txt"
        self.rest = 2

        # Start publishing angles periodically
        self.create_timer(0.008, self.read_and_publish_angles)  # Publish angles at ~10Hz

        # Start the movement sequence in a separate thread
        self.movement_thread = None
        self.start_movement_sequence()

        self.get_logger().info("Robot Controller Node initialized")

    def start_movement_sequence(self):
        """Starts a thread to run the full sequence continuously."""
        if self.movement_thread is None or not self.movement_thread.is_alive():
            self.movement_thread = threading.Thread(target=self.full_sequence, daemon=True)
            self.movement_thread.start()

    def full_sequence(self):
        """Execute a full movement sequence and restart upon completion."""
        while True:
            try:
                self.get_logger().info("Starting full sequence")
                self.home()
                self.get_logger().info("At home")
                self.movement_1()
                self.get_logger().info("Movement 1 completed")
                # Uncomment the next lines if Movement 2 is required
                # self.movement_2()
                # self.get_logger().info("Movement 2 completed")
            except Exception as e:
                self.get_logger().error(f"Error in sequence: {e}")
                break  # Stop if there's an error

    def home(self):
        """Move MyCobot to the home position."""
        self.mc.send_angles([0, 0, 0, 0, 0, 0], 20)
        time.sleep(self.rest)
        self.get_logger().info("Moved to home position")

    def movement_1(self):
        """Execute the first movement sequence."""
        self.get_logger().info("Starting Movement 1")
        self.mc.send_angles([30, 60, 30, 30, 120, 30], 20)
        time.sleep(self.rest)
        self.mc.send_angles([-30, -60, -30, -30, -120, -30], 20)
        time.sleep(self.rest)
        self.get_logger().info("Movement 1 completed")

    def movement_2(self):
        """Execute the second movement sequence."""
        self.get_logger().info("Starting Movement 2")
        self.mc.send_angles([90, 90, 10, -150.04, 150.01, -32.34], 30)
        time.sleep(self.rest)
        self.mc.send_angles([-1.66, -6.06, 96.15, -147.04, 177.18, -48.6], 30)
        time.sleep(self.rest)
        self.get_logger().info("Movement 2 completed")

    def read_and_publish_angles(self):
        """Reads the robot's current joint angles and publishes them to /robot_coordinates."""
        try:
            angles = self.mc.get_angles()
            if angles:
                angles_data = ','.join(map(str, angles))
                msg = String()
                msg.data = angles_data
                self.publisher.publish(msg)
                self.get_logger().info(f"Published coordinates: {angles_data}")
        except Exception as e:
            self.get_logger().error(f"Error reading or publishing angles: {e}")

def main(args=None):
    rclpy.init(args=args)
    robot_controller_node = RobotControllerNode()

    try:
        rclpy.spin(robot_controller_node)
    except KeyboardInterrupt:
        robot_controller_node.get_logger().info("Node interrupted by user")
    finally:
        robot_controller_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
