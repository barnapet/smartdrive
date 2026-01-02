import time
import os
import sys
import logging

# Biztosítjuk, hogy a projekt gyökere benne legyen a python útvonalban
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.src.providers.real import RealOBDProvider

# Konstansok szinkronizálva a v1.3-as specifikációval
V_VAMPIRE_THRESHOLD = 11.5  #
CRANKING_RPM_LIMIT = 600    #
CRANKING_POLL_RATE = 0.1    # 10Hz a pontos Vmin méréshez
STEADY_POLL_RATE = 0.5      # 2Hz diagnosztikához

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_diagnostic():
    if os.getenv("SMARTDRIVE_MODE") != "REAL":
        print("\n❌ ERROR: SMARTDRIVE_MODE is not set to REAL!")
        return

    vin = "TEST-VIN-2025-REAL"
    target_port = "/dev/rfcomm0"
    provider = RealOBDProvider(vin=vin, port=target_port) 

    print("\n" + "="*70)
    print("🚀 SMARTDRIVE ADAPTIVE SAMPLING - IGNITION PRIORITY MODE")
    print(f"Threshold: {V_VAMPIRE_THRESHOLD}V | Cranking/Ready: 10Hz")
    print("="*70)

    while not provider.connect():
        print(f"⏳ Retrying in 5 seconds...")
        time.sleep(5)

    print("\n✅ Connection stable. Monitoring states...")
    print(f"{'Time':<10} | {'Hz':<6} | {'Voltage':<10} | {'RPM':<8} | {'Mode':<15}")
    print("-" * 70)

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

                v_icon = "🟢" if data.voltage >= 13.0 else ("🟡" if data.voltage >= V_VAMPIRE_THRESHOLD else "🔴 LOW!")
                
                # --- ÚJ ADAPTÍV LOGIKA ---
                # ... a ciklus belsejében
                if data.rpm < CRANKING_RPM_LIMIT:
                    mode = "🏎️  READY/CRANK"
                    sleep_time = CRANKING_POLL_RATE
                    # PRÓBÁLD KI: Nyers feszültségmérés a Hz növeléséhez
                    raw_v = provider.fetch_raw_voltage()
                    if raw_v > 0:
                        # Frissítjük a data objektum feszültségét a nyers értékkel
                        # (Ehhez a TelemetryData-nak nem szabad frozen=True-nak lennie, 
                        # vagy új objektumot kell létrehozni)
                        pass

                if data.rpm >= CRANKING_RPM_LIMIT:
                    # Motor jár: normál üzemi mintavétel
                    mode = "🛣️  STEADY"
                    sleep_time = STEADY_POLL_RATE

                elif data.rpm == 0 and data.voltage < V_VAMPIRE_THRESHOLD:
                    # Nincs gyújtás ÉS alacsony feszültség: takarékos mód
                    mode = "💤 PWR SAVE"
                    sleep_time = 1.0

                elif data.rpm < CRANKING_RPM_LIMIT:
                    # IDE TARTOZIK: Gyújtás ON (RPM=0) és a tényleges indítás (0<RPM<600)
                    # Amint van adat (gyújtás ráadva), 10Hz-re kapcsolunk!
                    mode = "🏎️  READY/CRANK"
                    sleep_time = CRANKING_POLL_RATE
                
                else:
                    mode = "🅿️  PARKED"
                    sleep_time = 1.0

                timestamp = time.strftime("%H:%M:%S")
                output = (
                    f"{timestamp:<10} | {actual_hz:>4.1f} | "
                    f"{v_icon} {data.voltage:>5.2f}V | "
                    f"{data.rpm:>7.0f} | {mode:<15}"
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
