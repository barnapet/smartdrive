# System Design: Algorithms & Logic Plan

**Version:** 1.4
**Date:** Jan 2026
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Document Status:** Detailed Logic Specification
**Author:** Peter Barna
**Status:** Updated with v1.4 $V_{min}$ Refinement

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

### 2.1 Mathematical Model & Signal Processing (v1.4 Update)
To ensure accuracy and avoid false positives from inductive inrush spikes (Phase 1), the system implements a **100ms Moving Average Filter**[cite: 150, 217].

**Voltage Plateau Calculation:**
1. **Inrush Blanking:** Discard the first 100ms of data after starter engagement to ignore the "Hammer Blow" dip.
2. **Plateau Averaging:** Calculate the mean voltage over the subsequent 500ms (Phase 2) to determine the true $V_{min\_plateau}$.
3. **Temperature Compensation:** Adjust the critical threshold using a linear model (-18mV/°C):
   $$V_{crit\_adj} = V_{crit\_25C} - 0.018 \cdot (25 - T_{amb})$$

### 2.2 Decision Logic & Thresholds (v1.4 Optimized)
**Validation Gates:**
* **SOC Gate:** If State of Charge (**SOC**) < 70%, the SOH measurement is marked as "Inconclusive" to avoid false failures due to a discharged battery.
* **Debounce Logic:** A "Critical" status is only confirmed after **3 consecutive driving cycles** failing the threshold.

**SOH Monitoring Matrix (at 25°C):**
* **Yellow Alert (Warning):** SOH < 80%. (Message: "Battery life is nearing its end. Plan a check.")
* **Red Alert (Critical):** SOH < 65-70%. (Message: "Critical battery state. Immediate replacement required.")

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

### 4.1 Winter Survival Pack (Proactive Logic)
* **Trigger:** Forecasted temperature < 0°C within 24 hours.
* **Condition:** AND Battery **SOH < 85%** (higher safety margin for cold viscosity).
* **Safety Condition:** OR **SOC < 60%** (prevents electrolyte freezing).
* **Timing:** Alert sent 24 hours prior to forecasted freeze.
