import requests
from typing import Optional
from domain.interfaces import ITemperatureProvider

class OpenMeteoWeatherProvider(ITemperatureProvider):
    """
    Ingyenes Open-Meteo alapú időjárás szolgáltató.
    Nincs szükség API kulcsra.
    """
    def __init__(self):
        pass

    def get_temperature(self, payload: dict) -> Optional[float]:
        lat, lon = payload.get('lat'), payload.get('lon')
        if not (lat and lon): return None
        
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                return float(resp.json()['current']['temperature_2m'])
        except Exception as e:
            print(f"Open-Meteo API error: {e}")
        return None

    def get_forecast_min(self, lat: float, lon: float) -> Optional[float]:
        """
        Winter Survival Pack előrejelzés: a következő 24 óra minimuma.
        """
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&forecast_days=1"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                temps = resp.json()['hourly']['temperature_2m']
                return min(temps)
        except Exception as e:
            print(f"Open-Meteo Forecast error: {e}")
        return None
