from dataclasses import dataclass

@dataclass(frozen=True)
class TelemetryData:
    vin: str
    timestamp: int
    speed: float
    rpm: float
    voltage: float
    coolant_temp: float
