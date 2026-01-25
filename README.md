Overview
This document describes the experimental implementation used in the study:
“A ROS2-based Digital Factory Architecture for Real-Time and Interoperable Virtual Reality Simulation”

The experiments evaluate end-to-end round-trip time (RTT) and timing stability (jitter) across multiple manufacturing subsystems using:
- TCP/IP socket-based communication (baseline)
- ROS2 middleware (DDS-based) communication (proposed architecture)

All experiments are conducted under identical hardware and network conditions.

RTT Measurement Principle
RTT is always measured only at the initiating device:
RTT = T_received − T_sent
This avoids clock synchronization issues and PTP dependency.

Experimental Use Cases
UC1 – Safety System (Streaming)
UC2 – Inspection System (RPC)
UC3 – Robot Arm System (Streaming)
UC4b – Complex Integrated System

Each use case has:
- TCP/IP baseline
- ROS2 implementation

UC1 – Safety System
TCP/IP:
Safety Pi → Central PC → VR → Central PC → Safety Pi
Files:
Safety_Pi.py
Safety_Yap.py
Safety_VR_RTT.cs

ROS2:
Safety Pi → Central PC (ROS Bridge) → VR → Central PC → Safety Pi
Files:
Safety_Pi_ROS.py
Safety_Yap_ROS_bridge.py
Safety_VR_RTT.cs

UC2 – Inspection System
TCP/IP:
Central PC → Inspection Pi → Central PC → VR → Central PC
Files:
InspectionNonRosYapComplete.py
IncomingTCPImage_1.cs

ROS2:
Central PC → Inspection Pi (ROS Service) → Central PC → VR → Central PC
Files:
image_client_node.py
Image_ROS_Service.py
IncomingTCPImage_1.cs

UC3 – Robot Arm System
TCP/IP:
Robot PC → Central PC → VR → Central PC → Robot PC
Files:
robot_tcpip.py
robot_yap.py
ServerRobot.cs

ROS2:
Robot PC → Central PC (ROS Bridge) → VR → Central PC → Robot PC
Files:
robot_controller_node.py
robot_to_central.py
Robot_Yap_ROS.py
ServerRobot.cs

UC4b – Complex Integrated System
TCP/IP:
Central PC → Inspection → Robot → Safety → VR → Central PC
Files:
uc4b_tcpip_central_orchestrator.py
robot_contour_tcp_server.py
Safety_Complex.py
CounterReceiver.cs

ROS2:
Central PC → Inspection → Robot → Safety → Central PC → VR
Files:
image_processing_node.py
safety_counter_node.py
counter_listener_node.py
Robot_Yap_ROS.py
CounterReceiver.cs

Data Logging
- RTT logged only at initiating node
- Buffered logging to avoid bias
- Streaming UCs: 10–60 Hz
- Trigger-based UCs: on-demand

Repository Scope
This repository does not include:
- OS images
- ROS2 installation
- Python/ROS dependencies


This repository was prepared with the assistance of AI-based tools for
code formatting, commenting, and documentation drafting. All system
design decisions, implementations, experiments, and analyses were
performed by the author.
