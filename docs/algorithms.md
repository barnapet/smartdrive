# System Design: Algorithms & Logic Plan

**Version:** 1.3
**Date:** Jan 2026
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Document Status:** Detailed Logic Specification
**Author:** Peter Barna
**Status:** Updated with v1.3 $V_{min}$ Refinement and 11.5V Safety Logic

---

## 1. Mechanic‑Translator (Hybrid DTC Interpretation)
This algorithm is responsible for translating diagnostic trouble codes (DTCs) into human‑readable explanations, combining deterministic databases with Generative AI capabilities.

### 1.1 Multi‑Tier Lookup Logic
The system searches for an explanation using the following hierarchy:

1. **Tier 1: SAE Standard Library (L1 Cache):** The software includes a built‑in JSON database containing standard P0xxx codes.
2. **Tier 2: DynamoDB Global Cache (L2):** If the code is non‑standard (e.g., manufacturer‑specific), the system queries the cloud‑based global cache, which stores previously translated codes.
3. **Tier 3: LLM Fallback (gpt‑4o‑mini):** If no match is found, the system calls the OpenAI API with a context‑aware prompt (vehicle model + code). The returned explanation is immediately saved into Tier 2 for future requests.

### 1.2 Severity & Action Logic
Each interpretation is assigned a severity level based on the following categories:
* **Critical (Red):** Immediate stop required.  
* **Warning (Yellow):** Service recommended within 500 km.  
* **Informative (Blue):** Non‑critical comfort or auxiliary system issue.  

---

## 2. Battery Health Prediction (SOH)
This model analyzes the voltage drop during the engine cranking phase to predict failure before it occurs.

### 2.1 Mathematical Model & Data Capture (v1.3 Update)
Battery internal resistance ($R_i$) increases with degradation. We monitor the relationship between the cranking voltage drop ($V_{drop}$) and the starting current ($I_{start}$):

$$V_{start} = V_{ocv} - (I_{start} \cdot R_i)$$

**High-Fidelity Capture Strategy:**
1.  **Ignition-Priority Trigger:** High-frequency sampling (Target: 10Hz) starts immediately at **Ignition ON (RPM=0)** to capture the full transient curve.
2.  **Numerical Refinement (Parabolic Interpolation):** Since hardware latency may limit actual sampling to 3-6 Hz, the system applies a parabolic fit (Quadratic Interpolation) to the lowest measured points to estimate the true $V_{min}$ between samples.

**Relative Trend Tracking:**
$$SOH\% = 100 \cdot \left( 1 - \frac{V_{min, t} - V_{min, t-n}}{V_{min, t-n}} \right)$$

### 2.2 Logic Rules (v1.3 Update)
* **Health Alert:** If the refined $V_{min}$ consistently falls below **9.6V** at standard temperatures, a "Battery Replacement Recommended" alert is triggered.
* **Vampire Drain Protection (Safety):** If the vehicle is Parked (RPM=0) and $V_{ocv}$ falls below **11.5V**, all polling is suspended to prevent deep discharge.

---

## 3. Driver Scoring Model (Gamification)
This is an aggregated KPI that scales user performance from 0 to 100 points.

### 3.1 Calculation of the Score ($S$)
The score is composed of three main pillars with specific weightings ($w$):
* **Emergency Braking ($B$):** Occurrences of deceleration $> 0.3g$ per 100 km.
* **Intense Acceleration ($A$):** Occurrences of acceleration $> 0.25g$ per 100 km.
* **Idling ($I$):** Ratio of engine runtime while stationary vs. total trip duration.

$$S = 100 - (w_B \cdot \text{B-count} + w_A \cdot \text{A-count} + w_I \cdot \text{Idle-ratio})$$

---

## 4. Winter Survival Pack (Context-Aware Logic)
An event-driven logic designed to prevent "cold start" failures.

### 4.1 Trigger Mechanism
* **Trigger:** Ambient temperature retrieved from Weather API is **< 0°C**.
* **Condition:** AND Battery State of Health (**SOH**) is **< 70%**.
* **Action:** Send a Push Notification: *"Warning! Due to freezing temperatures, your battery may fail tomorrow morning. We recommend a health check or charging today."*
