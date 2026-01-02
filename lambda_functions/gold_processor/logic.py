import os
import json
from datetime import datetime
from infrastructure.repositories import DynamoDBInsightRepository
from infrastructure.external_apis import OpenMeteoWeatherProvider
from domain.services import TemperatureResolver, BatteryHealthService

def handler(event, context):
    # Inicializálás - Nincs szükség Secrets Managerre az Open-Meteo-hoz
    repo = DynamoDBInsightRepository(os.environ['INSIGHTS_TABLE'])
    weather_svc = OpenMeteoWeatherProvider()
    temp_resolver = TemperatureResolver(weather_svc)
    battery_svc = BatteryHealthService()

    for record in event.get('Records', []):
        try:
            data = json.loads(record.get('body', '{}'))
            vin = data.get('vin')
            vmin = data.get('refined_vmin')
            soh = data.get('soh')
            soc = data.get('soc', 100)
            
            if not vin or vmin is None:
                continue

            # 1. Hőmérséklet feloldása (Open-Meteo fallback-kel)
            temp_now, source = temp_resolver.resolve(data)
            
            # 2. SOH Diagnózis -18mV/°C korrekcióval
            diag = battery_svc.evaluate_battery(soh, soc, vmin, temp_now)
            
            # 3. Debounce logika: 3 egymást követő hiba ellenőrzése
            history = repo.get_last_insights(vin, 2)
            consecutive_fails = 1 if diag['status'] == "CRITICAL" else 0
            for h in history:
                if h.get('health_status') == "CRITICAL":
                    consecutive_fails += 1
            
            # 4. Winter Survival Pack (24h előrejelzés)
            forecast_min = weather_svc.get_forecast_min(data.get('lat'), data.get('lon'))
            winter_alert = (forecast_min is not None and forecast_min < 0 and (soh < 85 or soc < 60))

            # 5. Eredmények mentése a Gold Layer-be
            repo.save_insight({
                'vin': vin,
                'timestamp': datetime.utcnow().isoformat(),
                'health_status': diag['status'],
                'confirmed_failure': consecutive_fails >= 3,
                'winter_survival_alert': winter_alert,
                'measured_temp': temp_now,
                'temp_source': source,
                'soc_at_test': soc,
                'battery_vmin': vmin
            })
            
        except Exception as e:
            print(f"Error processing record for VIN {vin}: {e}")

    return {"status": "success"}
