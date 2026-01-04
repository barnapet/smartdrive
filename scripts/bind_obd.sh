#!/bin/bash

# scripts/bind_obd.sh - SmartDrive Auto-Bind Tool (v1.5)

echo "🔍 Scanning for OBD-II Bluetooth devices..."

# Megkeressük az OBDII nevű eszköz MAC címét
MAC_ADDRESS=$(hcitool scan | grep "OBDII" | awk '{print $1}')

if [ -z "$MAC_ADDRESS" ]; then
    echo "❌ ERROR: No 'OBDII' device found. Is it paired and in range?"
    exit 1
fi

echo "✅ Found OBD-II at: $MAC_ADDRESS"

# Ellenőrizzük, hogy létezik-e már a bind
if [ -e /dev/rfcomm0 ]; then
    echo "⚠️  /dev/rfcomm0 already exists. Releasing..."
    sudo rfcomm release 0
fi

echo "🔗 Binding $MAC_ADDRESS to /dev/rfcomm0..."
sudo rfcomm bind 0 "$MAC_ADDRESS"

if [ $? -eq 0 ]; then
    echo "✨ SUCCESS! You can now run diagnostics."
    ls -l /dev/rfcomm0
else
    echo "❌ Failed to bind device."
fi
