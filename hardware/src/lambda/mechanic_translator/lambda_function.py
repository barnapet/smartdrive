import json
import boto3
import os
import re
from openai import OpenAI

# AWS Resource Initialization
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

# Environment variables configured via Terraform
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'DTC_Global_Cache')
MODEL_NAME = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
table = dynamodb.Table(TABLE_NAME)

def get_secret():
    """Fetches the OpenAI API key from AWS Secrets Manager."""
    secret_name = "smartdrive/openai-key"
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])['api_key']
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise e

def build_response(code, desc, sev, is_ai):
    """Standardizes the output format for the mobile application."""
    return {
        'dtc_id': code,
        'description': desc,
        'severity': sev,
        'is_ai_generated': is_ai
    }

def lambda_handler(event, context):
    """Main entry point for interpreting Diagnostic Trouble Codes (DTC)."""
    vin = event.get('vin', 'UNKNOWN')
    model = event.get('model_info', 'Unknown Vehicle')
    dtc_code = event.get('dtc_code')

    if not dtc_code:
        return {"error": "No DTC code provided"}

    # --- TIER 1: SAE Standard Library (Local Cache) ---
    standard_codes = {
        "P0101": "Mass Air Flow Sensor Circuit Range/Performance",
        "P0300": "Random or Multiple Cylinder Misfire Detected"
    }
    if dtc_code in standard_codes:
        return build_response(dtc_code, standard_codes[dtc_code], "WARNING", False)

    # --- TIER 2: DynamoDB Global Cache (L2) ---
    try:
        cache_result = table.get_item(Key={'dtc_id': dtc_code})
        if 'Item' in cache_result:
            return cache_result['Item']
    except Exception as e:
        print(f"DynamoDB lookup failed: {e}")

    # --- TIER 3: OpenAI Fallback (Generative Interpretation) ---
    api_key = get_secret()
    client = OpenAI(api_key=api_key)
    
    # Strict instructions to ensure structured JSON output
    system_prompt = (
        "You are a professional automotive diagnostic expert. "
        "Provide a clear, human-readable explanation in Hungarian. "
        "Respond ONLY with a valid JSON object containing: "
        "'description' (Hungarian text) and 'severity' (CRITICAL/WARNING/INFO)."
    )
    user_prompt = f"VIN: {vin}, Model: {model}, DTC: {dtc_code}. Interpret this fault for a non-technical car owner."
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}  # Forces JSON output mode
        )
        
        # Parse AI response safely
        raw_content = response.choices[0].message.content
        ai_data = json.loads(raw_content)
        
        # Use .get() to prevent KeyError
        description = ai_data.get('description', 'No description available.')
        severity = ai_data.get('severity', 'INFO')

        # Update Tier 2 Cache (Self-Learning Mechanism)
        table.put_item(Item={
            'dtc_id': dtc_code,
            'description': description,
            'severity': severity,
            'is_ai_generated': True
        })
        
        return build_response(dtc_code, description, severity, True)

    except Exception as e:
        print(f"AI Interpretation failed: {e}")
        return build_response(dtc_code, "Internal diagnostic error. Please consult a mechanic.", "WARNING", False)
