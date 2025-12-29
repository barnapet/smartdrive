# System Design Document (SDD): SmartDrive Platform (v1.1)

**Version:** 1.1
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
* **External APIs (New in v1.1):**
    * **OpenWeatherMap:** Provides external ambient temperature data for the "Winter Survival Pack" logic.
    * **OpenAI API (gpt-4o-mini):** Generative diagnostic engine used for interpreting rare or manufacturer-specific DTC codes.

### 1.2 Storage Strategy (Medallion Architecture)
The platform follows the Medallion data design pattern:
* **Bronze / Silver (Amazon S3):** Long-term storage for raw events and cleaned, structured files (**Apache Parquet** format).
* **Gold (Amazon DynamoDB / PostgreSQL):** High-performance application database for real-time retrieval and global caching of diagnostic insights.

---

## 2. Data Model
The hybrid model combines relational and document-based approaches to ensure data integrity and rapid query performance.

### 2.1 Logical Data Model (Updated Attributes)

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

### 3.1 Battery Health Prediction
The algorithm analyzes the **voltage drop** during the engine cranking phase.
* **Logic:** If the minimum voltage ($V_{min}$) falls below **9.6V** for three consecutive days, a "Critical" status is flagged.
* **Output:** Automated push notification for battery replacement.

### 3.2 Mechanic-Translator (Hybrid DTC Interpretation)
This algorithm interprets Diagnostic Trouble Codes through a tiered lookup strategy:
1. **Tier 1 (SAE Library):** Local lookup of standard P0xxx codes.
2. **Tier 2 (Global Cache):** Querying the `DTC_Global_Cache` in DynamoDB for previously translated codes.
3. **Tier 3 (AI Fallback):** Calling the OpenAI API for a human-readable Hungarian explanation, which is then stored in the Tier 2 cache.

---

## 4. Interface Design (API Design)
Communication is facilitated through a standardized **REST API**.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/vehicle/{vin}/status` | **GET** | Returns status, including `dtc_description_hu`. |
| `/vehicle/{vin}/report` | **GET** | Generates a vehicle health certificate in PDF format. |
| `/telemetry/ingest` | **POST** | Endpoint for the mobile app to upload compressed data. |

---

## 5. Security & Privacy
Multi-layered protection following the **"Defense in Depth"** principle.

### 5.1 Data Protection (GDPR & Encryption)
* **Encryption:** AES-256 for storage and TLS 1.3 for transit.
* **Pseudonymization:** VINs are hashed within analytical layers.

### 5.2 Authentication & Secrets
* **Identity:** Verified using **JSON Web Tokens (JWT)**.
* **Secrets Management (New):** OpenAI API keys and database credentials are stored in **AWS Secrets Manager** to prevent hardcoding in source files.

---

## 6. Data Flow & Resilience
1. **Collection:** Data gathered in local **SQLite** database.
2. **Ingest:** Pushed via **MQTT** to **AWS IoT Core**.
3. **Process:** S3 Trigger activates **Processing Lambda** for cleaning and Parquet conversion.
4. **Insight Generation:** Hybrid DTC lookup and SOH algorithms update the Gold Layer.
5. **Visualization:** Client retrieves data via REST API.
