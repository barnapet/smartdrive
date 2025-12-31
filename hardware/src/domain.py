from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TelemetryData:
    """
    Standardized telemetry model for the SmartDrive ecosystem.
    Supports high-frequency sampling (10Hz) and analytics.
    """
    vin: str             # Vehicle Identification Number
    timestamp: int       # Unix timestamp (seconds)
    speed: float         # Vehicle speed in km/h
    rpm: float           # Engine revolutions per minute
    voltage: float       # Battery voltage (critical for SOH and Vampire Drain)
    coolant_temp: float  # Engine coolant temperature
    
    # Optional fields for future scaling (e.g., G-sensor for Driver Scoring)
    accel_x: Optional[float] = 0.0 #
    accel_y: Optional[float] = 0.0 #
