# System Design: Algorithms & Logic Plan

**Version:** 1.1
**Date:** December 2025
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Document Status:** Detailed Logic Specification
**Author:** Peter Barna

---

# System Design: Algorithms & Logic Plan (v1.1)

---

## 1. Mechanic‑Translator (Hybrid DTC Interpretation)
This algorithm is responsible for translating diagnostic trouble codes (DTCs) into human‑readable explanations, combining deterministic databases with Generative AI capabilities.

### 1.1 Multi‑Tier Lookup Logic
The system searches for an explanation using the following hierarchy:

1. **Tier 1: SAE Standard Library (L1 Cache):**  
   The software includes a built‑in JSON database containing standard P0xxx codes.

2. **Tier 2: DynamoDB Global Cache (L2):**  
   If the code is non‑standard (e.g., manufacturer‑specific), the system queries the cloud‑based global cache, which stores previously translated codes.

3. **Tier 3: LLM Fallback (gpt‑4o‑mini):**  
   If no match is found, the system calls the OpenAI API with a context‑aware prompt (vehicle model + code).  
   The returned explanation is immediately saved into Tier 2 for future requests.

### 1.2 Severity & Action Logic
Each interpretation is assigned a severity level based on the following categories:

* **Critical (Red):** Immediate stop required.  
  AI prompt keyword: *"immediate safety risk"*.

* **Warning (Yellow):** Service recommended within 500 km.  
  AI prompt keyword: *"preventive maintenance"*.

* **Informative (Blue):** Non‑critical comfort or auxiliary system issue.  
  AI prompt keyword: *"non-critical"*.

---

## 2. Battery Health Prediction (SOH)
This model analyzes the voltage drop during the engine cranking phase to predict failure before it occurs.

### 2.1 Mathematical Model
Battery internal resistance ($R_i$) increases with degradation. We monitor the relationship between the cranking voltage drop ($V_{drop}$) and the starting current ($I_{start}$):

$$V_{start} = V_{ocv} - (I_{start} \cdot R_i)$$

Where $V_{ocv}$ is the Open Circuit Voltage. Since not all OBD-II dongles measure current ($I_{start}$), we track the **relative voltage drop trend** over time ($t$):

$$SOH\% = 100 \cdot \left( 1 - \frac{V_{min, t} - V_{min, t-n}}{V_{min, t-n}} \right)$$

### 2.2 Logic Rule
If the $V_{min}$ (minimum cranking voltage) consistently falls below **9.6V** at standard temperatures, the system triggers a "Battery Replacement Recommended" alert.



---

## 3. Driver Scoring Model (Gamification)
This is an aggregated KPI that scales user performance from 0 to 100 points.

### 3.1 Calculation of the Score ($S$)
The score is composed of three main pillars with specific weightings ($w$):
* **Emergency Braking ($B$):** Occurrences of deceleration $> 0.3g$ per 100 km.
* **Intense Acceleration ($A$):** Occurrences of acceleration $> 0.25g$ per 100 km.
* **Idling ($I$):** Ratio of engine runtime while stationary vs. total trip duration.

$$S = 100 - (w_B \cdot \text{B-count} + w_A \cdot \text{A-count} + w_I \cdot \text{Idle-ratio})$$

*Weights are optimized for safety; emergency braking triggers the highest point deduction.*



---

## 4. Winter Survival Pack (Context-Aware Logic)
An event-driven logic designed to prevent "cold start" failures.

### 4.1 Trigger Mechanism
* **Trigger:** Ambient temperature retrieved from Weather API is **< 0°C**.
* **Condition:** AND Battery State of Health (**SOH**) is **< 70%**.
* **Action:** Send a Push Notification: *"Warning! Due to freezing temperatures, your battery may fail tomorrow morning. We recommend a health check or charging today."*
