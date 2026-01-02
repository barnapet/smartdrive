# Project Charter (Extended v1.3): SmartDrive OBD-II Data Platform

**Version:** 1.3
**Date:** Jan 2026
**Project Lead:** Peter Barna
**Status:** Updated with Winter Edition Safety Logic (11.5V)

---

## 1. Project Definition & Scope
To prevent **"Scope Creep"** and ensure project delivery, the boundaries of development are strictly defined as follows:

### 1.1 In-Scope (What we are developing)
* **Data Ingestion:** Real-time reading of standard OBD-II PIDs (Speed, RPM, Voltage, Temperature, DTC codes).
* **Adaptive Sampling:** **(v1.3 Update)** Implementation of state-based polling rates: **10Hz (100ms)** starting from **Ignition ON (Ready Phase)** to capture $V_{min}$ transients accurately.
* **Cloud Architecture:** A Medallion-based data warehouse (Bronze/Silver/Gold) hosted on AWS.
* **Analytics Engines:** Temperature-compensated battery degradation predictive models and driving style scoring algorithms.
* **Safety Features:** **(v1.3 Update)** Vampire Drain Protection logic to suspend polling if battery voltage drops below **11.5V** while the engine is OFF.
* **User Interfaces:** Cross-platform mobile application (Android/iOS) and automated PDF reporting engine.
* **Infrastructure:** Fully automated CI/CD pipelines and Infrastructure as Code (Terraform).

### 1.2 Out-of-Scope (What we are NOT developing)
* **Hardware Manufacturing:** We rely on existing ELM327-compliant Bluetooth dongles.
* **Video Processing:** No integration or storage of dashcam/video footage.
* **ECU Writing/Chiptuning:** The system is **read-only** for safety and legal reasons.

---

## 2. Stakeholder Analysis
* **End User (Car Owner):** Primary persona focusing on cost savings, safety, and battery reliability.
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
* **Battery Diagnostic Precision:** **(v1.3 Update)** Successful capture of the $V_{min}$ curve using **High-Frequency sampling (up to 10Hz)** starting from Ignition ON.
* **Connectivity Performance:** Bluetooth initialization within **5 seconds**.
* **DevOps KPI:** Infrastructure deployable via Terraform within **15 minutes**.
* **Reliability:** DTC interpretation accuracy of at least **90%** for P-codes.

---

## 5. Risk Management Matrix (Updated)

| Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Offline Data Loss** | High | Medium | Implement **SQLite-based local caching** on the mobile client. |
| **API Latency Spikes** | Low | High | Implement **CloudFront CDN** and aggressive caching for static assets. |
| **Incorrect AI Prediction** | Medium | High | Display a **confidence level** alongside insights. |
| **Vampire Drain** | Medium | High | **(v1.3 Update)** Implement 11.5V cut-off logic with engine-state awareness. |
| **High-Freq Data Gap** | Low | Medium | **(v1.3 Update)** Initiate 10Hz polling at Ignition ON (RPM=0) to ensure $V_{min}$ capture. |

---

## 6. Resources & Budget Estimation
* **Human Resources:** 1 Lead Developer / Data Engineer.
* **Infrastructure Costs (MVP):** Estimated **$10–$25 USD/month**.
* **Hardware:** 1 ELM327 Bluetooth Dongle (approx. $15–$30 USD).

---

## 7. Project Roadmap & Milestones (v1.3 Update)

### M1: Foundation & Adaptive Ingestion (Month 1)
* **Deliverables:** Working Bluetooth handshake, **Ignition-triggered 10Hz buffer**, Raw data streaming to AWS S3 (Bronze Layer).
* **Goal:** Establish a high-fidelity data pipeline capable of capturing engine start transients.

### M2: Processing & Safety Logic (Month 2)
* **Deliverables:** Data cleaning pipelines (Silver Layer), **Winter-ready Vampire Drain Protection** (11.5V cut-off), Mechanic-Translator logic.
* **Goal:** Implement core diagnostic intelligence and hardware safety mechanisms.

### M3: Business Logic & Validation (Month 3)
* **Deliverables:** Aggregated Business tables (Gold Layer), **Dynamic Threshold validation**, Automated PDF "Value Guard" generation.
* **Goal:** Finalize the predictive engine and provide measurable financial and safety value to the user.
