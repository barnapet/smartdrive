import logging
from .providers import SimulatedOBDProvider, RealOBDProvider
from .app import SmartDriveMonitor

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    VIN = "TESTVIN123456789"
    MODE = "SIMULATED"
    
    if MODE == "REAL":
        provider = RealOBDProvider(VIN)
    else:
        provider = SimulatedOBDProvider(VIN)
        
    monitor = SmartDriveMonitor(provider)
    monitor.start()

if __name__ == "__main__":
    main()
