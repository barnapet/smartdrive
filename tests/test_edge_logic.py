import time
import unittest
from unittest.mock import MagicMock
from hardware.src.app import SmartDriveMonitor
from hardware.src.providers.simulated import SimulatedOBDProvider
from hardware.src.domain import TelemetryData

class TestEdgeLogic(unittest.TestCase):
    def setUp(self):
        self.vin = "TEST-VIN-999"
        self.publisher = MagicMock()
        self.provider = SimulatedOBDProvider(self.vin)
        self.monitor = SmartDriveMonitor(self.provider, self.publisher)

    def test_vampire_drain_protection_trigger(self):
        """
        TC-6: Verify that polling stops when voltage drops below 12.1V.
       
        """
        print("\n🔍 Testing Vampire Drain Protection (FR11)...")
        # Force low voltage
        self.provider.is_engine_running = False
        low_voltage_data = TelemetryData(self.vin, int(time.time()), 0, 0, 11.9, 20.0)
        
        self.monitor._handle_battery_protection(low_voltage_data.voltage)
        
        self.assertTrue(self.monitor.power_saving_active)
        self.assertEqual(self.monitor.current_interval, 1800.0)
        print("✅ Success: Power Saving Mode activated at 11.9V.")

    def test_vampire_drain_recovery(self):
        """
        FR11: Verify that polling resumes when voltage reaches 13.0V.
       
        """
        print("🔍 Testing Vampire Drain Recovery...")
        self.monitor.power_saving_active = True
        
        self.monitor._handle_battery_protection(13.1)
        
        self.assertFalse(self.monitor.power_saving_active)
        self.assertEqual(self.monitor.current_interval, 5.0)
        print("✅ Success: Normal operation resumed at 13.1V.")

    def test_adaptive_sampling_cranking(self):
        """
        FR4: Verify 10Hz sampling during cranking phase (0 < RPM < 600).
       
        """
        print("🔍 Testing Adaptive Sampling - Cranking Phase...")
        self.monitor._adjust_sampling_rate(rpm=350.0)
        
        self.assertEqual(self.monitor.current_interval, 0.1)
        print("✅ Success: High-speed sampling (10Hz) active during cranking.")

    def test_adaptive_sampling_steady_state(self):
        """
        FR4: Verify 0.2Hz sampling during steady state (RPM >= 600).
       
        """
        print("🔍 Testing Adaptive Sampling - Steady State...")
        self.monitor._adjust_sampling_rate(rpm=2200.0)
        
        self.assertEqual(self.monitor.current_interval, 5.0)
        print("✅ Success: 0.2Hz sampling active during steady state.")

if __name__ == "__main__":
    unittest.main()
