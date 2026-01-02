import json
from config import ProcessorConfig
from domain.math_services import CrankingAnalysisContext, PlateauAveragingProcessor
# from infrastructure.repository import SilverRepository (Feltételezett repo kód)

def lambda_handler(event, context):
    config = ProcessorConfig()
    
    # Stratégia kiválasztása (Lead-Acid / AGM alapértelmezett)
    # v1.4: Plateau Averaging is the current industry standard for SOH[cite: 63, 209].
    strategy = PlateauAveragingProcessor()
    analyzer = CrankingAnalysisContext(strategy)
    
    for record in event.get('Records', []):
        # 1. Adat kinyerése
        payload = json.loads(record['body'])
        points = payload.get('voltage_samples', []) # (timestamp, voltage) list
        
        # 2. Jelfeldolgozás (Domain Layer)
        v_min_refined = analyzer.analyze(points, config)
        
        if v_min_refined:
            print(f"Validated Plateau Voltage: {v_min_refined}V [cite: 48]")
            # 3. Mentés a Silver Layer-be (Infrastructure Layer)
            # repo.save_to_silver(vin, v_min_refined, payload)
            
    return {"status": "processed"}
