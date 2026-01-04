import os
import json
from datetime import datetime
from infrastructure.repositories import DynamoDBInsightRepository
from infrastructure.external_apis import OpenMeteoWeatherProvider
from domain.services import TemperatureResolver, BatteryHealthService

def handler(event, context):
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
            fuel_type = data.get('fuel_type', 'gasoline')
            coolant_temp = data.get('coolant_temp')

            if not vin or vmin is None:
                continue

            temp_now, source = temp_resolver.resolve(data)
            cold_start_flag = battery_svc.is_cold_start(temp_now, coolant_temp)
            diag = battery_svc.evaluate_battery(soh, soc, vmin, temp_now)
            
            history = repo.get_last_insights(vin, 2)
            consecutive_fails = 1 if diag['status'] == "CRITICAL" else 0
            for h in history:
                if h.get('health_status') == "CRITICAL":
                    consecutive_fails += 1
            
            forecast_min = weather_svc.get_forecast_min(data.get('lat'), data.get('lon'))
            winter_alert = (forecast_min is not None and forecast_min < 0 and (soh < 85 or soc < 60))

            repo.save_insight({
                'vin': vin,
                'timestamp': datetime.utcnow().isoformat(),
                'health_status': diag['status'],
                'is_cold_start': cold_start_flag,
                'confirmed_failure': consecutive_fails >= 3,
                'winter_survival_alert': winter_alert,
                'measured_temp': temp_now,
                'temp_source': source,
                'fuel_type_at_test': fuel_type,
                'soc_at_test': soc,
                'battery_vmin': vmin
            })
            
        except Exception as e:
            print(f"Error processing record for VIN {vin}: {e}")

    return {"status": "success"}
