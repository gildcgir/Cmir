# Cmir Android

WebView-оболочка для Google Play. Публикация: [PLAY_STORE.md](PLAY_STORE.md).

## Lab на Pixel 7 (USB)

1. На Mac: API/web — `bash scripts/start-lab.sh` (или уже подняты :3000 / :8090).
2. На телефоне: Developer options → **USB debugging**.
3. USB-кабель → Allow debugging.
4. Один раз открой в Android Studio папку `apps/android` (Gradle Sync → появится `gradlew`).
5. Потом:

```bash
bash scripts/android-lab-pixel.sh
```

Debug-сборка сама использует `http://127.0.0.1:3000/` + `adb reverse` (см. `app/src/debug/.../strings.xml`).  
Release по-прежнему смотрит на `https://app.cmir.live/`.

```bash
# вручную
$HOME/Library/Android/sdk/platform-tools/adb devices
$HOME/Library/Android/sdk/platform-tools/adb reverse tcp:3000 tcp:3000
$HOME/Library/Android/sdk/platform-tools/adb reverse tcp:8090 tcp:8090
```
