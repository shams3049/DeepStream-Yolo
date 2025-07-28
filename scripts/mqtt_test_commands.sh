#!/bin/bash

# MQTT Testing Commands
# Various ways to test MQTT message reception

echo "🔍 MQTT TESTING METHODS"
echo "======================"
echo

# Check if mosquitto clients are installed
if ! command -v mosquitto_sub &> /dev/null; then
    echo "📦 Installing mosquitto clients..."
    sudo apt-get update
    sudo apt-get install -y mosquitto-clients
    echo
fi

echo "Available testing methods:"
echo

echo "1️⃣  SUBSCRIBE TO ALL TOPICS"
echo "   mosquitto_sub -h mqtt-proxy.ad.dicodrink.com -p 1883 \\"
echo "     -u r_vmays -P 'csYr9xH&WTfAvMj2' \\"
echo "     -t '+' -v"
echo

echo "2️⃣  SUBSCRIBE TO SPECIFIC CAMERA"
echo "   mosquitto_sub -h mqtt-proxy.ad.dicodrink.com -p 1883 \\"
echo "     -u r_vmays -P 'csYr9xH&WTfAvMj2' \\"
echo "     -t 'camera1' -v"
echo

echo "3️⃣  SUBSCRIBE TO HEALTH STATUS"
echo "   mosquitto_sub -h mqtt-proxy.ad.dicodrink.com -p 1883 \\"
echo "     -u r_vmays -P 'csYr9xH&WTfAvMj2' \\"
echo "     -t 'deepstream/health' -v"
echo

echo "4️⃣  PYTHON SUBSCRIBER TEST (Recommended)"
echo "   python3 scripts/test_mqtt_subscriber.py"
echo

echo "5️⃣  CONTINUOUS MONITORING WITH JSON PARSING"
echo "   mosquitto_sub -h mqtt-proxy.ad.dicodrink.com -p 1883 \\"
echo "     -u r_vmays -P 'csYr9xH&WTfAvMj2' \\"
echo "     -t '+' | jq ."
echo

echo "Choose a method and run the command!"
echo "Press Ctrl+C to stop monitoring"
