# Controlled Communication Experiments

This directory contains the available source code supporting the controlled communication experiments reported in the study:

**Experimental characterization of communication performance in heterogeneous Digital Factory environments**

The controlled experiments evaluated native TCP/IP, ROS2 DDS and ROS2–Unity communication across PC and Raspberry Pi deployments under different communication workloads and update frequencies.

## Directory Structure

Controlled_Communication/
├── ROS2_DDS/
│   ├── PC_PC/
│   ├── Pi_Pi/
│   └── Pi_PC/
├── TCP_IP/
│   ├── PC_PC/
│   └── Pi_Pi/
└── ROS2_Unity/
    ├── PC_PC/
    └── Pi_PC/


The principal scripts are:

ros2_scalability.py – generates timestamped messages with unique identifiers.
scalability_publishers_10.launch.py – launches multiple concurrent ROS2 publisher nodes.
multi_topic_echo_responder.py – returns received messages to the originating side.
multi_ros_echo.launch.py – launches multiple echo-responder nodes.
multi_topic_rtt_logger.py – records round-trip time and identifies messages for which no response is received within the configured timeout.
logger_launch.launch.py – launches the corresponding RTT logger nodes.
tcpraw.py – creates multiple TCP communication processes, transmits UUID- and timestamp-tagged messages, measures RTT and records unsuccessful returns.
tcprawreply.py – provides TCP echo servers for the corresponding communication ports.
tcp_rtt_pub.py – generates UUID- and timestamp-tagged communication probes and measures returned RTT.
multi_ros_unity.launch.py – launches multiple concurrent communication instances.
UnityTcpEchoClient.cs – Unity-side TCP echo implementation.