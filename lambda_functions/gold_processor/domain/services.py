from typing import Tuple, List
from .interfaces import ITemperatureProvider

class BatteryHealthService:
    @staticmethod
    def get_adjusted_threshold(base_v: float, temp_c: float) -> float:
        return base_v - (0.018 * (25.0 - temp_c))

    @staticmethod
    def get_soh_thresholds(temp_c: float, fuel_type: str) -> tuple:
        is_diesel = fuel_type.lower() == "diesel"
        
        if temp_c > 20.0:
            return (80.0, 65.0 if is_diesel else 60.0)
        elif 0.0 <= temp_c <= 20.0:
            return (80.0, 75.0 if is_diesel else 70.0)
        elif -10.0 <= temp_c < 0.0:
            return (85.0 if is_diesel else 80.0, 80.0 if is_diesel else 75.0)
        else:
            return (90.0 if is_diesel else 85.0, 85.0 if is_diesel else 80.0)

    @staticmethod
    def evaluate_battery(soh: float, soc: float, vmin: float, temp_c: float) -> dict:
        if soc < 70.0:
            return {"status": "INCONCLUSIVE", "alerts": ["Alacsony SOC: Töltés szükséges."], "is_valid": False}

        v_pass = BatteryHealthService.get_adjusted_threshold(9.6, temp_c)
        v_fail = BatteryHealthService.get_adjusted_threshold(8.5, temp_c)

        if vmin < v_fail or soh < 65.0:
            return {"status": "CRITICAL", "alerts": ["Azonnali csere szükséges!"], "is_valid": True}
        elif vmin < v_pass or soh < 80.0:
            return {"status": "WARNING", "alerts": ["Az akkumulátor gyengül."], "is_valid": True}
        
        return {"status": "OK", "alerts": [], "is_valid": True}

    @staticmethod
    def is_cold_start(temp_c: float, coolant_temp: float = None) -> bool:
        if coolant_temp is not None:
            return coolant_temp < 30.0 and abs(coolant_temp - temp_c) < 5.0
        return temp_c < 10.0

class TemperatureResolver:
    def __init__(self, api_provider: ITemperatureProvider):
        self.api_provider = api_provider

    def resolve(self, payload: dict) -> Tuple[float, str]:
        if payload.get('intake_temp') is not None:
            return float(payload['intake_temp']), "OBD_IAT"
        api_temp = self.api_provider.get_temperature(payload)
        return (api_temp, "WEATHER_API") if api_temp is not None else (25.0, "DEFAULT")
