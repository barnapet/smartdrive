from dataclasses import dataclass

@dataclass
class ProcessorConfig:
    # Matematikai beállítások
    min_points_for_interpolation: int = 3
    convexity_threshold: float = 1e-6
    max_voltage_drop_diff: float = 0.5
    time_unit_divisor: int = 1_000_000_000  # Nanosec -> Sec
    
    # Storage beállítások
    parquet_compression: str = "snappy"
    silver_prefix: str = "processed_telemetry"
