import boto3
import pandas as pd
import io
import sys

# Konfiguráció
SILVER_BUCKET = "smartdrive-telemetry-silver"
TEST_VIN = "TESTVIN123456789"
# A dátumot a logjaid alapján állítom be (ma)
PREFIX = f"processed_telemetry/vin={TEST_VIN}"

def check_all_silver_files():
    s3 = boto3.client('s3')
    
    print(f"🔍 Scanning ALL files in s3://{SILVER_BUCKET}/{PREFIX}...\n")
    
    response = s3.list_objects_v2(Bucket=SILVER_BUCKET, Prefix=PREFIX)
    if 'Contents' not in response:
        print("❌ No files found.")
        return

    found_valid_crank = False
    files = sorted(response['Contents'], key=lambda x: x['LastModified'])

    print(f"📂 Found {len(files)} files. Checking for cranking data...\n")

    for obj_meta in files:
        key = obj_meta['Key']
        
        # Csak a ma délutáni fájlokat nézzük (optimalizálás)
        # Ha sok fájl van, ez gyorsítja
        
        try:
            # Letöltés memóriába
            obj = s3.get_object(Bucket=SILVER_BUCKET, Key=key)
            buffer = io.BytesIO(obj['Body'].read())
            df = pd.read_parquet(buffer)
            
            # Keresünk olyan sort, ahol a refined_vmin NEM üres
            if 'refined_vmin' in df.columns:
                valid_rows = df[df['refined_vmin'].notnull()]
                
                if not valid_rows.empty:
                    print(f"✅ FOUND CRANKING EVENT in file: {key.split('/')[-1]}")
                    print("-" * 60)
                    print(valid_rows[['timestamp', 'pid_code', 'value', 'refined_vmin']].to_string())
                    print("-" * 60)
                    print(f"🎯 Calculated V_min: {valid_rows.iloc[0]['refined_vmin']:.4f} V")
                    found_valid_crank = True
                    # Nem break-elünk, hátha több indítás is volt
        
        except Exception as e:
            print(f"⚠️ Error reading {key}: {e}")

    if not found_valid_crank:
        print("\n❌ Scanned all files, but no valid cranking logic was triggered.")
        print("Tip: Did the voltage drop below the previous measurement? (Convex parabola required)")

if __name__ == "__main__":
    check_all_silver_files()
