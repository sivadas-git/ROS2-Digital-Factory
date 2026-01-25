import socket
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Keep names consistent with your earlier style
HOST_PC_THREE = '192.168.1.4'      # Unity / VR host
PORT_PC_TWO_TO_THREE = 23002       # Unity / VR port

def recv_line(sock: socket.socket, buf: bytearray) -> str:
    """Receive one newline-terminated UTF-8 line."""
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

class UnityClient:
    """Persistent client to Unity; reconnect once on failure."""
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self.buf = bytearray()

    def connect(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.connect((self.host, self.port))
        self.buf = bytearray()

    def send_and_wait_echo(self, payload: str) -> str:
        if not self.sock:
            self.connect()

        # Ensure newline framing
        msg = payload.strip("\n") + "\n"

        try:
            self.sock.sendall(msg.encode("utf-8"))
            return recv_line(self.sock, self.buf)
        except Exception:
            # reconnect once
            self.connect()
            self.sock.sendall(msg.encode("utf-8"))
            return recv_line(self.sock, self.buf)

class YapSafetyRosUnityBridge(Node):
    def __init__(self):
        super().__init__('yap_safety_ros_unity_bridge')

        # Topics (match your device ROS node)
        self.sub = self.create_subscription(String, 'safety_out', self.on_msg, 10)
        self.pub = self.create_publisher(String, 'safety_echo', 10)

        # Unity client
        self.unity = UnityClient(HOST_PC_THREE, PORT_PC_TWO_TO_THREE)

        self.get_logger().info("[YAP ROS] Bridge started. safety_out -> Unity -> safety_echo")

    def on_msg(self, msg: String):
        # Forward EXACT payload (do not modify UUID/payload)
        payload = msg.data

        try:
            echoed = self.unity.send_and_wait_echo(payload)
        except Exception as e:
            self.get_logger().error(f"[YAP ROS] Unity forward error: {e}")
            return

        out = String()
        out.data = echoed
        self.pub.publish(out)

def main(args=None):
    rclpy.init(args=args)
    node = YapSafetyRosUnityBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if node.unity.sock:
                node.unity.sock.close()
        except:
            pass
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
