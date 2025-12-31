# Project Charter (Extended v1.3): SmartDrive OBD-II Data Platform

**Version:** 1.3
**Date:** Dec 2025
**Project Lead:** Peter Barna

---

## 1. Project Definition & Scope
To prevent **"Scope Creep"** and ensure project delivery, the boundaries of development are strictly defined as follows:

### 1.1 In-Scope (What we are developing)
* **Data Ingestion:** Real-time reading of standard OBD-II PIDs (Speed, RPM, Voltage, Temperature, DTC codes).
* **Adaptive Sampling:** **(New)** Implementation of state-based polling rates: **10Hz** during the Cranking Phase and dynamic intervals during Sleep modes.
* **Cloud Architecture:** A Medallion-based data warehouse (Bronze/Silver/Gold) hosted on AWS.
* **Analytics Engines:** **Temperature-compensated** battery degradation predictive models and driving style scoring algorithms.
* **Safety Features:** **(New)** Vampire Drain Protection logic to suspend polling if battery voltage drops below **12.1V**.
* **User Interfaces:** Cross-platform mobile application (Android/iOS) and automated PDF reporting engine.
* **Infrastructure:** Fully automated CI/CD pipelines and Infrastructure as Code (Terraform).

### 1.2 Out-of-Scope (What we are NOT developing)
* **Hardware Manufacturing:** We rely on existing ELM327-compliant Bluetooth dongles.
* **Video Processing:** No integration or storage of dashcam/video footage.
* **ECU Writing/Chiptuning:** The system is **read-only** for safety and legal reasons.

---

## 2. Stakeholder Analysis
* **End User (Car Owner):** Primary persona. Focuses on cost savings, safety, and battery reliability.
* **Used Car Buyer:** Interested in the "Value Guard Certificate" for transparency.
* **Lead Developer:** Responsible for Data Engineering, DevOps, and Backend logic.
* **Service Partners:** Mechanics who receive translated diagnostic reports.

---

## 3. System Architecture & Data Model
The system utilizes a multi-layered data processing strategy.

### 3.1 Data Processing Layers
1.  **Ingestion Layer:** AWS IoT Core handles incoming MQTT messages with **adaptive frequency** logic.
2.  **Bronze (Raw):** Original JSON payloads stored in Amazon S3 for full auditability.
3.  **Silver (Cleaned):** Schema enforcement via AWS Glue and conversion to **Parquet** format.
4.  **Gold (Business):** Aggregated tables ready for visualization (e.g., `driver_score`, `battery_health`).

---

## 4. Quality & Acceptance Criteria
* **Engineering Validation:** Diagnostic data accuracy within **98%** of professional tools.
* **Battery Diagnostic Precision:** **(New)** Successful capture of the $V_{min}$ curve using **10Hz sampling** with 99% reliability.
* **Connectivity Performance:** Bluetooth initialization within **5 seconds**.
* **DevOps KPI:** Infrastructure deployable via Terraform within **15 minutes**.
* **Reliability:** DTC interpretation accuracy of at least **90%** for P-codes.

---

## 5. Risk Management Matrix (Updated)

| Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Offline Data Loss** | High | Medium | Implement **SQLite-based local caching** on the mobile client. |
| **API Latency Spikes** | Low | High | Implement **CloudFront CDN** and aggressive caching for static assets. |
| **Incorrect AI Prediction** | Medium | High | Display a **confidence level** alongside insights and use dynamic thresholds to reduce false positives. |
| **Vampire Drain** | Medium | High | **(New)** Implement hard-coded 12.1V cut-off logic to protect vehicle battery. |
| **High-Freq Data Gap** | Low | Medium | **(New)** Use local 10Hz buffering to ensure $V_{min}$ is captured even during transmission jitter. |

---

## 6. Resources & Budget Estimation
* **Human Resources:** 1 Lead Developer / Data Engineer.
* **Infrastructure Costs (MVP):** Estimated **$10–$25 USD/month** (leveraging AWS Free Tier).
* **Hardware:** 1 ELM327 Bluetooth Dongle (approx. $15–$30 USD).

---

## 7. Project Roadmap & Milestones (v1.3 Update)

### M1: Foundation & Adaptive Ingestion (Month 1)
* **Deliverables:** Working Bluetooth handshake, **10Hz Cranking Phase buffer**, Raw data streaming to AWS S3 (Bronze Layer), and Basic Mobile UI.
* **Goal:** Establish a high-fidelity data pipeline capable of capturing engine start transients.

### M2: Processing & Safety Logic (Month 2)
* **Deliverables:** Data cleaning pipelines (Silver Layer), **Vampire Drain Protection** (12.1V cut-off), Mechanic-Translator logic, and initial SOH algorithm.
* **Goal:** Implement core diagnostic intelligence and hardware safety mechanisms.

### M3: Business Logic & Validation (Month 3)
* **Deliverables:** Aggregated Business tables (Gold Layer), **Dynamic Threshold validation** (Weather API integration), Automated PDF "Value Guard" generation.
* **Goal:** Finalize the predictive engine and provide measurable financial and safety value to the user.
