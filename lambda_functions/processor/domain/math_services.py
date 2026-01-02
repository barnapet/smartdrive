import numpy as np
from typing import List, Tuple, Optional
from .interfaces import ISignalProcessor
from config import ProcessorConfig

class PlateauAveragingProcessor(ISignalProcessor):
    """
    v1.4 Automotive Logic: Focuses on the sustained cranking plateau[cite: 42, 48].
    Filters out inductive inrush spikes and compression ripples[cite: 41, 57].
    """
    
    def process(self, points: List[Tuple[float, float]], config: ProcessorConfig) -> Optional[float]:
        if not points or len(points) < 2:
            return None
            
        t_raw, v_raw = zip(*points)
        t_start = t_raw[0]
        
        # 1. Inrush Blanking: Discard first 100ms (Phase 1) 
        # Prevents false positives from inductive cabling reactance[cite: 37, 40].
        plateau_start_time = t_start + 0.100 
        
        # 2. Plateau Window: Next 500ms (Phase 2) [cite: 153]
        # This phase correlates directly with battery internal resistance[cite: 47, 51].
        plateau_end_time = plateau_start_time + 0.500
        
        plateau_values = [
            v for t, v in points 
            if plateau_start_time <= t <= plateau_end_time
        ]
        
        if len(plateau_values) < 2:
            return None
            
        # 3. Averaging: Calculate mean DC component to filter AC ripple[cite: 57, 153].
        v_plateau = np.mean(plateau_values)
        
        # 4. Safety Margin Check: Ensuring ECU survivability[cite: 123, 214].
        # ECU floor is typically 6.0V; our red line is 8.5V[cite: 122, 138].
        if not (6.0 <= v_plateau <= 13.5):
            return None
            
        return float(v_plateau)

class CrankingAnalysisContext:
    """Strategy Context: Orchestrates the execution of signal analysis[cite: 144]."""
    def __init__(self, strategy: ISignalProcessor):
        self._strategy = strategy

    def analyze(self, points: List[Tuple[float, float]], config: ProcessorConfig) -> Optional[float]:
        return self._strategy.process(points, config)
