import requests
from typing import Optional
from domain.interfaces import ITemperatureProvider

class OpenMeteoWeatherProvider(ITemperatureProvider):
    def __init__(self, cache_repo=None):
        self.cache_repo = cache_repo

    def get_temperature(self, payload: dict) -> Optional[float]:
        lat, lon = payload.get('lat'), payload.get('lon')
        if not (lat and lon): return None
        
        if self.cache_repo:
            cached = self.cache_repo.get_cached_weather(lat, lon)
            if cached: return float(cached['temperature'])        
        
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                temp = float(resp.json()['current']['temperature_2m'])
                
                if self.cache_repo:
                    self.cache_repo.save_weather(lat, lon, temp, None)
                return temp
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
    def get_forecast_min(self, lat: float, lon: float) -> Optional[float]:
        if self.cache_repo:
            cached = self.cache_repo.get_cached_weather(lat, lon)
            if cached and cached.get('forecast_min') is not None:
                return float(cached['forecast_min'])

        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&forecast_days=1"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                temps = resp.json()['hourly']['temperature_2m']
                min_temp = min(temps)
                
                if self.cache_repo:
                    self.cache_repo.save_weather(lat, lon, min_temp, min_temp) 
                return min_temp
        except Exception as e:
            print(f"Open-Meteo Forecast error: {e}")
        return None    except Exception as e:
            print(f"Open-Meteo Forecast error: {e}")
        return None
