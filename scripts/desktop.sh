#!/bin/sh
set -eu
export LIBGL_ALWAYS_SOFTWARE=1
export ALSOFT_DRIVERS=null
python - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
target = Path.home() / '.torcs/config/screen.xml'
target.parent.mkdir(parents=True, exist_ok=True)
tree = ET.parse('/usr/local/share/games/torcs/config/screen.xml')
props = tree.getroot().find("section[@name='Screen Properties']")
for name, value in [('x', '1280'), ('y', '800')]:
    props.find(f"attnum[@name='{name}']").set('val', value)
props.find("attstr[@name='fullscreen']").set('val', 'yes')
tree.write(target, encoding='UTF-8', xml_declaration=True)
PY
# Let Xvfb choose a free display, including after an unclean VM shutdown.
display_file=$(mktemp)
Xvfb -displayfd 3 -screen 0 1280x800x24 +extension GLX -nolisten tcp 3>"$display_file" &
xvfb_pid=$!
trap 'rm -f "$display_file"; kill "$xvfb_pid"; exit' INT TERM EXIT
attempt=0
until [ -s "$display_file" ]; do
    attempt=$((attempt + 1))
    if ! kill -0 "$xvfb_pid" 2>/dev/null; then echo "X display stopped during startup" >&2; exit 1; fi
    if [ "$attempt" -gt 50 ]; then echo "X display failed to start" >&2; exit 1; fi
    sleep 0.1
done
DISPLAY=:$(cat "$display_file")
export DISPLAY
rm -f "$display_file"
attempt=0
until xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -gt 50 ]; then echo "X display failed to start" >&2; exit 1; fi
    sleep 0.1
done
openbox > /tmp/openbox.log 2>&1 &
x11vnc -display "$DISPLAY" -localhost -rfbport 5900 -forever -shared -nopw > /tmp/vnc.log 2>&1 &
websockify --web /usr/share/novnc 6080 localhost:5900 > /tmp/novnc.log 2>&1 &
python -m scripts.gateway &
gateway_pid=$!
trap 'kill "$gateway_pid" "$xvfb_pid"; exit' INT TERM EXIT
wait "$gateway_pid"
