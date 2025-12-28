# System Design Document (SDD): SmartDrive Platform

**Version:** 1.0
**Date:** Dec 2025
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Author:** Peter Barna

---

## 1. Physical Architecture (Cloud Architecture)
The system is built on a modern, cloud-native **Event-driven Architecture** utilizing microservices for high scalability and cost-efficiency.

### 1.1 Components
* **Client Side:** Cross-platform mobile application (Flutter or React Native). To ensure stability and offline functionality, it utilizes an **SQLite-based Local Cache**.
* **Communication Layer:** **AWS IoT Core**. Data transmission between the vehicle-mounted OBD unit and the phone (Bluetooth), and subsequently between the phone and the cloud, is handled via the **MQTT protocol**, ensuring reliability even in low-bandwidth scenarios.
* **Compute Layer:** **AWS Lambda (Serverless)**. Processing logic is executed only upon data ingestion, eliminating continuous server maintenance costs.

### 1.2 Storage Strategy (Medallion Architecture)
The platform follows the Medallion data design pattern:
* **Bronze / Silver (Amazon S3):** Long-term storage for raw events and cleaned, structured files (**Apache Parquet** format) for historical analytics.
* **Gold (Amazon DynamoDB / PostgreSQL):** High-performance application database for real-time data retrieval (e.g., current vehicle status display).

---

## 2. Data Model
The hybrid model combines relational and document-based approaches to ensure data integrity and rapid query performance.

### 2.1 Logical Data Model (ER Sketch)

| Table Name | Description | Key Attributes |
| :--- | :--- | :--- |
| **Users** | User profiles and subscription status. | `user_id` (PK), `email`, `password_hash` |
| **Vehicles** | Master data of registered vehicles. | `vin` (PK), `user_id` (FK), `model_info` |
| **RawEvents** | Ingested raw JSON payloads (Bronze level). | `event_id` (PK), `vin` (FK), `timestamp` |
| **Telemetry** | Cleaned data with normalized physical units. | `telemetry_id` (PK), `vin` (FK), `pid_code`, `value` |
| **VehicleInsights** | Pre-calculated indicators and analytics (Gold level). | `vin` (PK/FK), `battery_health`, `driver_score` |

---

## 3. Algorithms & Business Logic
The system transforms raw telemetry data (Voltage, RPM, Speed) into actionable intelligence.

### 3.1 Battery Health Prediction
The algorithm analyzes the **voltage drop** during the engine cranking phase.
* **Logic:** If the minimum voltage during cranking ($V_{min}$) falls below the critical threshold of **9.6V** for three consecutive days under similar ambient temperatures, the system flags a "Critical" status.
* **Output:** Automated push notification advising the user on immediate battery replacement.

### 3.2 Driving Style Scoring (Gamification)
Driver performance is rated on a scale of 0–100 based on the following weighted KPIs:
* **Safety (60%):** Frequency of sudden acceleration events and emergency braking maneuvers.
* **Economy (40%):** Proportion of time spent idling and frequency of exceeding the engine's optimal RPM range.

---

## 4. Interface Design (API Design)
Communication between the mobile application and the backend is facilitated through a standardized **REST API**.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/vehicle/{vin}/status` | **GET** | Returns the latest vehicle status (battery health, active DTCs). |
| `/vehicle/{vin}/report` | **GET** | Generates a vehicle health certificate in PDF format. |
| `/telemetry/ingest` | **POST** | Endpoint for the mobile app to upload compressed OBD data packets. |
| `/user/settings` | **PATCH** | Modify user preferences and notification settings. |

---

## 5. Security & Privacy
The system handles sensitive data (VIN, location, driving patterns) and follows the **"Defense in Depth"** principle to ensure multi-layered protection.



### 5.1 Data Protection (GDPR & Encryption)
* **Encryption At Rest:** All databases (PostgreSQL, DynamoDB) and S3 buckets utilize **AES-256** encryption.
* **Encryption In Transit:** Communication between the mobile app and the cloud is restricted to **TLS 1.3** protocols.
* **Sensitive Data Handling:** Vehicle Identification Numbers (VIN) are **pseudonymized (hashed)** within the analytical layers (Silver/Bronze) to prevent developers from directly linking vehicle data to individual users.

### 5.2 Authentication & Authorization
* **User Level:** Identity is verified using **JSON Web Tokens (JWT)**. Tokens feature short expiration times and use a Refresh Token mechanism for security.
* **System Level (AWS IAM):** All cloud components operate under the **"Principle of Least Privilege"**. Lambda functions are granted access only to the specific S3 buckets and database tables required for their execution.

---

## 6. Data Flow & Resilience
This section describes the end-to-end journey of data from the vehicle to the user interface and the mechanisms ensuring system uptime.



### 6.1 Data Pipeline Flow
1.  **Collection:** The mobile app gathers data from the OBD-II adapter and stores it in a local **SQLite** database.
2.  **Ingest:** Once an internet connection is established, the app pushes data packets via **MQTT** to **AWS IoT Core**.
3.  **Bronze (Raw):** IoT Core immediately archives the raw JSON payload into an S3 bucket.
4.  **Silver (Process):** An S3 Trigger activates a **Processing Lambda**, which cleans the data, normalizes units, and saves it in **Parquet** format.
5.  **Gold (Insights):** Analytical algorithms (Battery SOH, Driving Score) are executed, and results are written to the **PostgreSQL/DynamoDB** tables.
6.  **Visualization:** Upon the next app launch, the client retrieves updated insights via the REST API.

### 6.2 Resilience & Scalability
* **Offline Functionality:** If cellular connection is lost, the app buffers data in the local SQLite cache and utilizes **auto-sync retry logic** once connectivity is restored.
* **Dead Letter Queue (DLQ):** If a data packet fails processing due to a technical error, it is moved to a DLQ. This prevents data loss and allows engineers to perform manual troubleshooting.
* **Auto-scaling:** Utilizing **AWS Lambda** and **DynamoDB** ensures the system scales automatically based on load, whether supporting 10 or 10,000 concurrent vehicles.

---
