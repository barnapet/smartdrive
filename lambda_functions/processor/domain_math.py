import numpy as np
from typing import List, Tuple, Optional
from config import ProcessorConfig

class ParabolicInterpolator:
    """
    Numerikus analízis modul.
    Felelősség: Pontokból csúcspontot (minimumot) számolni.
    """
    
    @staticmethod
    def find_vertex(points: List[Tuple[float, float]], config: ProcessorConfig) -> Optional[float]:
        t_raw, v = zip(*points)
        # Idő eltolása 0-hoz a numerikus stabilitás érdekében (Time Shift)
        t0 = t_raw[1] 
        t = np.array(t_raw) - t0

        # Lagrange interpoláció nevezője
        denom = (t[0] - t[1]) * (t[0] - t[2]) * (t[1] - t[2])
        if denom == 0: return None

        # Együtthatók számítása (y = Ax^2 + Bx + C)
        A = (t[2] * (v[1] - v[0]) + t[1] * (v[0] - v[2]) + t[0] * (v[2] - v[1])) / denom
        B = (t[2]**2 * (v[0] - v[1]) + t[1]**2 * (v[2] - v[0]) + t[0]**2 * (v[1] - v[2])) / denom

        # Csak konvex parabola (völgy) esetén interpolálunk
        if A <= config.convexity_threshold:
            return None

        # Csúcspont helye relatív időben
        t_vertex_rel = -B / (2 * A)
        
        # Csúcspont értéke
        C = v[0] - A * t[0]**2 - B * t[0]
        v_vertex = A * t_vertex_rel**2 + B * t_vertex_rel + C

        # Sanity check: Nem lehet sokkal mélyebb, mint a mért minimum
        if v_vertex < min(v) - config.max_voltage_drop_diff:
            return None
            
        return float(v_vertex)
