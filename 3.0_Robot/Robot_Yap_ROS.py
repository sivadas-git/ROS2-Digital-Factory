import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import socket
import threading
import time

TOPIC_IN_FROM_ROBOT = "/robot_to_central_out"
TOPIC_OUT_TO_ROBOT = "/robot_echo_back"

SIVA_HOST = "192.168.1.4"
SIVA_PORT = 23009

RECONNECT_BACKOFF_S = 0.5  # reconnect delay on failure


def recv_line(sock: socket.socket, buf: bytearray) -> str:
    """Receive until newline; return line without newline."""
    while True:
        nl = buf.find(b"\n")
        if nl != -1:
            line = buf[:nl].decode("utf-8", errors="replace")
            del buf[:nl + 1]
            return line
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Socket closed while waiting for newline")
        buf.extend(chunk)


class PersistentVRClient:
    """
    Persistent TCP client to VR:
      - connect once, reuse socket
      - newline-framed request/echo
      - reconnect on failure
      - thread-safe send/recv via external lock
    """

    def __init__(self, host: str, port: int, logger):
        self.host = host
        self.port = port
        self.logger = logger

        self.sock: socket.socket | None = None
        self.buf = bytearray()

    def connect(self):
        self.close()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.connect((self.host, self.port))

        self.sock = s
        self.buf = bytearray()
        self.logger.info(f"[YAP] Connected to VR at {self.host}:{self.port}")

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except:
                pass
        self.sock = None
        self.buf = bytearray()

    def ensure_connected(self):
        if self.sock is None:
            self.connect()

    def send_and_wait_echo(self, payload: str) -> str:
        """
        Send one newline-framed message and wait for one newline-framed echo.
        If socket fails, reconnect once and retry.
        """
        msg_bytes = (payload.rstrip("\n") + "\n").encode("utf-8")

        self.ensure_connected()

        try:
            self.sock.sendall(msg_bytes)
            return recv_line(self.sock, self.buf)
        except Exception as e:
            self.logger.warn(f"[YAP] VR socket error: {e}. Reconnecting...")
            time.sleep(RECONNECT_BACKOFF_S)
            self.connect()
            self.sock.sendall(msg_bytes)
            return recv_line(self.sock, self.buf)


class RobotYapBridge(Node):
    """
    MSI-YAP bridge:
      /robot_to_central_out (ROS2) -> VR (persistent TCP, newline-framed) -> /robot_echo_back (ROS2)
    """

    def __init__(self):
        super().__init__("robot_yap_bridge_persistent")

        self.sub = self.create_subscription(String, TOPIC_IN_FROM_ROBOT, self.on_msg, 200)
        self.pub = self.create_publisher(String, TOPIC_OUT_TO_ROBOT, 200)

        # Persistent VR connection + lock to prevent interleaving send/recv
        self._io_lock = threading.Lock()
        self.vr = PersistentVRClient(SIVA_HOST, SIVA_PORT, self.get_logger())

        # Connect once at startup (optional). If VR isn't up yet, it will reconnect on first msg.
        try:
            self.vr.connect()
        except Exception as e:
            self.get_logger().warn(f"[YAP] Initial VR connect failed (will retry on demand): {e}")

        self.get_logger().info("robot_yap_bridge (persistent, newline-framed) started.")

    def on_msg(self, msg: String):
        payload = msg.data

        try:
            with self._io_lock:
                echoed_line = self.vr.send_and_wait_echo(payload)
        except Exception as e:
            self.get_logger().error(f"[YAP] Forward failed: {e}")
            return

        out = String()
        out.data = echoed_line  # "uuid;angles"
        self.pub.publish(out)

    def destroy_node(self):
        # clean shutdown
        try:
            with self._io_lock:
                self.vr.close()
        except:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RobotYapBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
