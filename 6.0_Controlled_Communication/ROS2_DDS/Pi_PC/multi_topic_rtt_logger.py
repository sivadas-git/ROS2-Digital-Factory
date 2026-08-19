# Updated: Single-topic RTT logger node for modular scaling
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import time
import csv
import os
from datetime import datetime

class SingleTopicRTTLogger(Node):
    def __init__(self):
        super().__init__('single_topic_rtt_logger')

        self.index = self.declare_parameter('topic_index', 0).get_parameter_value().integer_value
        self.timeout = self.declare_parameter('timeout_sec', 2.0).get_parameter_value().double_value

        self.echo_topic = f"rtt_test_echo_{self.index}"
        self.sent_topic = f"rtt_sent_{self.index}"
        self.qos = rclpy.qos.QoSProfile(depth=10, reliability=rclpy.qos.ReliabilityPolicy.RELIABLE)

        self.sent_times = {}
        self.rtts = []
        self.received = 0
        self.lost = 0

        self.log_dir = "/home/inspection/ROS_ROS_Pi_Reverse"
        os.makedirs(self.log_dir, exist_ok=True)
        self.start_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.csv_path = f"{self.log_dir}/rtt_log_{self.echo_topic}_{self.start_time_str}.csv"
        self.summary_path = f"{self.log_dir}/summary_{self.echo_topic}_{self.start_time_str}.txt"

        with open(self.csv_path, 'w', newline='') as f:
            csv.writer(f).writerow(["timestamp_now", "msg_id", "rtt_seconds", "status"])

        self.create_subscription(String, self.sent_topic, self.sent_callback, self.qos)
        self.create_subscription(String, self.echo_topic, self.echo_callback, self.qos)
        self.create_timer(0.5, self.check_timeouts)

        self.get_logger().info(f"Started RTT logger for topic index {self.index}")

    def sent_callback(self, msg):
        try:
            data = json.loads(msg.data)
            self.sent_times[data['id']] = data['timestamp']
        except Exception as e:
            self.get_logger().error(f"Failed to parse sent message: {e}")

    def echo_callback(self, msg):
        try:
            data = json.loads(msg.data)
            msg_id = data['id']
            now = time.time()
            if msg_id in self.sent_times:
                rtt = now - self.sent_times.pop(msg_id)
                self.rtts.append(rtt)
                self.received += 1
                with open(self.csv_path, 'a', newline='') as f:
                    csv.writer(f).writerow([now, msg_id, round(rtt, 6), "OK"])
                self.get_logger().info(f"RTT OK [{msg_id}] = {rtt:.6f}s")
        except Exception as e:
            self.get_logger().error(f"Failed to parse echo: {e}")

    def check_timeouts(self):
        now = time.time()
        expired = [msg_id for msg_id, t in self.sent_times.items() if now - t > self.timeout]
        for msg_id in expired:
            self.lost += 1
            with open(self.csv_path, 'a', newline='') as f:
                csv.writer(f).writerow([now, msg_id, "", "LOST"])
            self.get_logger().warn(f"Message LOST: {msg_id}")
            del self.sent_times[msg_id]

    def destroy_node(self):
        super().destroy_node()
        total = self.received + self.lost
        avg_rtt = round(sum(self.rtts) / len(self.rtts), 6) if self.rtts else 0.0
        loss_pct = (self.lost / total * 100) if total else 0.0

        summary = [
            f"==== RTT Summary for topic index {self.index} ====",
            f"Sent     : {total}",
            f"Received : {self.received}",
            f"Lost     : {self.lost}",
            f"Loss %   : {loss_pct:.2f}%",
            f"Avg RTT  : {avg_rtt:.6f}s"
        ]

        for line in summary:
            self.get_logger().info(line)

        with open(self.summary_path, 'w') as f:
            for line in summary:
                f.write(line + "\n")
        self.get_logger().info(f"Saved summary to {self.summary_path}")


def main(args=None):
    rclpy.init(args=args)
    node = SingleTopicRTTLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
