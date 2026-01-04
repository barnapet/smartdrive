# Testing Plan: SmartDrive Platform (v1.5)

**Version:** 1.5
**Date:** Jan 2026
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Focus:** Quality Assurance, Validation, and Verification
**Author:** Peter Barna
**Status:** Updated with Requirements Traceability Matrix

---

## 1. Testing Levels
To ensure a robust system, testing is conducted across four distinct layers, following the industry-standard **Testing Pyramid**.

### 1.1 Unit Testing
* **Objective:** Verify the mathematical and logical correctness of individual functions.
* **Scope:** * **Battery SOH Algorithm:** Verifying if specific $V_{min}$ values trigger correct alerts based on **temperature-compensated thresholds** (e.g., ensuring 9.0V is "Critical" at 21°C but "Pass" at -10°C).
    * **Vampire Drain Logic:** Testing the threshold-based suspension of polling at 11.5V and resumption at 13.0V.
    * **Adaptive Sampling Rate:** Verifying the switching logic between 10Hz (Cranking) and 0.2Hz (Steady State) modes.
    * **Driver Scoring Calculation:** Validating the $S$ score based on acceleration, braking, and idling pillars.
    * **DTC Translation Mapping:** Ensuring hex codes map to the correct human-readable strings.
    * **SOC Gate Logic:** Verify that SOH alerts are suppressed if simulated SOC is 65%.
    * **Debounce Verification:** Verify that a "Critical" notification is ONLY sent on the 3rd consecutive failing start simulation.
    * **Filter Validation:** Verify that a 15ms voltage drop to 6.0V (Inrush) is correctly ignored by the 100ms moving average.

### 1.2 Integration Testing
* **Objective:** Verify that different system components communicate correctly.
* **Scope:**
    * **Mobile App to AWS IoT Core:** Successful JSON/MQTT payload delivery.
    * **S3 Trigger to Lambda:** Ensuring raw (Bronze) data correctly invokes the Processing Lambda.
    * **Lambda to Database:** Stable connections between functions and PostgreSQL/DynamoDB.
    * **Weather API Integration:** Verifying that temperature data is correctly fetched for the SOH and Winter Survival Pack logic.

### 1.3 System Testing (End-to-End)
* **Objective:** Validate the entire data pipeline from the vehicle to the user’s screen.
* **Scenario:** * Inject a simulated 10Hz OBD-II stream representing a cold start.
    * Verify data travels through Medallion layers (Bronze, Silver, Gold).
    * Verify if the "Winter Survival Pack" notification and PDF "Value Guard Certificate" are correctly generated.

### 1.4 User Acceptance Testing (UAT)
* **Objective:** Ensure the system meets the actual needs of the end user.
* **Key Questions:** * Does a non-technical user understand the "Mechanic-Translator" output?
    * Is the "Power Saving Mode" notification clear when Vampire Drain Protection is active?
    * Does the "Winter Survival Pack" push notification arrive at a helpful time?

---

## 2. Requirements Traceability Matrix (RTM)

| Req. ID | Test Case ID | Test Description | Expected Result |
| :--- | :--- | :--- | :--- |
| **FR1** (OBD Link) | **TC-1** | Initiate Bluetooth pairing with ELM327. | Stable connection; "Connected" status in UI. |
| **FR3** (Translator) | **TC-2** | Send known fault code (e.g., `P0101`). | UI displays "Mass Air Flow Sensor Circuit Range/Performance". |
| **FR5** (Battery) | **TC-3** | Simulate $V_{min} = 9.2V$ at $T = 25^\circ C$. | Immediate "Critical Battery" notification ($V_{crit} = 9.6V$). |
| **FR5** (Battery) | **TC-3b** | Simulate $V_{min} = 9.2V$ at $T = -5^\circ C$. | No notification (Pass); voltage is above cold $V_{crit}$ (8.5V). |
| **FR4** (Sampling) | **TC-5** | **(v1.3 Update)** Transition to Ignition ON (RPM=0). | Polling frequency increases to **10Hz (Target)** proactively. |
| **FR11** (Protection)| **TC-6** | **(v1.3 Update)** Lower simulated $V_{ocv}$ to **11.4V** (Engine OFF). | Polling stops; "Power Saving Mode" notification sent. |
| **FR8** (Certificate)| **TC-4** | Request report for the last 30 days. | A signed PDF is generated and downloadable. |
| **FR5** | **TC-7** | Simulate 3 failing starts ($V_{min}=8.8V$). | Critical alert sent on 3rd attempt. |
| **FR7** | **TC-8** | Temp = -5°C, SOH = 82%. | Winter Survival Pack alert triggered (85% limit). |
| **FR11** | **TC-9** | Monitor current draw after RPM=0 for 5+ mins. | Current drops below 2mA (Deep Sleep verified). |
| **FR11** | **TC-10** | Simulate external 2A load during Deep Sleep. | At 11.5V, a "Critical External Drain" notification is received. |
| **FR11** | **TC-11** | Increase simulated voltage to 13.0V during Sleep. | System exits Deep Sleep and resumes 0.2Hz sampling. |
---

## 3. Testing Environment & Tools
Since real-world vehicle testing is time-consuming and difficult to replicate across various temperatures, we utilize a simulation-heavy environment.

* **OBD-II Simulator (v1.3 Update):** * **High-Speed Simulation:** Must support sending 10Hz PID sequences to validate the Ready-state trigger.
    * **High-Speed Simulation:** Must support sending 10Hz PID sequences (100ms intervals) to validate the Cranking Phase buffer logic.
    * **Voltage Manipulation:** Ability to simulate voltage drops below **11.5V** to trigger "Vampire Drain Protection".
* **Weather API Mocker:** A tool to inject various ambient temperatures into the system to verify the **Dynamic Threshold ($V_{crit}$)** selection logic.
* **Postman / Insomnia:** Used for manual testing of REST API endpoints and verifying JWT authentication.
* **Mocking Frameworks:** We use **Moto** (for AWS mocking) to simulate S3 and DynamoDB environments during CI/CD to prevent unnecessary cloud costs.

---

## 4. Defect Severity Classification
Errors found during testing are categorized as follows:

* **S1 (Blocker):** Total system failure or data loss (e.g., Telemetry not reaching the cloud, or 10Hz buffer failing to capture $V_{min}$).
* **S2 (Major):** A core feature is non-functional (e.g., Battery health is miscalculated due to incorrect $V_{crit}$ selection or Vampire Drain Protection failing to stop polling).
* **S3 (Minor):** UI/UX glitches, minor translation errors in the "Mechanic-Translator," or notification timing issues.

---

## 5. Exit Criteria (Definition of Done)
The testing phase is considered complete only when:

1. **100% of Critical and High priority** test cases (TCs), including the new Adaptive Sampling and Battery Protection cases, have passed.
2. **Zero open S1 or S2 defects** remain in the bug tracker.
3. **Code Coverage** for the analytical algorithms (**SOH with temperature compensation**, Driver Scoring, and Vampire Drain Protection) reaches a minimum of **90%**.
4. **Validation of Safety Logic:** **(v1.3 Update)** Successful verification that the system does not drain the vehicle battery below **11.5V** while the engine is OFF.
5. **Regression Testing** is successful, ensuring that high-frequency sampling hasn't impacted the stability of standard "Mechanic-Translator" lookups.
