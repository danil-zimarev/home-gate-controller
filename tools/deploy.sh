#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <serial_port>"
    echo "Example: $0 /dev/ttyACM0"
    exit 1
fi
PORT="$1"

sleep 1
echo "Cleaning device filesystem..."
mpremote connect "$PORT" fs rm -r :

echo "Deploying to $PORT..."
echo "Uploading new files..."
sleep 1
mpremote connect "$PORT" fs cp -r src/* :

echo "Starting main..."
sleep 1
mpremote connect "$PORT" exec "import main"

echo "Done."