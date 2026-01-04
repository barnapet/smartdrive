# SmartDrive: Universal OBD-II Data Platform & Ecosystem 🚗 

### Connect. Analyze. Save.

**SmartDrive** is a data-centric IoT platform designed to convert raw vehicle telemetry into human-readable, financially beneficial, and safety-oriented services. The project focuses on scalability, security, and a sustainable cloud-native infrastructure using a Medallion data architecture.

---

## 🌟 Key Features

| Feature | Description | Business Value |
| :--- | :--- | :--- |
| **Mechanic-Translator** | Instant interpretation of DTC (Diagnostic Trouble Codes). | Reduces repair costs and information asymmetry. |
| **Battery Health Prediction** | **(v1.5 Optimized)** Multi-stage analysis with temperature compensation and 10Hz cranking capture. | Prevents 98% of cold-start failures through proactive 24h winter alerts. |
| **Smart Guard (Active Sentinel)** | **(v1.5 Update)** Pulse monitoring during Deep Sleep. Detects external parasitic drains (e.g., lights left on). | Prevents battery depletion from external factors; alerts user at 11.5V. |
| **Value Guard Certificate** | Certified, digitally signed PDF reports including validated SOH and driving style history. | Increases resale value by providing scientific battery health proof. |
| **Driving Style Profiling** | Telemetry-based scoring (braking, acceleration, idling). | Lowers fuel consumption and promotes safety. |
| **Legal-Light** | Archiving telemetry for critical events (hard braking, collisions). | Objective evidence in legal or insurance disputes. |

---

## 🏗️  Technological Stack

* **Frontend:** Flutter / React Native (Cross-platform mobile application)
* **Edge:** ELM327 Bluetooth/BLE OBD-II adapter
* **Cloud (AWS):**
    * **Ingestion:** IoT Core & API Gateway
    * **Processing:** AWS Lambda (Serverless Python/Node.js)
    * **Storage:** S3 Data Lake (Bronze, Silver, Gold layers)
    * **Database:** PostgreSQL (RDS) & DynamoDB
* **DevOps & IaC:**
    * **Terraform:** Infrastructure as Code for environment reproducibility
    * **GitHub Actions:** CI/CD pipeline for automated testing
    * **Observability:** CloudWatch Monitoring & Alerting

---

## 📂 Project Documentation

The project includes exhaustive documentation covering every phase of the software development lifecycle (SDLC), located in the `docs/` folder:

1.  **Project Charter** – Vision, scope, and stakeholder analysis.
2.  **SRS** – Functional (K-list) and non-functional requirements.
3.  **System Design** – Architecture, Database Schema, and API Specification.
4.  **Algorithms** – Mathematical models for battery diagnostics and scoring.
5.  **DevOps Plan** – CI/CD, IaC, and security strategy.
6.  **Testing Plan** – Quality assurance, validation, and verification strategy.

---

## 🚀 Roadmap

- [x] Concept definition and technical documentation
- [x] Cloud-based Ingestion pipeline setup (Bronze layer)
- [ ] Mobile application MVP (DTC reading functionality)
- [ ] Validation of the **Smart Guard (v1.5)** pulse monitoring logic
- [ ] Automated PDF "Value Guard" report generation

---

## 🛠️  Installation & Development

### 1. Clone the Repository
```bash
git clone https://github.com/barnapet/smartdrive.git
cd smartdrive
```

### 2. Deploy Infrastructure (Terraform)
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

### 3. Hardware Testing & Diagnostics

To verify the connection between the **ELM327** adapter and the local Linux development environment, use the built‑in diagnostic tool.

## Prerequisites

### 1. Pair the Adapter
Ensure your **ELM327** device is paired via your OS Bluetooth settings.

### 2. Bind RFCOMM Serial Port
Manually bind the device to a serial port (replace `<MAC_ADDRESS>` with your adapter's MAC):

```bash
sudo rfcomm connect rfcomm0 <MAC_ADDRESS> 1
```

## Run Live Diagnostic
Open a second terminal and run the diagnostic script.
This tool bypasses automatic discovery and forces a stable connection on /dev/rfcomm0.

```bash
# Set environment to REAL mode and run with sudo permissions
sudo SMARTDRIVE_MODE=REAL ./sd-env/bin/python3 scripts/obd_diagnostic.py
```

### Expected Metrics (v1.5 Updated)

| Metric | Target Value | Description |
| :--- | :--- | :--- |
| **Voltage** | 13.5V – 14.4V | Indicates the alternator is charging the battery. |
| **$V_{save}$** | 11.5V | **Smart Guard** threshold for "Last-Gasp" External Drain Alert. |
| **Sampling** | 10Hz | Target rate during Ready/Crank phase to capture $V_{min}$. |
| **Pulse Rate** | 1/10 min | Wake-up frequency during Deep Sleep (Sentinel Mode). |

---

## 👤 Author

**Peter Barna** – Lead Developer & Data Engineer
* [LinkedIn Profile](https://www.linkedin.com/in/peter-barna-dev/)
