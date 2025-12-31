x# System Design Document (SDD): SmartDrive Platform (v1.2)

**Version:** 1.2
**Date:** Dec 2025
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Author:** Peter Barna

---

## 1. Physical Architecture (Cloud Architecture)
The system is built on a modern, cloud-native **Event-driven Architecture** utilizing microservices for high scalability and cost-efficiency.

### 1.1 Components
* **Client Side:** Cross-platform mobile application (Flutter or React Native). To ensure stability and offline functionality, it utilizes an **SQLite-based Local Cache**.
* **Communication Layer:** **AWS IoT Core**. Data transmission between the vehicle-mounted OBD unit and the phone (Bluetooth), and subsequently between the phone and the cloud, is handled via the **MQTT protocol**.
* **Compute Layer:** **AWS Lambda (Serverless)**. Processing logic is executed only upon data ingestion, eliminating continuous server maintenance costs.
* **External APIs: (v1.1 Update)**
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
| **Users** | User profiles and subscription status. | `user_id` (PK), `email`, `password_hash` |
| **Vehicles** | Master data of registered vehicles. | `vin` (PK), `user_id` (FK), `model_info` |
| **Telemetry** | Cleaned data with normalized physical units. | `telemetry_id` (PK), `vin` (FK), `pid_code`, `value` |
| **DTC_Global_Cache** | **(New)** Global table for pre-translated codes to minimize AI costs. | `dtc_id` (PK), `description`, `is_ai_generated` |
| **VehicleInsights** | Pre-calculated indicators and analytics (Gold level). | `vin` (PK/FK), `battery_health`, `driver_score`, `dtc_description_hu` |

---

## 3. Algorithms & Business Logic
The system transforms raw telemetry data (Voltage, RPM, Speed) into actionable intelligence.

### 3.1 Battery Health Prediction (v1.2 Update)
The algorithm analyzes the **voltage drop** during the engine cranking phase using a **Temperature-Compensated Dynamic Threshold ($V_{crit}$)**.

* **Dynamic Threshold Logic:**
    * $T \geq 21^\circ C$: **9.6V** (Standard BCI threshold)
    * $10^\circ C \leq T < 21^\circ C$: **9.4V**
    * $0^\circ C \leq T < 10^\circ C$: **9.1V**
    * $T < 0^\circ C$: **8.5V** (Winter Survival Pack threshold)
* **Logic:** If the minimum voltage ($V_{min}$) falls below $V_{crit}$ for three consecutive days, a "Critical" status is flagged.
* **Output:** Automated push notification for battery replacement.

### 3.2 Mechanic-Translator (Hybrid DTC Interpretation)
This algorithm interprets Diagnostic Trouble Codes through a tiered lookup strategy:
1. **Tier 1 (SAE Library):** Local lookup of standard P0xxx codes.
2. **Tier 2 (Global Cache):** Querying the `DTC_Global_Cache` in DynamoDB for previously translated codes.
3. **Tier 3 (AI Fallback):** Calling the OpenAI API for human-readable explanations, which is then stored in the Tier 2 cache.

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
* **Secrets Management (New):** OpenAI API keys and database credentials are stored in **AWS Secrets Manager** to prevent hardcoding in source files.

### 5.3 Energy Efficiency (Vampire Drain Protection)
To prevent the ELM327 adapter from draining the vehicle battery during "Engine OFF" periods:
* **Voltage-based Cut-off:** If $V_{ocv}$ falls below **12.1V**, all background polling is suspended.
* **Resume Condition:** Data ingestion resumes only when voltage reaches **13.0V** (indicating the alternator is active).
* **User Notification:** A push notification is sent: *"Power Saving Mode: Monitoring paused to protect battery."*

---

## 6. Data Flow & Resilience (v1.2 Update)

1.  **Collection (Adaptive Sampling):**
    * **Cranking Phase:** High-speed sampling at **10 Hz (100 ms)** to accurately capture $V_{min}$.
    * **Steady State (Running):** Standard **0.2 Hz (5 s)** sampling for operational telemetry.
    * **Post-Drive (0-30 min OFF):** 1-minute intervals to monitor surface charge decay.
    * **Standard Sleep (30 min-24 h OFF):** 30-minute intervals for discharge tracking.
    * **Deep Sleep (>24 h OFF):** Sampling suspended to maximize protection.
2.  **Ingest:** Pushed via **MQTT** to **AWS IoT Core**.
3.  **Process:** S3 Trigger activates **Processing Lambda** for cleaning and Parquet conversion.
4.  **Insight Generation:** Hybrid DTC lookup and SOH algorithms update the Gold Layer.
5.  **Visualization:** Client retrieves data via REST API.
