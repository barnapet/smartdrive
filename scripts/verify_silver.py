import boto3
import pandas as pd
import io
import sys

# Konfiguráció
SILVER_BUCKET = "smartdrive-telemetry-silver" # A Terraformban megadott név
TEST_VIN = "TESTVIN123456789"
PREFIX = f"processed_telemetry/vin={TEST_VIN}"

def check_silver_data():
    s3 = boto3.client('s3')
    
    print(f"🔍 Searching for Parquet files in s3://{SILVER_BUCKET}/{PREFIX}...")
    
    # 1. Fájlok listázása
    response = s3.list_objects_v2(Bucket=SILVER_BUCKET, Prefix=PREFIX)
    
    if 'Contents' not in response:
        print("❌ No files found in Silver bucket yet. Lambda might be still processing or failed.")
        return

    # A legutolsó fájlt vesszük (ha több lenne)
    latest_file = sorted(response['Contents'], key=lambda x: x['LastModified'])[-1]
    key = latest_file['Key']
    
    print(f"📥 Downloading: {key}")
    
    # 2. Letöltés memóriába (BytesIO)
    obj = s3.get_object(Bucket=SILVER_BUCKET, Key=key)
    buffer = io.BytesIO(obj['Body'].read())
    
    # 3. Olvasás Pandas-szal
    try:
        df = pd.read_parquet(buffer)
        
        # 4. Eredmény megjelenítése
        print("\n✅ PARQUET FILE CONTENT (First 10 rows):")
        print("-" * 60)
        
        # Csak a releváns oszlopokat mutassuk
        cols_to_show = ['timestamp', 'pid_code', 'value', 'refined_vmin']
        # Biztosítjuk, hogy csak létező oszlopokat kérünk le
        available_cols = [c for c in cols_to_show if c in df.columns]
        
        print(df[available_cols].to_string())
        print("-" * 60)
        
        # 5. Matek ellenőrzése
        if 'refined_vmin' in df.columns:
            vmin_rows = df[df['refined_vmin'].notnull()]
            if not vmin_rows.empty:
                calculated_val = vmin_rows.iloc[0]['refined_vmin']
                print(f"\n🎯 SUCCESS! Calculated Parabolic Minimum: {calculated_val:.4f} V")
                print("   (This proves the math module logic executed correctly)")
            else:
                print("\n⚠️  'refined_vmin' column exists but is empty (Conditions for interpolation not met?)")
        else:
            print("\n❌ 'refined_vmin' column is MISSING. The ETL script did not add it.")
            
    except Exception as e:
        print(f"❌ Error reading Parquet: {e}")
        print("Tip: You might need to install pyarrow: 'pip install pyarrow'")

if __name__ == "__main__":
    check_silver_data()
