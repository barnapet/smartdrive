#!/bin/bash

# --- CONFIGURATION (Based on SDD and Terraform) ---
THING_NAME="TESTVIN123456789"
POLICY_NAME="SmartDriveVehiclePolicy"
CERTS_DIR="certs"

echo "🚗 Starting SmartDrive Vehicle Registration: $THING_NAME"

# 1. Create certs directory (if it doesn't exist)
mkdir -p $CERTS_DIR
cd $CERTS_DIR

echo "🔐 Generating certificates in AWS IoT Core..."
# Creating certificates and keys according to the DevOps plan
CERT_OUTPUT=$(aws iot create-keys-and-certificate \
    --set-as-active \
    --certificate-pem-outfile "certificate.pem.crt" \
    --public-key-outfile "public.pem.key" \
    --private-key-outfile "private.pem.key")

# Extracting the ARN for successful attachment
CERT_ARN=$(echo $CERT_OUTPUT | grep -o '"certificateArn": "[^"]*' | cut -d'"' -f4)

if [ -z "$CERT_ARN" ]; then
    echo "❌ ERROR: Failed to generate certificate. Please check your AWS CLI authentication!"
    exit 1
fi

echo "✅ Certificate created: $CERT_ARN"

# 2. Attach Policy (To the SmartDriveVehiclePolicy created in Terraform)
echo "📝 Attaching permissions (Policy)..."
aws iot attach-policy --policy-name $POLICY_NAME --target $CERT_ARN

# 3. Attach Thing (To the TESTVIN123456789 resource created in Terraform)
echo "🔗 Mapping certificate to the vehicle (Thing)..."
aws iot attach-thing-principal --thing-name $THING_NAME --principal $CERT_ARN

# 4. Download Amazon Root CA for secure network connection
if [ ! -f "AmazonRootCA1.pem" ]; then
    echo "📥 Downloading Amazon Root CA..."
    curl -o AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem
fi

echo "✨ DONE! Certificates are located in the hardware/certs/ folder."
echo "🚀 You can now start main.py!"
