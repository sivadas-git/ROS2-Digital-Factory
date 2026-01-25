import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from datetime import datetime
from time import time
import uuid
import queue
import threading

# Log file setup (same naming pattern style)
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = "Log_Safety_ROS_RT_" + str(now)

# -----------------------------
# Buffered logging (flush at 10 Hz)
# -----------------------------
log_q = queue.Queue(maxsize=200000)
stop_evt = threading.Event()

def _logger_thread_fn(path: str, flush_hz: float = 10.0):
    import time as _t
    period = 1.0 / flush_hz
    with open(path, 'a', buffering=1) as log_file:
        while not stop_evt.is_set():
            t_deadline = _t.perf_counter() + period
            batch = []
            while True:
                try:
                    batch.append(log_q.get_nowait())
                except queue.Empty:
                    break
            if batch:
                log_file.write("\n".join(batch) + "\n")
            sleep_time = t_deadline - _t.perf_counter()
            if sleep_time > 0:
                _t.sleep(sleep_time)

threading.Thread(target=_logger_thread_fn, args=(filename, 10.0), daemon=True).start()

def log_data(message):
    """Log data with timestamp to a file. (kept same function name style)"""
    try:
        log_q.put_nowait(f"{datetime.now()}, {message}")
    except queue.Full:
        pass

class SafetyROSRTTNode(Node):
    def __init__(self):
        super().__init__('safety_ros_rtt_node')

        # Topics (choose names that your YAP bridge will use)
        self.pub = self.create_publisher(String, 'safety_out', 10)
        self.sub = self.create_subscription(String, 'safety_echo', self.echo_callback, 10)

        # Latest states (you can feed these from real sensors if needed)
        self.light_state = "none"
        self.sound_state = "0"

        # Track outstanding requests
        self.pending = {}  # uuid -> send_time

        # Probe at 10 Hz (same as your TCP/IP run)
        self.timer = self.create_timer(0.1, self.send_probe)

    def send_probe(self):
        msg_id = str(uuid.uuid4())
        payload = f"{msg_id};{self.light_state},{self.sound_state}"

        self.pending[msg_id] = time()

        m = String()
        m.data = payload
        self.pub.publish(m)

    def echo_callback(self, msg: String):
        # Expect "uuid;light,sound"
        data = msg.data
        echoed_id = data.split(";", 1)[0] if ";" in data else ""

        if echoed_id in self.pending:
            rtt = time() - self.pending.pop(echoed_id)
            # log seconds for consistency with your other logs
            log_data(f"{data}, ok=True, rtt={rtt}")
        else:
            # Echo we didn't send (or arrived too late / already removed)
            log_data(f"{data}, ok=False, reason=unknown_uuid")

def main(args=None):
    rclpy.init(args=args)
    node = SafetyROSRTTNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        stop_evt.set()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
