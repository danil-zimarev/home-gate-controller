#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <serial_port>"
    echo "Example: $0 /dev/ttyACM0"
    exit 1
fi
PORT="$1"


PYTHON="$(pwd)/.venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

echo "Minifing index.html..."
$PYTHON -c "
import minify_html, sys
path = 'src/www/index.html'
html = open(path, 'r').read()
minified = minify_html.minify(html, minify_js=True, minify_css=True)
open(path, 'w').write(minified)
print(f'  {len(html)} -> {len(minified)} bytes ({100 - len(minified)*100//len(html)}% reduction)')
" || { echo "minify-html not installed, run: pip3 install minify-html"; exit 1; }


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