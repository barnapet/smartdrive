# System Design Document (SDD): SmartDrive Platform (v1.5)

**Version:** 1.5
**Date:** Jan 2026
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Author:** Peter Barna
**Status:** Update Section 5.3 Energy Efficiency (v1.5 Smart Guard Implementation) and 6.1 Data Flow (v1.5 Update)

---

## 1. Physical Architecture (Cloud Architecture)
The system is built on a modern, cloud-native **Event-driven Architecture** utilizing microservices for high scalability and cost-efficiency.

### 1.1 Components
* **Client Side:** Cross-platform mobile application (Flutter or React Native). To ensure stability and offline functionality, it utilizes an **SQLite-based Local Cache**.
* **Communication Layer:** **AWS IoT Core**. Data transmission between the vehicle-mounted OBD unit and the phone (Bluetooth), and subsequently between the phone and the cloud, is handled via the **MQTT protocol**.
* **Compute Layer:** **AWS Lambda (Serverless)**. Processing logic is executed only upon data ingestion, eliminating continuous server maintenance costs.
* **External APIs:**
    * **OpenWeatherMap:** Provides external ambient temperature data for the "Winter Survival Pack" and dynamic SOH logic.
    * **OpenAI API (gpt-4o-mini):** Generative diagnostic engine used for interpreting rare or manufacturer-specific DTC codes.

### 1.2 Storage Strategy (Medallion Architecture)
The platform follows the Medallion data design pattern:
* **Bronze / Silver (Amazon S3):** Long-term storage for raw events and cleaned, structured files (**Apache Parquet** format).
* **Gold (Amazon DynamoDB / PostgreSQL):** High-performance application database for real-time retrieval and global caching of diagnostic insights.

---

## 2. Data Model
The hybrid model combines relational and document-based approaches to ensure data integrity and rapid query performance.

### 2.1 Logical Data Model
The platform follows the Medallion data design pattern with tables for Users, Vehicles, Telemetry, DTC Global Cache, and Vehicle Insights.

| Table Name | Description | Key Attributes |
| :--- | :--- | :--- |
| **Users** | User profiles and subscription status. | `user_id` (PK), `email` |
| **Vehicles** | Master data of registered vehicles. | `vin` (PK), `user_id` (FK) |
| **Telemetry** | Cleaned data with normalized physical units. | `telemetry_id` (PK), `vin` (FK) |
| **DTC_Global_Cache** | Global table for pre-translated codes to minimize AI costs. | `dtc_id` (PK), `description` |
| **VehicleInsights** | Pre-calculated indicators and analytics (Gold level). | `vin` (PK/FK), `battery_health` |

---

## 3. Algorithms & Business Logic
The system transforms raw telemetry data (Voltage, RPM, Speed) into actionable intelligence.

### 3.1 Battery Health Prediction (v1.4 Dynamic Matrix)
The system utilizes a Fuel-Type Aware Lookup Table for SOH estimation.

| Ambient Temp ($T_{amb}$) | Min. SOH (Gasoline) | Min. SOH (Diesel) |
| :--- | :--- | :--- |
| $> 20^\circ C$ | 60% | 65% |
| $0^\circ C \dots 20^\circ C$ | 70% | 75% |
| $-10^\circ C \dots 0^\circ C$ | 75% | 80% |
| $< -10^\circ C$ | 80% | 85% |

### 3.2 Mechanic-Translator (Hybrid DTC Interpretation)
This algorithm interprets Diagnostic Trouble Codes through a tiered lookup strategy:
1. **Tier 1 (SAE Library):** Local lookup of standard P0xxx codes.
2. **Tier 2 (Global Cache):** Querying the `DTC_Global_Cache` in DynamoDB for previously translated codes.
3. **Tier 3 (AI Fallback):** Calling the OpenAI API (gpt-4o-mini) for human-readable explanations, which are then stored in the Tier 2 cache.

---

## 4. Interface Design (API Design)
Communication is facilitated through a standardized **REST API** with endpoints for vehicle status, health reports, and telemetry ingestion.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/vehicle/{vin}/status` | **GET** | Returns status, including `dtc_description_hu`. |
| `/vehicle/{vin}/report` | **GET** | Generates a vehicle health certificate in PDF format. |
| `/telemetry/ingest` | **POST** | Endpoint for the mobile app to upload compressed data. |

---

## 5. Security, Privacy & Energy Efficiency
Multi-layered protection following the **"Defense in Depth"** principle.

### 5.1 Data Protection (GDPR & Encryption)
* **Encryption:** AES-256 for storage and TLS 1.3 for transit.
* **Pseudonymization:** VINs are hashed within analytical layers.

### 5.2 Authentication & Secrets
* **Identity:** Verified using **JSON Web Tokens (JWT)**.
* **Secrets Management:** OpenAI API keys and database credentials are stored in **AWS Secrets Manager**.

### 5.3 Energy Efficiency (v1.5 Smart Guard Implementation)
To move beyond simple "Vampire Drain Protection," the system implements **Pulse Monitoring Technology**:
* **Low-Power Cycle:** After 5 minutes of engine-off inactivity, the MCU enters a sub-2mA state.
* **Wake-up Timer:** An internal hardware timer wakes the voltage-sensing circuit every 10 minutes.
* **Final Transmission Reserve:** The system maintains a small energy buffer to ensure it can successfully transmit the "External Drain" alert even at 11.5V before total disconnection.

---

## 6. Data Flow & Resilience (v1.5 Integrated Update)

### 6.1 Collection (Adaptive Sampling)
The system adjusts sampling frequency based on the vehicle's electrical state to balance data fidelity with power preservation:
* **Ready/Crank Phase:** High-speed sampling at $10\text{Hz}$ ($100\text{ms}$) starts immediately upon **Ignition ON ($\text{RPM}=0$)** to capture the $V_{min}$ transient curve.
* **Steady State (Running):** Standard $0.2\text{Hz}$ ($5\text{s}$) sampling for operational telemetry once $\text{RPM} \ge 600$.
* **Post-Drive (0-30 min OFF):** $1$-minute intervals to monitor surface charge decay after the alternator stops.
* **Smart Guard (Sentinel Mode):** Instead of suspended sampling, the device enters a **Pulse Monitoring** state, performing $100\text{ms}$ voltage checks every $10$ minutes to detect external parasitic drains.

### 6.2 Ingest & Emergency Path
Data is transmitted to the cloud via two distinct priority levels:
* **Standard Ingest:** Telemetry batches are pushed via **MQTT** to **AWS IoT Core** during active driving or standard intervals.
* **Emergency "Last-Gasp" Ingest (v1.5):** If the Sentinel Mode detects $V_{ocv} \le 11.5\text{V}$, the system immediately bypasses standard batching to send a high-priority **External Drain Alert** before shutting down to protect the battery.

### 6.3 Processing & Insights
* **Process:** **S3 Triggers** activate **Processing Lambdas** for cleaning and **Parquet** conversion.
* **Insight Generation:** Hybrid **DTC lookup** and **SOH algorithms** update the **Gold Layer** (Business tables).
* **Visualization:** The **Mobile Client** retrieves data and **"Smart Guard"** notifications via the **REST API**.
