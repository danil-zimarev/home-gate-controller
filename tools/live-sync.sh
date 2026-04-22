#!/bin/bash
PORT=/dev/ttyACM0

mpremote connect $PORT fs cp -r src/* :
mpremote connect $PORT exec "import main"
