import pandas as pd
from config import ProcessorConfig
from domain_math import ParabolicInterpolator
from repository import S3Repository

class ETLService:
    def __init__(self, repo: S3Repository, config: ProcessorConfig):
        self.repo = repo
        self.config = config

    def _enrich_battery_health(self, df: pd.DataFrame) -> pd.DataFrame:
        """Kiszámolja és hozzáadja a 'refined_vmin' oszlopot."""
        if 'pid_code' not in df.columns: 
            return df
        
        df_out = df.copy()
        df_out['refined_vmin'] = None
        
        # Feszültség adatok kiválasztása
        v_mask = df_out['pid_code'] == 'BATTERY_VOLTAGE'
        v_data = df_out[v_mask].sort_values('timestamp')

        if len(v_data) >= self.config.min_points_for_interpolation:
            min_idx = v_data['value'].idxmin()
            
            try:
                # A minimum érték indexének pozíciója a szűrt listában
                loc_idx = v_data.index.get_loc(min_idx)
                
                # Ha van bal és jobb szomszéd
                if 0 < loc_idx < len(v_data) - 1:
                    subset = v_data.iloc[loc_idx-1 : loc_idx+2]
                    
                    # Adatok konvertálása a matek modul számára
                    # .view('int64') a gyorsabb numpy hozzáférésért
                    points = list(zip(
                        subset['timestamp'].view('int64') / self.config.time_unit_divisor,
                        subset['value']
                    ))
                    
                    refined_val = ParabolicInterpolator.find_vertex(points, self.config)
                    
                    if refined_val:
                        df_out['refined_vmin'] = refined_val
                        
            except (KeyError, ValueError):
                pass 
                
        return df_out

    def process_file(self, bucket: str, key: str):
        # 1. Betöltés
        df = self.repo.fetch_json_as_df(bucket, key)
        if df.empty: return

        # 2. Transzformáció (Dátum oszlop a particionáláshoz)
        if 'timestamp' in df.columns and 'date' not in df.columns:
            df['date'] = df['timestamp'].dt.date.astype(str)

        # 3. Gazdagítás (Üzleti logika)
        df_enriched = self._enrich_battery_health(df)

        # 4. Mentés
        self.repo.save_dataframe_to_parquet(
            df_enriched, 
            prefix=self.config.silver_prefix, 
            compression=self.config.parquet_compression
        )
        print(f"ETL Success: {key} -> Parquet")
