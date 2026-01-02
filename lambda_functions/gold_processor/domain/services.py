from typing import Tuple, List
from .interfaces import ITemperatureProvider

class BatteryHealthService:
    @staticmethod
    def get_adjusted_threshold(base_v: float, temp_c: float) -> float:
        # Kutatás alapú hőmérséklet-kompenzáció
        return base_v - (0.018 * (25.0 - temp_c))

    @staticmethod
    def evaluate_battery(soh: float, soc: float, vmin: float, temp_c: float) -> dict:
        # SOC Validációs kapu: 70% alatt nem megbízható a mérés
        if soc < 70.0:
            return {"status": "INCONCLUSIVE", "alerts": ["Alacsony SOC: Töltés szükséges."], "is_valid": False}

        # Küszöbök számítása korrekcióval
        v_pass = BatteryHealthService.get_adjusted_threshold(9.6, temp_c)
        v_fail = BatteryHealthService.get_adjusted_threshold(8.5, temp_c)

        # SOH Monitor szintek
        if vmin < v_fail or soh < 65.0:
            return {"status": "CRITICAL", "alerts": ["Azonnali csere szükséges!"], "is_valid": True}
        elif vmin < v_pass or soh < 80.0:
            return {"status": "WARNING", "alerts": ["Az akkumulátor gyengül."], "is_valid": True}
        
        return {"status": "OK", "alerts": [], "is_valid": True}

class TemperatureResolver:
    def __init__(self, api_provider: ITemperatureProvider):
        self.api_provider = api_provider

    def resolve(self, payload: dict) -> Tuple[float, str]:
        if payload.get('intake_temp') is not None:
            return float(payload['intake_temp']), "OBD_IAT"
        api_temp = self.api_provider.get_temperature(payload)
        return (api_temp, "WEATHER_API") if api_temp is not None else (25.0, "DEFAULT")
