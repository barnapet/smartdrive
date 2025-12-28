# SmartDrive: Universal OBD-II Data Platform & Ecosystem 🚗 

### Connect. Analyze. Save.

**SmartDrive** is a data-centric IoT platform designed to convert raw vehicle telemetry into human-readable, financially beneficial, and safety-oriented services. The project focuses on scalability, security, and a sustainable cloud-native infrastructure using a Medallion data architecture.

---

## 🌟 Key Features

| Feature | Description | Business Value |
| :--- | :--- | :--- |
| **Mechanic-Translator** | Instant interpretation of DTC (Diagnostic Trouble Codes). | Reduces repair costs and information asymmetry. |
| **Value Guard Certificate** | Certified, digitally signed PDF reports of vehicle history. | Increases resale value and builds buyer trust. |
| **Battery Health Prediction** | Time-series analysis of cranking voltage (SOH prediction). | Prevents unexpected breakdowns. |
| **Driving Style Profiling** | Telemetry-based scoring (braking, acceleration, idling). | Lowers fuel consumption and promotes safety. |
| **Legal-Light** | Archiving telemetry for critical events (hard braking, collisions). | Objective evidence in legal or insurance disputes. |

---

## 🏗️ Technological Stack

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
- [ ] Cloud-based Ingestion pipeline setup (Bronze layer)
- [ ] Mobile application MVP (DTC reading functionality)
- [ ] Validation of the Battery Health Prediction algorithm
- [ ] Automated PDF "Value Guard" report generation

---

## 🛠️ Installation & Development

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

---

## 👤 Author

**Peter Barna** – Lead Developer & Data Engineer
* [LinkedIn Profile](https://www.linkedin.com/in/peter-barna-dev/)
