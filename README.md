# ROS2 Digital Factory Experimental Repository

## Overview

This repository contains the source code supporting the experimental work reported in:

**Experimental characterization of communication performance in heterogeneous Digital Factory environments**

The repository contains two main groups of experimental implementations:

1. **Controlled communication experiments** used to characterise TCP/IP, ROS2 DDS, and ROS2–Unity communication under increasing workloads.
2. **Integrated Digital Factory use cases** involving safety, inspection, robotic, and industrial systems.

The experiments evaluate communication behaviour using:

- round-trip time (RTT);
- 99th-percentile RTT (P99 RTT);
- application-level packet loss; and
- computational resource utilisation.

The implementations cover heterogeneous PC, Raspberry Pi, Unity, ROS2, and industrial-device configurations.

---

## Associated Publication

**Sivadas Chandra Sekaran, Hwa Jen Yap, Siti Nurmaya Musa, Chee Hau Tan, and Iqraq Kamal**

**Experimental characterization of communication performance in heterogeneous Digital Factory environments**

Submitted to *PeerJ Computer Science*.

The repository should be interpreted together with the Materials & Methods section of the associated manuscript, which describes the experimental procedures, configurations, performance metrics, filtering rules, and analysis methodology.

---

## Repository Structure

```text
ROS2-Digital-Factory/
│
├── 1.0_Safety/
│
├── 2.0_Inspection/
│
├── 3.0_Robot/
│
├── 4.0_Complex/
│
├── 5.0_Industrial/
│
├── 6.0_Controlled_Communication/
│   │
│   ├── ROS2_DDS/
│   │   ├── PC_PC/
│   │   ├── Pi_Pi/
│   │   └── Pi_PC/
│   │
│   ├── TCP_IP/
│   │   ├── PC_PC/
│   │   └── Pi_Pi/
│   │
│   └── ROS2_Unity/
│       ├── PC_PC/
│       └── Pi_PC/
│
└── README.md
```

---

## Experimental Implementations

### 1.0 Safety

Contains source code supporting the safety-monitoring implementation used in the integrated Digital Factory experiments.

The safety subsystem represents an edge-device workload in which physical sensor information is communicated to the wider Digital Factory environment.

---

### 2.0 Inspection

Contains source code supporting the machine-vision inspection implementation.

The inspection subsystem represents an event-driven workload involving image-processing and inspection-related operations within the integrated Digital Factory environment.

---

### 3.0 Robot

Contains source code supporting robotic-system communication and integration.

The robotic workload was used to evaluate communication behaviour associated with the physical–digital representation of robot operation.

---

### 4.0 Complex

Contains source code supporting the integrated laboratory-scale Digital Factory configuration.

This implementation combines multiple subsystems, including:

- safety monitoring;
- machine-vision inspection;
- robotic operation; and
- Unity-based Digital Factory visualisation.

These implementations support the integrated UC4 validation reported in the manuscript.

---

### 5.0 Industrial

Contains source code supporting the industrial-equipment validation configuration.

The implementation includes communication involving industrial equipment such as:

- programmable logic controller (PLC);
- LiDAR;
- UR10 industrial robot; and
- Unity-based Digital Factory components.

These implementations support the UC5 industrial-equipment validation reported in the manuscript.

---

## Controlled Communication Experiments

The controlled experiments used for communication-performance characterisation are contained in:

```text
6.0_Controlled_Communication/
```

The experiments progressively increased the number of active communication pairs while evaluating communication and computational behaviour across different hardware and deployment configurations.

Two update frequencies were evaluated:

- **10 Hz**
- **60 Hz**

The controlled experiments used timestamp- and UUID-based communication probes to measure round-trip communication behaviour.

---

### ROS2 DDS

```text
6.0_Controlled_Communication/
└── ROS2_DDS/
    ├── PC_PC/
    ├── Pi_Pi/
    └── Pi_PC/
```

Contains implementations used for the controlled ROS2 DDS communication experiments.

The evaluated deployment configurations include:

- PC–PC;
- Pi–Pi; and
- Pi–PC.

The ROS2 results reported in the manuscript used:

- **ROS2 Humble Hawksbill**
- **Fast DDS**
- **Reliable QoS**
- **Keep Last history**
- **queue depth = 10**

The remaining QoS parameters were left at their default settings for the reported experiments.

---

### Native TCP/IP

```text
6.0_Controlled_Communication/
└── TCP_IP/
    ├── PC_PC/
    └── Pi_Pi/
```

Contains implementations used for the native TCP/IP reference experiments.

The reported experimental implementation used:

- blocking TCP socket communication;
- persistent connections during each experimental run;
- one socket pair for each active communication pair; and
- a 2 s receive timeout.

`TCP_NODELAY` was not enabled in the reported experiments.

The TCP/IP implementations were evaluated across PC–PC and Pi–Pi configurations.

---

### ROS2–Unity

```text
6.0_Controlled_Communication/
└── ROS2_Unity/
    ├── PC_PC/
    └── Pi_PC/
```

Contains implementations supporting controlled ROS2–Unity communication experiments.

In this configuration, the ROS2-side application communicates with Unity through a TCP socket interface.

The evaluated configurations include:

- PC–PC; and
- Pi–PC.

These experiments were used to investigate the effect of application integration and increasing communication workload on communication latency and computational resource utilisation.

---

## Communication Probe

For the controlled communication experiments, each transmitted communication probe contained:

- a Unix timestamp; and
- a Universally Unique Identifier (UUID).

Example:

```json
{
  "id": "03337028-d789-4f75-9a3b-de1a464e7aa6",
  "timestamp": 1746932181.6736686
}
```

The UUID was used to associate each returned response with its corresponding transmitted message.

The application payload used in the reported controlled experiments was **79 bytes before protocol or middleware framing**.

---

## Performance Metrics

The experimental implementations support measurement of the following principal metrics.

### Round-Trip Time

RTT represents the elapsed time from transmission of a communication probe until the corresponding response returns to the originating system.

Both median RTT and P99 RTT were used in the associated study.

---

### Application-Level Packet Loss

Packet loss was measured at the application level.

A transmitted communication probe was classified as lost when no corresponding UUID-matched response was recorded.

These observations were excluded from RTT calculations but included in the packet-loss calculation.

---

### CPU Utilisation

CPU utilisation measurements represent whole-system processor utilisation rather than the utilisation of an individual communication process.

The associated study analyses upper-tail processor demand using P99 CPU utilisation.

---

## Software Environment

The reported experiments used the following principal software environments:

| Component | Environment |
|---|---|
| ROS2 | ROS2 Humble Hawksbill |
| DDS implementation | Fast DDS |
| Unity | Unity 2021 LTS |
| Linux systems | Ubuntu 22.04 LTS |
| Raspberry Pi 3B+ inspection platform | Raspbian Buster |
| Windows systems | Windows 10 Pro |
| ROS2 / communication programs | Python |
| Unity-side programs | C# |

Individual scripts may require modification of hardware-specific parameters such as:

- IP addresses;
- communication ports;
- local paths;
- device interfaces; and
- workload parameters.

These values depend on the deployment environment.

---

## Experimental Network

The reported experiments were conducted using a private wired Ethernet network.

The experimental network used:

- Cat6 Ethernet connections;
- a TP-Link TL-SG1024DE Gigabit Ethernet switch;
- manually assigned static IP addresses; and
- no wireless communication.

Network-level QoS was not used during the reported experiments.

---

## Experimental Procedure

The associated experiments were conducted using repeated experimental runs.

For the reported study:

- each experimental condition was repeated **five times**;
- each run lasted **300 s**;
- the first **60 s** of each run was excluded as a warm-up period; and
- the remaining **240 s** was retained for analysis.

Valid observations from all five repetitions were pooled for each experimental condition, providing **20 min of analysed data per condition**.

Full experimental procedures and filtering rules are provided in the associated manuscript.

---

## Experimental Data

The experimental datasets supporting the publication are provided separately as supplementary material with the journal submission.

The supplementary data include:

```text
Data/
│
├── 01_Controlled_Communication/
│
├── 02_UC4_Laboratory_Validation/
│
└── 03_UC4_UC5_Integrated_Summaries/
```

The supplied datasets include:

- RTT measurements;
- packet-loss results;
- CPU-utilisation measurements;
- UC4 laboratory-validation data; and
- UC5 industrial-equipment validation summaries.

The source code in this repository and the supplementary datasets should be interpreted together with the experimental methodology described in the manuscript.

---

## Reproducibility Notes

This repository contains research code corresponding to the experimental implementations used in the associated study.

Reproduction on different hardware may require configuration changes because the original experiments used specific:

- computing platforms;
- operating systems;
- IP addresses;
- network interfaces;
- industrial devices;
- ROS2 configurations; and
- Unity deployments.

The experimentally observed performance values should therefore not be interpreted as universal performance limits for ROS2, TCP/IP, Unity, or Digital Factory systems.

In particular, the approximately 80% System CPU P99 operating boundary reported in the associated publication is specific to the experimental population and the adopted 100 ms P99 RTT criterion.

---

## Citation

If this repository is used in academic work, please cite the associated publication.

Citation information and DOI will be added after publication.

---

## Contact

For questions relating to the experimental work:

**Sivadas Chandra Sekaran**  
Aerospace Malaysia Innovation Centre (AMIC)
sivadas@gmail.com

**Corresponding author of the associated publication:**  
Hwa Jen Yap  
Department of Mechanical Engineering  
Faculty of Engineering  
Universiti Malaya  
Kuala Lumpur, Malaysia

---

## Disclaimer

This repository contains experimental research implementations and is provided primarily to support transparency and reproducibility of the associated scientific study.

The code should not be interpreted as production-certified software for industrial or safety-critical deployment.
