# Software Requirements Specification (SRS): SmartDrive Platform (v1.3)

**Version:** 1.3
**Date:** Jan 2026
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Author:** Peter Barna
**Status:** Updated with Winter Logic (11.5V) and Ready-State Triggering

---

## 1. Introduction

### 1.1 Purpose
The purpose of this document is to define the functional and non-functional requirements of the **SmartDrive** universal OBD-II application and data platform. This document serves as the primary reference for development, testing, and final acceptance.

### 1.2 Scope
The system consists of a cross-platform mobile application, a cloud-native IoT data processing layer (Medallion architecture), and an administrative/analytics module.

---

## 2. General Description

### 2.1 User Classes and Characteristics
* **Average Car Owner:** Non-technical users seeking easy-to-understand explanations of vehicle health.
* **Conscious Driver:** Users interested in preserving vehicle value and optimizing driving efficiency.
* **Used Car Buyer/Seller:** Users requiring verified, tamper-proof vehicle health data.

### 2.2 Operating Environment
* **Hardware:** ELM327 Bluetooth/BLE OBD-II adapter.
* **Mobile Platforms:** iOS 14+ and Android 10+.
* **Cloud Infrastructure:** AWS (Lambda, S3, RDS, IoT Core, Timestream).

---

## 3. Functional Requirements

| ID | Name | Detailed Description | Priority |
| :--- | :--- | :--- | :--- |
| **FR1** | **OBD-II Connection** | Establish stable BT/BLE connection with ELM327 dongles. Automatic reconnection on drop. | **Critical** |
| **FR2** | **DTC Diagnostics** | Read and clear Stored and Pending Diagnostic Trouble Codes (DTC). | **High** |
| **FR3** | **Mechanic-Translator** | Translate DTCs into natural language; determine severity levels (Critical/Warning/Info). | **High** |
| **FR4** | **Adaptive Telemetry** | **(v1.3 Update)** Capture data with **Adaptive Polling**: Steady State (5s) and **High-Frequency Ready/Crank Phase (Target: 10Hz)**. Triggered at Ignition ON (RPM=0). Actual rate is hardware-dependent (Best Effort). | **High** |
| **FR5** | **Battery SOH Analysis** | Profile voltage drop during engine start using **Temperature-Compensated Dynamic Thresholds**. | **High** |
| **FR6** | **Driving Style Scoring** | Calculate safety and economy indices based on G-sensor and speed data. | **Medium** |
| **FR7** | **Winter Survival Pack** | Proactive push notifications based on ambient temperature and battery health. | **Medium** |
| **FR8** | **Value Guard Certificate** | Generate digitally signed PDF reports of service history and driving profiles. | **Medium** |
| **FR9** | **Accident Event Recorder** | Highlighted backup of the last 30s of telemetry data upon detecting high G-force events. | **Low** |
| **FR10** | **User Profile** | Vehicle registration via VIN; support for multi-car management per account. | **High** |
| **FR11** | **Vampire Drain Protection** | **(v1.3 Update)** Automatically suspend data polling if $V_{ocv} < 11.5V$ while engine is OFF (RPM=0) to prevent battery discharge; resume at $13.0V$. | **High** |

---

## 4. Use Cases (UC)
---

## 4. Use Cases (UC)

### UC-1: "Mechanic-Translator" (Diagnostics)
* **Actor:** User
* **Process:**
    1. User initiates a diagnostic scan.
    2. The App retrieves DTCs from the vehicle.
    3. The Cloud API provides the translation and actionable repair suggestions.
* **Exception:** If offline, the app attempts to translate from local cache or displays a network error.

### UC-2: Automatic Battery Health Check (v1.3 Update)
* **Actor:** System (Background Process)
* **Process:**
    1. System detects Ignition ON (RPM=0) and switches to **High-Speed Sampling (Target: 10Hz)** to proactively monitor the cranking transient.
    2. System measures the minimum cranking voltage ($V_{min}$), utilizing numerical interpolation to compensate for hardware latency if the actual sampling rate is below 10Hz.
    3. System retrieves ambient temperature via OpenWeatherMap API and determines the **Dynamic Threshold ($V_{crit}$)**.
    4. Data is ingested into the cloud (Bronze Layer).
    5. If $V_{min} < V_{crit}$ or a significant negative trend is detected, the system sends a push notification to the user.

### UC-3: Certificate Request
* **Actor:** User
* **Process:**
    1. User selects a date range and vehicle.
    2. The system aggregates data from the Gold Layer.
    3. A PDF is generated and made available for download.

---

## 5. Non-Functional Requirements (NFR)

### 5.1 Performance & Scalability
* **NFR1:** API response time for DTC lookup must not exceed 2 seconds (p95).
* **NFR2:** System must support 10,000 concurrent active data-ingesting clients.

### 5.2 Reliability & Availability
* **NFR3:** Cloud-side ingestion endpoint availability must be 99.9%.
* **NFR4:** Offline Mode: The app must cache up to 50MB of telemetry data locally if a connection is unavailable.

### 5.3 Security & Privacy
* **NFR5:** GDPR Compliance: Users must be able to request permanent data deletion at any time.
* **NFR6:** All data transmission between mobile and cloud must use TLS 1.2+ encryption.

### 5.4 Maintainability
* **NFR7:** The infrastructure must be fully redeployable via Terraform (IaC) to a clean AWS environment within 15 minutes.

---

## 6. External Interface Requirements

* **User Interface (UI):** Modern "cardiovascular" color coding (Green/Yellow/Red).
* **Hardware Interface:** Standard ELM327 AT command set. **v1.3** utilizes optimized commands (AT S0, H0, AT1) for 10Hz stability.
* **Software Interface:** **OpenWeatherMap API** integration for external temperature data.	
