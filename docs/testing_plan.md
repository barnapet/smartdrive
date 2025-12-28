# Testing Plan: SmartDrive Platform

**Version:** 1.0
**Date:** Dec 2025
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Focus:** Quality Assurance, Validation, and Verification
**Author:** Peter Barna

---

## 1. Testing Levels
To ensure a robust system, testing is conducted across four distinct layers, following the industry-standard **Testing Pyramid**.



### 1.1 Unit Testing
* **Objective:** Verify the mathematical and logical correctness of individual functions.
* **Scope:** * The **Battery SOH** algorithm (verifying if specific $V_{min}$ values trigger the correct alerts).
    * The **Driver Scoring** calculation logic ($S$ score calculation).
    * **DTC Translation Mapping** (ensuring hex codes map to the correct strings).
* **Tools:** PyTest (Python), Jest (Flutter/JS).

### 1.2 Integration Testing
* **Objective:** Verify that different system components communicate correctly.
* **Scope:**
    * Does the Mobile App successfully push a JSON payload to the **AWS IoT Core**?
    * Does the **S3 Trigger** correctly invoke the Processing Lambda?
    * Is the connection between the **Lambda** functions and the **PostgreSQL** Gold database stable?

### 1.3 System Testing (End-to-End)
* **Objective:** Validate the entire data pipeline from the vehicle to the user’s screen.
* **Scenario:** Inject a simulated OBD-II data stream -> Data travels through the Medallion layers -> Verify if a PDF "Value Guard Certificate" is correctly generated with the simulated data.

### 1.4 User Acceptance Testing (UAT)
* **Objective:** Ensure the system meets the actual needs of the end user.
* **Key Questions:** * Does a non-technical user understand the "Mechanic-Translator" output?
    * Is the PDF report visually trustworthy and professional?
    * Does the "Winter Survival Pack" push notification arrive at a helpful time?

---

## 2. Requirements Traceability Matrix (RTM)
The RTM ensures that every requirement defined in the SRS is accounted for and tested.

| Req. ID | Test Case ID | Test Description | Expected Result |
| :--- | :--- | :--- | :--- |
| **FR1** (OBD Link) | **TC-1** | Initiate Bluetooth pairing with ELM327. | Stable connection; "Connected" status in UI. |
| **FR3** (Translator) | **TC-2** | Send known fault code (e.g., `P0101`). | UI displays "Mass Air Flow Sensor Circuit Range/Performance." |
| **FR5** (Battery) | **TC-3** | Simulate cranking voltage of $9.0V$. | Immediate "Critical Battery" push notification sent. |
| **FR8** (Certificate) | **TC-4** | Request report for the last 30 days. | A signed PDF is generated and downloadable. |

---

## 3. Testing Environment & Tools
Since real-world vehicle testing is time-consuming, we utilize a simulation-heavy environment.



[Image of the V-model in software testing]


* **OBD-II Simulator:** A custom Python script that "emulates" an ELM327 dongle, sending randomized or pre-defined PID sequences via Bluetooth or directly to the Ingest API.
* **Postman / Insomnia:** Used for manual testing of REST API endpoints and verifying JWT authentication.
* **Mocking Frameworks:** We use **Moto** (for AWS mocking) to simulate S3 and DynamoDB environments during CI/CD to prevent unnecessary cloud costs.

---

## 4. Defect Severity Classification
Errors found during testing are categorized as follows:
* **S1 (Blocker):** Total system failure or data loss (e.g., Telemetry not reaching the cloud).
* **S2 (Major):** A core feature is non-functional (e.g., Battery health is miscalculated).
* **S3 (Minor):** UI/UX glitches or minor translation errors.

---

## 5. Exit Criteria (Definition of Done)
The testing phase is considered complete only when:
1. **100% of Critical and High priority** test cases (TCs) have passed.
2. **Zero open S1 or S2 defects** remain in the bug tracker.
3. **Code Coverage** for the analytical algorithms (SOH, Scoring) reaches a minimum of **90%**.
4. **Regression Testing** is successful, ensuring that new updates haven't broken existing "Mechanic-Translator" functions.

---
