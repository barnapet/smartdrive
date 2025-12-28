# Project Charter (Extended v1.2): SmartDrive OBD-II Data Platform

**Version:** 1.0
**Date:** Dec 2025
**Project Lead:** Peter Barna

---

## 1. Project Definition & Scope
To prevent **"Scope Creep"** and ensure project delivery, the boundaries of development are strictly defined as follows:

### 1.1 In-Scope (What we are developing)
* **Data Ingestion:** Real-time reading of standard OBD-II PIDs (Speed, RPM, Voltage, Temperature, DTC codes).
* **Cloud Architecture:** A Medallion-based data warehouse (Bronze/Silver/Gold) hosted on AWS.
* **Analytics Engines:** Battery degradation predictive models and driving style scoring algorithms.
* **User Interfaces:** Cross-platform mobile application (Android/iOS) and automated PDF reporting engine.
* **Infrastructure:** Fully automated CI/CD pipelines and Infrastructure as Code (Terraform).

### 1.2 Out-of-Scope (What we are NOT developing)
* **Hardware Manufacturing:** We rely on existing ELM327-compliant Bluetooth dongles.
* **Video Processing:** No integration or storage of dashcam/video footage.
* **ECU Writing/Chiptuning:** The system is **read-only** for safety and legal reasons.

---

## 2. Stakeholder Analysis
* **End User (Car Owner):** Primary persona. Focuses on cost savings and safety.
* **Used Car Buyer:** Interested in the "Value Guard Certificate" for transparency.
* **Lead Developer:** Responsible for Data Engineering, DevOps, and Backend logic.
* **Service Partners:** Mechanics who receive translated diagnostic reports.

---

## 3. System Architecture & Data Model
The system utilizes a multi-layered data processing strategy.



### 3.1 Data Processing Layers
1.  **Ingestion Layer:** AWS IoT Core handles incoming MQTT messages.
2.  **Bronze (Raw):** Original JSON payloads stored in Amazon S3 for full auditability.
3.  **Silver (Cleaned):** Schema enforcement via AWS Glue and conversion to **Parquet** format.
4.  **Gold (Business):** Aggregated tables ready for visualization (e.g., `driver_score`).

---

## 4. Quality & Acceptance Criteria
* **Engineering Validation:** Diagnostic data accuracy within **98%** of professional tools.
* **Connectivity Performance:** Bluetooth initialization within **5 seconds**.
* **DevOps KPI:** Infrastructure deployable via Terraform within **15 minutes**.
* **Reliability:** DTC interpretation accuracy of at least **90%** for P-codes.

---

## 5. Risk Management Matrix

| Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Offline Data Loss** | High | Medium | Implement **SQLite-based local caching**. |
| **API Latency Spikes** | Low | High | Implement **CloudFront CDN** and caching. |
| **Incorrect AI Prediction** | Medium | High | Display a **confidence level** alongside insights. |

---

## 6. Resources & Budget Estimation
* **Human Resources:** 1 Lead Developer / Data Engineer.
* **Infrastructure Costs (MVP):** Estimated **$10–$25 USD/month** (AWS Free Tier).
* **Hardware:** 1 ELM327 Bluetooth Dongle (approx. $15–$30 USD).

---

## 7. Project Roadmap & Milestones

### M1: Foundation & Ingestion (Month 1)
* **Deliverables:** Working Bluetooth handshake, Raw data streaming to AWS S3 (Bronze Layer), Basic Mobile UI for connection status.
* **Goal:** Establish a stable data pipeline from vehicle to cloud.

### M2: Processing & Translation (Month 2)
* **Deliverables:** Data cleaning pipelines (Silver Layer), "Mechanic-Translator" logic (DTC look-up tables), and initial Battery Health algorithm.
* **Goal:** Convert raw hex codes into human-readable information.

### M3: Business Logic & MVP Launch (Month 3)
* **Deliverables:** Aggregated Business tables (Gold Layer), Automated PDF "Value Guard" generation, and final Dashboard UI.
* **Goal:** Provide measurable value to the user and finalize the product for release.

---
