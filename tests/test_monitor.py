import unittest
from unittest.mock import MagicMock, patch
import json
from hardware.src.app import SmartDriveMonitor
from hardware.src.domain import TelemetryData

class TestSmartDriveMonitor(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_publisher = MagicMock()
        self.monitor = SmartDriveMonitor(self.mock_provider, self.mock_publisher)

    def test_publish_calls_publisher_with_correct_data(self):
        test_data = TelemetryData(
            vin="TESTVIN123",
            timestamp=1640995200,
            speed=50.0,
            rpm=2500.0,
            voltage=14.1
        )
        
        self.monitor._publish(test_data)
        expected_topic = "vehicle/TESTVIN123/telemetry"
        self.assertTrue(self.mock_publisher.publish.called)
        args, _ = self.mock_publisher.publish.call_args
        self.assertEqual(args[0], expected_topic)
        sent_payload = json.loads(args[1])
        self.assertEqual(sent_payload['vin'], "TESTVIN123")
        self.assertEqual(sent_payload['speed'], 50.0)

    def test_monitor_stops_on_connection_failure(self):
        self.mock_provider.connect.return_value = False
        self.monitor.start()
        self.assertFalse(self.monitor.is_running)
