import time
import os
import sys
import logging

# Biztosítjuk, hogy a projekt gyökere benne legyen a python útvonalban
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.src.providers.real import RealOBDProvider

# Konstansok szinkronizálva a v1.5-ös specifikációval
V_VAMPIRE_THRESHOLD = 11.5  
V_CRITICAL_FLOOR = 9.0      # ECU brownout határ
CRANKING_RPM_LIMIT = 600    
CRANKING_POLL_RATE = 0.1    # 10Hz a pontos Vmin méréshez
STEADY_POLL_RATE = 0.5      
SENTINEL_PULSE_RATE = 600.0 # v1.5: 10 perces ciklus Deep Sleep-ben

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_diagnostic():
    if os.getenv("SMARTDRIVE_MODE") != "REAL":
        print("\n❌ ERROR: SMARTDRIVE_MODE is not set to REAL!")
        return

    vin = "TEST-VIN-2025-REAL"
    target_port = "/dev/rfcomm0"
    provider = RealOBDProvider(vin=vin, port=target_port) 

    # --- Állapotváltozók a Vmin számításhoz ---
    cranking_start_time = None
    cranking_samples = []
    vmin_plateau = None

    print("\n" + "="*70)
    print("🚀 SMARTDRIVE v1.5 - SMART GUARD & BATTERY DIAGNOSTICS")
    print(f"Threshold: {V_VAMPIRE_THRESHOLD}V | Sentinel Pulse: {SENTINEL_PULSE_RATE}s")
    print("="*70)

    while not provider.connect():
        print(f"⏳ Retrying in 5 seconds...")
        time.sleep(5)

    print("\n✅ Connection stable. Monitoring states...")
    print(f"{'Time':<10} | {'Hz':<6} | {'Voltage':<10} | {'Vmin':<8} | {'Mode':<15}")
    print("-" * 75)

    last_time = time.time()
    frame_count = 0
    actual_hz = 0.0

    try:
        while True:
            data = provider.fetch_data()
            
            if data:
                frame_count += 1
                now = time.time()
                
                if now - last_time >= 1.0:
                    actual_hz = frame_count / (now - last_time)
                    frame_count = 0
                    last_time = now

                # --- 1. NYERS FESZÜLTSÉG FRISSÍTÉS (IMPLEMENTÁLVA) ---
                if data.rpm < CRANKING_RPM_LIMIT:
                    raw_v = provider.fetch_raw_voltage()
                    if raw_v > 0:
                        data.voltage = raw_v # Az objektum frissítése a pontosabb méréshez

                # --- 3. VMIN PLATEAU SZÁMÍTÁS (IMPLEMENTÁLVA) ---
                if 0 < data.rpm < CRANKING_RPM_LIMIT:
                    if cranking_start_time is None:
                        cranking_start_time = time.time()
                        cranking_samples = []
                        vmin_plateau = None
                    
                    elapsed = time.time() - cranking_start_time
                    # 100ms blanking, majd 500ms gyűjtés (Phase 2)
                    if 0.1 <= elapsed <= 0.6:
                        cranking_samples.append(data.voltage)
                    elif elapsed > 0.6 and cranking_samples and vmin_plateau is None:
                        vmin_plateau = sum(cranking_samples) / len(cranking_samples)
                
                elif data.rpm >= CRANKING_RPM_LIMIT:
                    cranking_start_time = None # Reset indítás után

                # --- ÜZEMMÓD ÉS ALVÁS LOGIKA ---
                v_icon = "🟢" if data.voltage >= 13.0 else ("🟡" if data.voltage >= V_VAMPIRE_THRESHOLD else "🔴 LOW!")
                
                if data.rpm >= CRANKING_RPM_LIMIT:
                    mode = "🛣️  STEADY"
                    sleep_time = STEADY_POLL_RATE

                elif data.rpm == 0 and data.voltage < V_VAMPIRE_THRESHOLD:
                    # --- 2. SMART GUARD SENTINEL (IMPLEMENTÁLVA) ---
                    mode = "💤 SENTINEL"
                    sleep_time = SENTINEL_PULSE_RATE # 10 perces ébredés
                    print(f"\n⚠️ Critical voltage ({data.voltage}V). Entering Pulse Monitoring...")

                elif data.rpm < CRANKING_RPM_LIMIT:
                    mode = "🏎️  READY/CRANK"
                    sleep_time = CRANKING_POLL_RATE
                
                else:
                    mode = "🅿️  PARKED"
                    sleep_time = 1.0

                timestamp = time.strftime("%H:%M:%S")
                vmin_str = f"{vmin_plateau:>5.2f}V" if vmin_plateau else "---"
                output = (
                    f"{timestamp:<10} | {actual_hz:>4.1f} | "
                    f"{v_icon} {data.voltage:>5.2f}V | "
                    f"{vmin_str:<8} | {mode:<15}"
                )
                print(output, end='\r')
                
                time.sleep(sleep_time)
            else:
                print("\n⚠️ Connection lost. Reconnecting...", end='\r')
                provider.connect()
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Diagnostic stopped.")

if __name__ == "__main__":
    run_diagnostic()
