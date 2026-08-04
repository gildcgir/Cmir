#!/usr/bin/env bash
# Cmir — Pixel lab via adb reverse (persistent lab via launchctl)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ADB="${ADB:-$HOME/Library/Android/sdk/platform-tools/adb}"
ANDROID_DIR="$ROOT/apps/android"

if [[ -z "${JAVA_HOME:-}" || ! -x "${JAVA_HOME}/bin/java" ]]; then
  if [[ -x "/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/java" ]]; then
    export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
  fi
fi
export PATH="${JAVA_HOME:+$JAVA_HOME/bin:}$HOME/Library/Android/sdk/platform-tools:$PATH"

ensure_lab_launchctl() {
  export CMIR_ENV="${CMIR_ENV:-test}"
  export CMIR_WORKER_TOKEN="${CMIR_WORKER_TOKEN:-cmir-lab-worker-token}"
  export CMIR_DATA_KEY="${CMIR_DATA_KEY:-cmir-lab-data-key-not-for-prod}"
  export CMIR_ADMIN_PASSWORD="${CMIR_ADMIN_PASSWORD:-admin}"

  if ! curl -sf -m 2 http://127.0.0.1:8090/health >/dev/null; then
    echo "==> Starting API via launchctl"
    launchctl remove com.cmir.lab.api 2>/dev/null || true
    pkill -f "apps/api_py/server.py" 2>/dev/null || true
    sleep 0.3
    launchctl submit -l com.cmir.lab.api -- \
      /usr/bin/env CMIR_ENV="$CMIR_ENV" CMIR_WORKER_TOKEN="$CMIR_WORKER_TOKEN" \
      CMIR_DATA_KEY="$CMIR_DATA_KEY" CMIR_ADMIN_PASSWORD="$CMIR_ADMIN_PASSWORD" \
      /usr/bin/python3 "$ROOT/apps/api_py/server.py"
  fi

  if ! curl -sf -m 2 -o /dev/null http://127.0.0.1:3000/; then
    echo "==> Starting Web via launchctl"
    launchctl remove com.cmir.lab.web 2>/dev/null || true
    pkill -f "http.server 3000" 2>/dev/null || true
    sleep 0.3
    ln -sfn "$ROOT/apps/web/kiosk" "$ROOT/apps/consent-kiosk"
    launchctl submit -l com.cmir.lab.web -- \
      /usr/bin/python3 -m http.server 3000 --bind 127.0.0.1 --directory "$ROOT/apps/web"
  fi

  sleep 1
  curl -sf -m 2 http://127.0.0.1:8090/health >/dev/null && echo "  API OK" || {
    echo "API still down"; exit 1
  }
  curl -sf -m 2 -o /dev/null http://127.0.0.1:3000/ && echo "  Web OK" || {
    echo "Web still down"; exit 1
  }
}

mkdir -p "$ANDROID_DIR/app/src/debug/res/values"
cat >"$ANDROID_DIR/app/src/debug/res/values/strings.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="cmir_web_base">http://127.0.0.1:3000/</string>
</resources>
EOF

echo "==> Ensure lab (launchctl)"
ensure_lab_launchctl

echo "==> Devices"
"$ADB" start-server
"$ADB" devices -l
COUNT="$("$ADB" devices | awk 'NR>1 && $2=="device" {c++} END{print c+0}')"
if [[ "$COUNT" -lt 1 ]]; then
  echo "Pixel не подключён."
  exit 2
fi

echo "==> adb reverse"
"$ADB" reverse --remove-all 2>/dev/null || true
"$ADB" reverse tcp:3000 tcp:3000
"$ADB" reverse tcp:8090 tcp:8090
"$ADB" reverse --list

# Sanity: phone localhost → Mac (needs toybox wget/curl; skip if missing)
echo "==> installDebug + clear + launch"
(cd "$ANDROID_DIR" && ./gradlew installDebug)
"$ADB" shell pm clear com.cmir.app.debug >/dev/null
"$ADB" shell am start -n com.cmir.app.debug/com.cmir.app.MainActivity

echo ""
echo "ВАЖНО: в debug-режиме нужен USB + adb reverse."
echo "  Без USB телефон не достучится до http://127.0.0.1:3000 на Mac → чёрный экран."
echo "  После каждого переподключения кабеля снова запустите:"
echo "    adb reverse tcp:3000 tcp:3000 && adb reverse tcp:8090 tcp:8090"
echo "  или целиком: bash scripts/android-lab-pixel.sh"
echo ""
echo "На Pixel должно открыться http://127.0.0.1:3000/ через USB reverse."
echo "Остановка lab: launchctl remove com.cmir.lab.api; launchctl remove com.cmir.lab.web"
