# ROS2 Digital Factory Experimental Repository

## Overview

This repository contains source code supporting the experimental work reported in:

**Experimental characterization of communication performance in heterogeneous Digital Factory environments**

The repository includes two main groups of experimental implementations:

1. Controlled communication experiments used to characterise TCP/IP, ROS2 DDS and ROS2–Unity communication under increasing workloads.
2. Integrated Digital Factory use cases involving safety, inspection, robotic and industrial systems.

The experiments evaluate communication behaviour using round-trip time (RTT), upper-tail latency, message-loss behaviour and computational resource utilisation across heterogeneous PC, Raspberry Pi and industrial-device configurations.

## Repository Structure


ROS2-Digital-Factory/
├── 6.0_Controlled_Communication/
│   ├── ROS2_DDS/
│   │   ├── PC_PC/
│   │   ├── Pi_Pi/
│   │   └── Pi_PC/
│   ├── TCP_IP/
│   │   ├── PC_PC/
│   │   └── Pi_Pi/
│   └── ROS2_Unity/
│       ├── PC_PC/
│       └── Pi_PC/
│
├── 1.0_Safety/
├── 2.0_Inspection/
├── 3.0_Robot/
├── 4.0_Complex/
├── 5.0_Industrial/
└── README.md