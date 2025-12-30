import time
import os
import sys
import logging

# Ensure the project root is in the python path even if run from scripts/ folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.src.providers.real import RealOBDProvider

# Configure logging to see internal python-obd messages
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_diagnostic():
    # 1. Environment Check
    if os.getenv("SMARTDRIVE_MODE") != "REAL":
        print("\n❌ ERROR: SMARTDRIVE_MODE is not set to REAL!")
        print("Run: export SMARTDRIVE_MODE=REAL")
        return

    vin = "TEST-VIN-2025-REAL"
    # Using the manually created RFCOMM port
    target_port = "/dev/rfcomm0"
    provider = RealOBDProvider(vin=vin, port=target_port) 

    print("\n" + "="*60)
    print("🚀 SMARTDRIVE REAL MODE - HARDWARE DIAGNOSTIC TOOL")
    print(f"Target Port: {target_port}")
    print("="*60)

    # 2. Connection Loop
    while not provider.connect():
        print(f"⏳ Retrying in 5 seconds... (Press Ctrl+C to cancel)")
        time.sleep(5)

    print("\n✅ Connection stable. Starting live data stream...\n")
    print(f"{'Time':<10} | {'Voltage':<12} | {'RPM':<10} | {'Temp':<8} | {'Speed':<10}")
    print("-" * 70)

    try:
        # 3. Data Acquisition Loop
        while True:
            data = provider.fetch_data()
            
            if data:
                # Format time and status
                timestamp = time.strftime("%H:%M:%S", time.localtime(data.timestamp))
                
                # Visual indicator for battery/alternator health
                # (Charging usually > 13.2V)
                v_status = "🔋" if data.voltage > 13.2 else "🪫" 
                
                # Using carriage return (\r) to update the same line
		output = (
		    f"{timestamp:<10} | {v_status} {data.voltage:>6.2f}V | "
		    f"{data.rpm:>7.0f} | "
		    f"{data.coolant_temp:>6.0f}°C | "
		    f"{data.speed:>6.1f} km/h"
		)
		print(output, end='\r')
            else:
                print("\n⚠️ Data drop detected or waiting for ECU response...", end='\r')

            # Sleep to prevent overwhelming the ELM327 chip
            time.sleep(5) 

    except KeyboardInterrupt:
        print("\n\n🛑 Diagnostic stopped by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error during diagnostic: {e}")

if __name__ == "__main__":
    run_diagnostic()
