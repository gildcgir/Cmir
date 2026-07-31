# Cmir — исходники `apps/` для ревью

Сгенерировано: 2026-07-31 16:11 UTC

Репозиторий: https://github.com/gildcgir/Cmir

## Идея проекта (кратко)

Cmir — карта live-мест с privacy-first маскированием лиц. Киоск согласия снимает multi-pose профиль лица; на потоках зарегистрированным маска не ставится, остальным — ставится. Стек: Python API + SQLite, JS web/kiosk, MediaPipe face-worker, MediaMTX ingest, Android WebView shell.

## Оглавление файлов

1. `apps/admin/index.html` (9472 bytes)
2. `apps/android/PLAY_STORE.md` (2076 bytes)
3. `apps/android/README.md` (214 bytes)
4. `apps/android/app/build.gradle.kts` (1085 bytes)
5. `apps/android/app/src/main/AndroidManifest.xml` (1564 bytes)
6. `apps/android/app/src/main/java/com/cmir/app/MainActivity.kt` (3022 bytes)
7. `apps/android/app/src/main/res/values/strings.xml` (250 bytes)
8. `apps/android/app/src/main/res/values/themes.xml` (142 bytes)
9. `apps/android/app/src/main/res/xml/network_security_config.xml` (493 bytes)
10. `apps/android/build.gradle.kts` (142 bytes)
11. `apps/android/gradle.properties` (111 bytes)
12. `apps/android/settings.gradle.kts` (322 bytes)
13. `apps/api/Cargo.toml` (522 bytes)
14. `apps/api/src/domain.rs` (2839 bytes)
15. `apps/api/src/error.rs` (896 bytes)
16. `apps/api/src/main.rs` (1044 bytes)
17. `apps/api/src/routes.rs` (2868 bytes)
18. `apps/api/src/store.rs` (10540 bytes)
19. `apps/api_py/auth.py` (1736 bytes)
20. `apps/api_py/camera_health.py` (2759 bytes)
21. `apps/api_py/compliance.py` (7607 bytes)
22. `apps/api_py/database.py` (13273 bytes)
23. `apps/api_py/face_profiles.py` (2514 bytes)
24. `apps/api_py/local_relay.py` (15773 bytes)
25. `apps/api_py/platforms.py` (4466 bytes)
26. `apps/api_py/preview_buffer.py` (6153 bytes)
27. `apps/api_py/server.py` (56965 bytes)
28. `apps/api_py/store.py` (84749 bytes)
29. `apps/api_py/stream_paths.py` (4695 bytes)
30. `apps/api_py/stream_recorder.py` (3401 bytes)
31. `apps/consent-kiosk/index.html` (23463 bytes)
32. `apps/face-worker/README.md` (475 bytes)
33. `apps/face-worker/cmir_face/__init__.py` (60 bytes)
34. `apps/face-worker/cmir_face/avatar_sprite.py` (5235 bytes)
35. `apps/face-worker/cmir_face/embeddings.py` (6768 bytes)
36. `apps/face-worker/cmir_face/eye_mask.py` (7254 bytes)
37. `apps/face-worker/cmir_face/face_box.py` (1990 bytes)
38. `apps/face-worker/cmir_face/privacy_gate.py` (1962 bytes)
39. `apps/face-worker/cmir_face/rtmp_writer.py` (2133 bytes)
40. `apps/face-worker/cmir_face/rtsp_capture.py` (2428 bytes)
41. `apps/face-worker/cmir_face/tracker.py` (3695 bytes)
42. `apps/face-worker/cmir_face/worker.py` (14881 bytes)
43. `apps/face-worker/requirements.txt` (150 bytes)
44. `apps/ingest/docker-compose.yml` (457 bytes)
45. `apps/ingest/mediamtx.yml` (989 bytes)
46. `apps/web/admin.html` (8655 bytes)
47. `apps/web/css/app.css` (10165 bytes)
48. `apps/web/index.html` (6366 bytes)
49. `apps/web/js/admin.js` (31812 bytes)
50. `apps/web/js/api.js` (1820 bytes)
51. `apps/web/js/face-enroll.js` (4777 bytes)
52. `apps/web/js/live-camera.js` (21636 bytes)
53. `apps/web/js/mask-preview.js` (9418 bytes)
54. `apps/web/js/stream-player.js` (3243 bytes)
55. `apps/web/js/user.js` (27112 bytes)
56. `apps/web/performance.html` (14022 bytes)
57. `apps/web/stream.html` (3678 bytes)

---

## `apps/admin/index.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cmir Admin — POI &amp; камеры</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, sans-serif;
      background: #121820;
      color: #e8ecf0;
      padding: 1.5rem;
      max-width: 960px;
      margin: 0 auto;
    }
    h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .sub { opacity: 0.7; font-size: 0.9rem; margin-bottom: 1.5rem; }
    section {
      background: #1c2430;
      border: 1px solid #2e3d52;
      border-radius: 12px;
      padding: 1rem 1.25rem;
      margin-bottom: 1rem;
    }
    h2 { font-size: 1rem; color: #7eb8ff; margin-bottom: 0.75rem; }
    label { display: block; font-size: 0.8rem; opacity: 0.85; margin: 0.5rem 0 0.2rem; }
    input, select, textarea {
      width: 100%;
      padding: 0.45rem 0.6rem;
      border-radius: 8px;
      border: 1px solid #3a4d66;
      background: #0f1419;
      color: #fff;
      font-size: 0.95rem;
    }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    button {
      margin-top: 0.75rem;
      padding: 0.5rem 1rem;
      border: none;
      border-radius: 8px;
      background: #3d9ae8;
      color: #0a1018;
      font-weight: 600;
      cursor: pointer;
      margin-right: 0.5rem;
    }
    button.secondary { background: #3a4d66; color: #e8ecf0; }
    button.danger { background: #c44; color: #fff; }
    .poi-card {
      border: 1px solid #2e3d52;
      border-radius: 10px;
      padding: 0.75rem;
      margin-top: 0.75rem;
    }
    .cam {
      font-size: 0.85rem;
      padding: 0.5rem 0;
      border-top: 1px solid #2e3d52;
      margin-top: 0.5rem;
    }
    .badge {
      display: inline-block;
      font-size: 0.7rem;
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      background: #2d4a6f;
      margin-right: 0.35rem;
    }
    .health-ok { color: #5dcea0; }
    .health-bad { color: #f88; }
    a { color: #7eb8ff; }
    #log {
      font-family: ui-monospace, monospace;
      font-size: 0.75rem;
      white-space: pre-wrap;
      max-height: 160px;
      overflow: auto;
      margin-top: 0.5rem;
      opacity: 0.9;
    }
  </style>
</head>
<body>
  <h1>Cmir Admin</h1>
  <p class="sub">
    Фаза 1 — registry POI и камер.
    <a href="../docs/GOPRO13.md">GoPro HERO13</a> ·
    <a href="../web/index.html">Главная</a>
  </p>

  <section>
    <h2>API</h2>
    <label>Base URL</label>
    <input type="text" id="apiBase" value="http://localhost:8090" />
  </section>

  <section>
    <h2>Создать POI</h2>
    <label>Название</label>
    <input id="poiName" placeholder="Pilot: GoPro lab" />
    <div class="row">
      <div>
        <label>Тип</label>
        <select id="poiType">
          <option value="social_event">social_event (≥2 cam, ≥1 consent)</option>
          <option value="live_cam">live_cam</option>
          <option value="venue">venue (≥3 cam, ≥2 consent)</option>
        </select>
      </div>
      <div>
        <label>Промо-текст</label>
        <input id="poiPromo" placeholder="Описание для промо-режима" />
      </div>
    </div>
    <div class="row">
      <div>
        <label>Широта</label>
        <input id="poiLat" type="number" step="any" value="41.7151" />
      </div>
      <div>
        <label>Долгота</label>
        <input id="poiLng" type="number" step="any" value="44.8271" />
      </div>
    </div>
    <div class="row">
      <div>
        <label>Город</label>
        <input id="poiCity" value="Tbilisi" />
      </div>
      <div>
        <label>Страна (ISO)</label>
        <input id="poiCountry" value="GE" maxlength="2" />
      </div>
    </div>
    <button type="button" id="btnCreatePoi">Создать POI</button>
  </section>

  <section>
    <h2>Добавить камеру к POI</h2>
    <label>POI</label>
    <select id="camPoiSelect"></select>
    <label>Имя</label>
    <input id="camName" placeholder="GoPro General" />
    <label>Stream URL</label>
    <input id="camUrl" placeholder="rtsp://127.0.0.1:8554/gopro_main" />
    <p style="font-size:0.75rem;opacity:0.65;margin-top:0.25rem;">
      GoPro через MediaMTX: rtmp publish → <code>gopro_main</code> → читать
      <code>rtsp://127.0.0.1:8554/gopro_main</code>
    </p>
    <div class="row">
      <div>
        <label>Роль</label>
        <select id="camRole">
          <option value="general">general</option>
          <option value="consent">consent</option>
        </select>
      </div>
      <div>
        <label>Режим (view_mode)</label>
        <select id="camViewMode">
          <option value="standard">standard</option>
          <option value="fisheye">fisheye</option>
          <option value="zoom2x">zoom2x</option>
        </select>
      </div>
    </div>
    <button type="button" id="btnAddCam">Добавить камеру</button>
  </section>

  <section>
    <h2>Зарегистрированные POI</h2>
    <button type="button" class="secondary" id="btnRefresh">Обновить</button>
    <div id="poiList"></div>
    <pre id="log"></pre>
  </section>

  <script>
    const api = () => document.getElementById('apiBase').value.replace(/\/$/, '');
    const log = (msg) => {
      const el = document.getElementById('log');
      el.textContent = new Date().toISOString().slice(11, 19) + ' ' + msg + '\n' + el.textContent;
    };

    async function loadPois() {
      const res = await fetch(`${api()}/api/v1/pois`);
      const json = await res.json();
      const pois = json.data || [];
      const sel = document.getElementById('camPoiSelect');
      sel.innerHTML = pois.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
      const list = document.getElementById('poiList');
      list.innerHTML = pois.map(p => renderPoi(p)).join('');
      return pois;
    }

    function renderPoi(p) {
      const cams = (p.cameras || []).map(c => `
        <div class="cam" data-cam-id="${c.id}">
          <strong>${c.name}</strong>
          <span class="badge">${c.role}</span>
          <span class="badge">${c.view_mode}</span>
          ${c.is_active ? '' : '<span class="badge">off</span>'}
          <div style="opacity:0.75;margin:0.25rem 0;">${c.stream_url}</div>
          <button type="button" class="secondary" onclick="checkHealth('${c.id}')">Проверить поток</button>
          <button type="button" class="danger" onclick="deleteCam('${c.id}')">Удалить</button>
          <span id="health-${c.id}"></span>
        </div>
      `).join('');
      return `<div class="poi-card">
        <strong>${p.name}</strong> <span class="badge">${p.poi_type}</span>
        <div style="font-size:0.8rem;opacity:0.7;">${p.id}</div>
        ${cams || '<p style="opacity:0.6">Нет камер</p>'}
      </div>`;
    }

    window.checkHealth = async (camId) => {
      const res = await fetch(`${api()}/api/v1/cameras/${camId}/health`);
      const json = await res.json();
      const d = json.data || {};
      const el = document.getElementById(`health-${camId}`);
      const cls = d.status === 'reachable' ? 'health-ok' : 'health-bad';
      el.innerHTML = `<span class="${cls}"> ${d.status}: ${d.detail}</span>`;
      log(`health ${camId}: ${d.status}`);
    };

    window.deleteCam = async (camId) => {
      if (!confirm('Удалить камеру?')) return;
      await fetch(`${api()}/api/v1/cameras/${camId}`, { method: 'DELETE' });
      log(`deleted camera ${camId}`);
      loadPois();
    };

    document.getElementById('btnCreatePoi').onclick = async () => {
      const body = {
        name: document.getElementById('poiName').value,
        poi_type: document.getElementById('poiType').value,
        latitude: parseFloat(document.getElementById('poiLat').value),
        longitude: parseFloat(document.getElementById('poiLng').value),
        city: document.getElementById('poiCity').value,
        country: document.getElementById('poiCountry').value,
        promo_description: document.getElementById('poiPromo').value,
      };
      const res = await fetch(`${api()}/api/v1/pois`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      log(res.ok ? `POI created ${json.data?.id}` : `POI error: ${json.error}`);
      loadPois();
    };

    document.getElementById('btnAddCam').onclick = async () => {
      const poiId = document.getElementById('camPoiSelect').value;
      const body = {
        name: document.getElementById('camName').value,
        stream_url: document.getElementById('camUrl').value,
        role: document.getElementById('camRole').value,
        view_mode: document.getElementById('camViewMode').value,
      };
      const res = await fetch(`${api()}/api/v1/pois/${poiId}/cameras`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      log(res.ok ? `Camera ${json.data?.id}` : `Camera error: ${json.error}`);
      loadPois();
    };

    document.getElementById('btnRefresh').onclick = () => loadPois();
    loadPois().catch(e => log('API offline: ' + e.message));
  </script>
</body>
</html>
```

## `apps/android/PLAY_STORE.md`

````markdown
# Cmir Android — публикация в Google Play

## Что это
Нативный Android shell (`com.cmir.app`) с WebView: карта, киоск согласия (камера), аккаунт.
UI/логика — из веб-контура Cmir; приложение даёт доступ к камере и deep links.

## Перед загрузкой в Play Console
1. Замените `cmir_web_base` в `app/src/main/res/values/strings.xml` на production HTTPS URL.
2. Отключите cleartext в `network_security_config.xml` для prod (оставь только HTTPS).
3. Добавьте реальные иконки: `mipmap-*/ic_launcher` (1024×1024 → Adaptive Icon).
4. Privacy Policy URL (обязательно для CAMERA / biometrics): опубликуйте страницу и укажите в Play Console.
5. Data safety form: biometrics face templates, account phone/email, camera — «collected / processed».
6. Content rating questionnaire (IARC).
7. Подпишите AAB: `./gradlew bundleRelease` с upload key в Play App Signing.

## Сборка
```bash
cd apps/android
# Android Studio: Open this folder, sync Gradle, Build > Generate Signed Bundle
./gradlew assembleDebug
./gradlew bundleRelease
```

Lab на эмуляторе:
```bash
adb reverse tcp:3000 tcp:3000
adb reverse tcp:8090 tcp:8090
# временно cmir_web_base = http://10.0.2.2:3000/
```

## Листинг (черновик)
- Title: Cmir
- Short: Карта live-мест с приватностью лиц
- Full: Смотрите трансляции заведений, регистрируйте согласие на киоске, кошелёк ST/UT.
- Category: Social / Entertainment
- Screenshots: phone 1080×1920 — карта, киоск, эфир с маской

## Чеклист соответствия
- [ ] Target API 35+
- [ ] Camera permission rationale / in-app disclosure
- [ ] Privacy policy + Terms links in-app (footer веб-UI)
- [ ] No misleading biometric claims
- [ ] Crash-free on Pixel / Samsung mid-range
````

## `apps/android/README.md`

````markdown
# Cmir Android

WebView-оболочка для Google Play. Подробности публикации: [PLAY_STORE.md](PLAY_STORE.md).

```bash
# Android Studio → Open apps/android
./gradlew assembleDebug
```
````

## `apps/android/app/build.gradle.kts`

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.cmir.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.cmir.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity-ktx:1.9.3")
    implementation("androidx.webkit:webkit:1.12.1")
    implementation("com.google.android.material:material:1.12.0")
}
```

## `apps/android/app/src/main/AndroidManifest.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-feature android:name="android.hardware.camera" android:required="false" />

    <application
        android:allowBackup="false"
        android:icon="@android:drawable/ic_menu_camera"
        android:label="@string/app_name"
        android:networkSecurityConfig="@xml/network_security_config"
        android:supportsRtl="true"
        android:theme="@style/Theme.Cmir"
        android:usesCleartextTraffic="true">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:hardwareAccelerated="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="https" android:host="app.cmir.live" />
                <data android:scheme="cmir" android:host="open" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

## `apps/android/app/src/main/java/com/cmir/app/MainActivity.kt`

```kotlin
/**
 * Cmir Android — WebView shell for map / kiosk / account.
 * Package: com.cmir.app
 *
 * Build (Android Studio / CLI):
 *   cd apps/android && ./gradlew assembleRelease
 *
 * Play Console: see PLAY_STORE.md
 */
package com.cmir.app

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.Bundle
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private var pendingPermissionRequest: PermissionRequest? = null

    private val requestCamera = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        pendingPermissionRequest?.let { req ->
            if (granted) req.grant(req.resources) else req.deny()
            pendingPermissionRequest = null
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        webView = WebView(this)
        setContentView(webView)

        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.mediaPlaybackRequiresUserGesture = false
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
        settings.userAgentString = settings.userAgentString + " CmirAndroid/1.0"

        webView.webViewClient = WebViewClient()
        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest?) {
                if (request == null) return
                val needCamera = request.resources.any {
                    it == PermissionRequest.RESOURCE_VIDEO_CAPTURE
                }
                if (!needCamera) {
                    request.grant(request.resources)
                    return
                }
                if (ContextCompat.checkSelfPermission(
                        this@MainActivity,
                        Manifest.permission.CAMERA
                    ) == PackageManager.PERMISSION_GRANTED
                ) {
                    request.grant(request.resources)
                } else {
                    pendingPermissionRequest = request
                    requestCamera.launch(Manifest.permission.CAMERA)
                }
            }
        }

        val base = intent?.data?.toString()
            ?: getString(R.string.cmir_web_base)
        webView.loadUrl(base)
    }

    override fun onBackPressed() {
        if (this::webView.isInitialized && webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
```

## `apps/android/app/src/main/res/values/strings.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Cmir</string>
    <!-- Production host after deploy. Emulator lab: http://10.0.2.2:3000/ -->
    <string name="cmir_web_base">https://app.cmir.live/</string>
</resources>
```

## `apps/android/app/src/main/res/values/themes.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.Cmir" parent="Theme.AppCompat.DayNight.NoActionBar" />
</resources>
```

## `apps/android/app/src/main/res/xml/network_security_config.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- Prod: HTTPS only. Debug/lab: allow cleartext to LAN / localhost via adb reverse. -->
    <base-config cleartextTrafficPermitted="false" />
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">127.0.0.1</domain>
    </domain-config>
</network-security-config>
```

## `apps/android/build.gradle.kts`

```kotlin
plugins {
    id("com.android.application") version "8.7.2" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
}
```

## `apps/android/gradle.properties`

```properties
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTranslatableRClass=true
```

## `apps/android/settings.gradle.kts`

```kotlin
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "Cmir"
include(":app")
```

## `apps/api/Cargo.toml`

```toml
[package]
name = "cmir-api"
version.workspace = true
edition.workspace = true

[dependencies]
axum = { version = "0.7", features = ["macros"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1", features = ["v4", "serde"] }
thiserror = "1"
tower-http = { version = "0.5", features = ["cors", "trace"] }
tracing = "0.1"
tracing-subscriber = "0.3"

[dev-dependencies]
tokio-test = "0.4"
```

## `apps/api/src/domain.rs`

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Тип точки интереса — определяет минимум камер.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PoiType {
    LiveCam,
    SocialEvent,
    Venue,
}

impl PoiType {
    pub fn min_cameras(self) -> u32 {
        match self {
            PoiType::LiveCam => 1,
            PoiType::SocialEvent => 2,
            PoiType::Venue => 3,
        }
    }

    pub fn min_consent_cameras(self) -> u32 {
        match self {
            PoiType::LiveCam => 0,
            PoiType::SocialEvent => 1,
            PoiType::Venue => 2,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CameraRole {
    General,
    Consent,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ViewMode {
    Fisheye,
    Standard,
    Zoom2x,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Poi {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub poi_type: PoiType,
    pub latitude: f64,
    pub longitude: f64,
    pub promo_description: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CreatePoiRequest {
    pub name: String,
    pub description: Option<String>,
    pub poi_type: PoiType,
    pub latitude: f64,
    pub longitude: f64,
    pub promo_description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Camera {
    pub id: Uuid,
    pub poi_id: Uuid,
    pub name: String,
    pub stream_url: String,
    pub role: CameraRole,
    pub view_mode: ViewMode,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CreateCameraRequest {
    pub name: String,
    pub stream_url: String,
    pub role: CameraRole,
    pub view_mode: ViewMode,
}

#[derive(Debug, Clone, Serialize)]
pub struct PoiStats {
    pub poi_id: Uuid,
    pub consent_rate_percent: f64,
    pub participant_count_24h: u64,
    pub avatar_faces_ratio: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct PoiWithCameras {
    #[serde(flatten)]
    pub poi: Poi,
    pub cameras: Vec<Camera>,
    pub stats: PoiStats,
}

/// Consent (Phase 0 — mock wallet)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsentRecord {
    pub id: Uuid,
    pub poi_id: Uuid,
    pub wallet_address: String,
    pub consented_at: DateTime<Utc>,
    pub consent_text_version: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct GrantConsentRequest {
    /// Base64 embedding placeholder for POC
    pub face_embedding: Option<String>,
}
```

## `apps/api/src/error.rs`

```rust
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use serde_json::json;

#[derive(Debug, thiserror::Error)]
pub enum ApiError {
    #[error("not found: {0}")]
    NotFound(String),
    #[error("validation: {0}")]
    Validation(String),
    #[error("conflict: {0}")]
    Conflict(String),
}

impl ApiError {
    fn status(&self) -> StatusCode {
        match self {
            ApiError::NotFound(_) => StatusCode::NOT_FOUND,
            ApiError::Validation(_) => StatusCode::BAD_REQUEST,
            ApiError::Conflict(_) => StatusCode::CONFLICT,
        }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let body = json!({
            "success": false,
            "error": self.to_string(),
        });
        (self.status(), Json(body)).into_response()
    }
}

pub type ApiResult<T> = Result<T, ApiError>;
```

## `apps/api/src/main.rs`

```rust
//! Cmir API — POI & camera registry (Phase 0)

mod domain;
mod error;
mod routes;
mod store;

use std::net::SocketAddr;
use std::sync::Arc;

use axum::Router;
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing::info;

use crate::store::AppStore;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "cmir_api=info,tower_http=info".into()),
        )
        .init();

    let store = Arc::new(RwLock::new(AppStore::new_with_demo()));
    let app = Router::new()
        .merge(routes::router())
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(store);

    let addr = SocketAddr::from(([0, 0, 0, 0], 8090));
    info!("Cmir API listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.expect("bind");
    axum::serve(listener, app).await.expect("serve");
}
```

## `apps/api/src/routes.rs`

```rust
use std::sync::Arc;

use axum::extract::{Path, State};
use axum::routing::{get, post};
use axum::{Json, Router};
use serde_json::json;
use tokio::sync::RwLock;
use uuid::Uuid;

use crate::domain::{CreateCameraRequest, CreatePoiRequest, GrantConsentRequest};
use crate::error::ApiResult;
use crate::store::AppStore;

pub type SharedStore = Arc<RwLock<AppStore>>;

pub fn router() -> Router<SharedStore> {
    Router::new()
        .route("/health", get(health))
        .route("/api/v1/pois", get(list_pois).post(create_poi))
        .route("/api/v1/pois/:id", get(get_poi))
        .route("/api/v1/pois/:id/cameras", post(add_camera))
        .route("/api/v1/pois/:id/consent", post(grant_consent))
        .route("/api/v1/tops/consent", get(top_consent))
        .route("/api/v1/tops/participants", get(top_participants))
}

async fn health() -> Json<serde_json::Value> {
    Json(json!({
        "status": "healthy",
        "service": "cmir-api",
        "version": "0.1.0",
        "phase": "0"
    }))
}

async fn list_pois(State(store): State<SharedStore>) -> Json<serde_json::Value> {
    let store = store.read().await;
    Json(json!({ "success": true, "data": store.list_pois() }))
}

async fn create_poi(
    State(store): State<SharedStore>,
    Json(req): Json<CreatePoiRequest>,
) -> ApiResult<Json<serde_json::Value>> {
    let mut store = store.write().await;
    let poi = store.create_poi(req)?;
    Ok(Json(json!({ "success": true, "data": poi })))
}

async fn get_poi(
    State(store): State<SharedStore>,
    Path(id): Path<Uuid>,
) -> ApiResult<Json<serde_json::Value>> {
    let store = store.read().await;
    let poi = store.get_poi(id)?;
    Ok(Json(json!({ "success": true, "data": poi })))
}

async fn add_camera(
    State(store): State<SharedStore>,
    Path(poi_id): Path<Uuid>,
    Json(req): Json<CreateCameraRequest>,
) -> ApiResult<Json<serde_json::Value>> {
    let mut store = store.write().await;
    let camera = store.add_camera(poi_id, req)?;
    Ok(Json(json!({ "success": true, "data": camera })))
}

async fn grant_consent(
    State(store): State<SharedStore>,
    Path(poi_id): Path<Uuid>,
    Json(req): Json<GrantConsentRequest>,
) -> ApiResult<Json<serde_json::Value>> {
    let mut store = store.write().await;
    let record = store.grant_consent(poi_id, req.face_embedding)?;
    Ok(Json(json!({
        "success": true,
        "data": record,
        "message": "Consent recorded; wallet created (POC mock)"
    })))
}

async fn top_consent(State(store): State<SharedStore>) -> Json<serde_json::Value> {
    let store = store.read().await;
    Json(json!({ "success": true, "data": store.top_by_consent() }))
}

async fn top_participants(State(store): State<SharedStore>) -> Json<serde_json::Value> {
    let store = store.read().await;
    Json(json!({ "success": true, "data": store.top_by_participants() }))
}
```

## `apps/api/src/store.rs`

```rust
use std::collections::HashMap;

use chrono::Utc;
use uuid::Uuid;

use crate::domain::{
    Camera, CameraRole, ConsentRecord, CreateCameraRequest, CreatePoiRequest, Poi, PoiStats,
    PoiType, PoiWithCameras,
};
use crate::error::{ApiError, ApiResult};

pub struct AppStore {
    pois: HashMap<Uuid, Poi>,
    cameras: HashMap<Uuid, Camera>,
    consents: Vec<ConsentRecord>,
    /// POC: consent rate per POI (0.0 - 100.0)
    consent_rates: HashMap<Uuid, f64>,
    participants: HashMap<Uuid, u64>,
}

impl AppStore {
    pub fn new_with_demo() -> Self {
        let mut store = Self {
            pois: HashMap::new(),
            cameras: HashMap::new(),
            consents: Vec::new(),
            consent_rates: HashMap::new(),
            participants: HashMap::new(),
        };
        store.seed_demo();
        store
    }

    fn seed_demo(&mut self) {
        let poi_id = Uuid::new_v4();
        let now = Utc::now();
        let poi = Poi {
            id: poi_id,
            name: "Demo: Social Event — Пингвинья вечеринка".into(),
            description: "Тестовая точка для Фазы 0".into(),
            poi_type: PoiType::SocialEvent,
            latitude: 41.7151,
            longitude: 44.8271,
            promo_description: "Лучшее место в городе для live-трансляций.".into(),
            created_at: now,
            updated_at: now,
        };
        self.pois.insert(poi_id, poi);

        let c1 = Camera {
            id: Uuid::new_v4(),
            poi_id,
            name: "General A".into(),
            stream_url: "rtsp://localhost/demo/general_a".into(),
            role: CameraRole::General,
            view_mode: crate::domain::ViewMode::Standard,
            is_active: true,
            created_at: now,
        };
        let c2 = Camera {
            id: Uuid::new_v4(),
            poi_id,
            name: "General B".into(),
            stream_url: "rtsp://localhost/demo/general_b".into(),
            role: CameraRole::General,
            view_mode: crate::domain::ViewMode::Fisheye,
            is_active: true,
            created_at: now,
        };
        let c3 = Camera {
            id: Uuid::new_v4(),
            poi_id,
            name: "Consent kiosk".into(),
            stream_url: "rtsp://localhost/demo/consent".into(),
            role: CameraRole::Consent,
            view_mode: crate::domain::ViewMode::Standard,
            is_active: true,
            created_at: now,
        };
        self.cameras.insert(c1.id, c1);
        self.cameras.insert(c2.id, c2);
        self.cameras.insert(c3.id, c3);

        self.consent_rates.insert(poi_id, 42.0);
        self.participants.insert(poi_id, 17);
    }

    pub fn list_pois(&self) -> Vec<PoiWithCameras> {
        self.pois
            .values()
            .map(|p| self.poi_with_cameras(p.id))
            .collect()
    }

    pub fn poi_with_cameras(&self, poi_id: Uuid) -> PoiWithCameras {
        let poi = self.pois.get(&poi_id).cloned().expect("poi exists");
        let cameras: Vec<Camera> = self
            .cameras
            .values()
            .filter(|c| c.poi_id == poi_id)
            .cloned()
            .collect();
        let stats = PoiStats {
            poi_id,
            consent_rate_percent: *self.consent_rates.get(&poi_id).unwrap_or(&0.0),
            participant_count_24h: *self.participants.get(&poi_id).unwrap_or(&0),
            avatar_faces_ratio: 1.0
                - self.consent_rates.get(&poi_id).copied().unwrap_or(0.0) / 100.0,
        };
        PoiWithCameras {
            poi,
            cameras,
            stats,
        }
    }

    pub fn create_poi(&mut self, req: CreatePoiRequest) -> ApiResult<Poi> {
        if req.name.trim().is_empty() {
            return Err(ApiError::Validation("name is required".into()));
        }
        let id = Uuid::new_v4();
        let now = Utc::now();
        let poi = Poi {
            id,
            name: req.name,
            description: req.description.unwrap_or_default(),
            poi_type: req.poi_type,
            latitude: req.latitude,
            longitude: req.longitude,
            promo_description: req.promo_description.unwrap_or_default(),
            created_at: now,
            updated_at: now,
        };
        self.pois.insert(id, poi.clone());
        self.consent_rates.insert(id, 0.0);
        self.participants.insert(id, 0);
        Ok(poi)
    }

    pub fn get_poi(&self, id: Uuid) -> ApiResult<PoiWithCameras> {
        if !self.pois.contains_key(&id) {
            return Err(ApiError::NotFound(format!("poi {}", id)));
        }
        Ok(self.poi_with_cameras(id))
    }

    pub fn add_camera(&mut self, poi_id: Uuid, req: CreateCameraRequest) -> ApiResult<Camera> {
        let poi = self
            .pois
            .get(&poi_id)
            .ok_or_else(|| ApiError::NotFound(format!("poi {}", poi_id)))?;

        if req.stream_url.trim().is_empty() {
            return Err(ApiError::Validation("stream_url is required".into()));
        }

        let camera = Camera {
            id: Uuid::new_v4(),
            poi_id,
            name: req.name,
            stream_url: req.stream_url,
            role: req.role,
            view_mode: req.view_mode,
            is_active: true,
            created_at: Utc::now(),
        };
        self.cameras.insert(camera.id, camera.clone());

        self.validate_poi_cameras(poi.poi_type, poi_id)?;

        Ok(camera)
    }

    pub fn validate_poi_cameras(&self, poi_type: PoiType, poi_id: Uuid) -> ApiResult<()> {
        let cams: Vec<&Camera> = self.cameras.values().filter(|c| c.poi_id == poi_id).collect();
        let total = cams.len() as u32;
        let consent = cams
            .iter()
            .filter(|c| c.role == CameraRole::Consent)
            .count() as u32;

        if total < poi_type.min_cameras() {
            return Err(ApiError::Validation(format!(
                "poi type {:?} requires at least {} cameras, has {}",
                poi_type, poi_type.min_cameras(), total
            )));
        }
        if consent < poi_type.min_consent_cameras() {
            return Err(ApiError::Validation(format!(
                "poi type {:?} requires at least {} consent cameras, has {}",
                poi_type, poi_type.min_consent_cameras(), consent
            )));
        }
        Ok(())
    }

    pub fn grant_consent(
        &mut self,
        poi_id: Uuid,
        _embedding: Option<String>,
    ) -> ApiResult<ConsentRecord> {
        if !self.pois.contains_key(&poi_id) {
            return Err(ApiError::NotFound(format!("poi {}", poi_id)));
        }

        let wallet = format!("0xcmir{}", Uuid::new_v4().simple());
        let record = ConsentRecord {
            id: Uuid::new_v4(),
            poi_id,
            wallet_address: wallet,
            consented_at: Utc::now(),
            consent_text_version: "0.1.0-draft".into(),
        };
        self.consents.push(record.clone());

        let rate = self.consent_rates.entry(poi_id).or_insert(0.0);
        *rate = (*rate + 5.0).min(100.0);
        *self.participants.entry(poi_id).or_insert(0) += 1;

        Ok(record)
    }

    pub fn top_by_consent(&self) -> Vec<PoiWithCameras> {
        let mut list: Vec<_> = self.list_pois();
        list.sort_by(|a, b| {
            b.stats
                .consent_rate_percent
                .partial_cmp(&a.stats.consent_rate_percent)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        list
    }

    pub fn top_by_participants(&self) -> Vec<PoiWithCameras> {
        let mut list: Vec<_> = self.list_pois();
        list.sort_by(|a, b| {
            b.stats
                .participant_count_24h
                .cmp(&a.stats.participant_count_24h)
        });
        list
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::{CameraRole, CreateCameraRequest, CreatePoiRequest, PoiType, ViewMode};

    #[test]
    fn social_event_requires_two_cameras_and_one_consent() {
        let mut store = AppStore {
            pois: HashMap::new(),
            cameras: HashMap::new(),
            consents: Vec::new(),
            consent_rates: HashMap::new(),
            participants: HashMap::new(),
        };
        let poi = store
            .create_poi(CreatePoiRequest {
                name: "Test".into(),
                description: None,
                poi_type: PoiType::SocialEvent,
                latitude: 0.0,
                longitude: 0.0,
                promo_description: None,
            })
            .unwrap();

        assert!(store
            .add_camera(
                poi.id,
                CreateCameraRequest {
                    name: "g1".into(),
                    stream_url: "rtsp://x".into(),
                    role: CameraRole::General,
                    view_mode: ViewMode::Standard,
                },
            )
            .is_err());

        store
            .add_camera(
                poi.id,
                CreateCameraRequest {
                    name: "g2".into(),
                    stream_url: "rtsp://y".into(),
                    role: CameraRole::General,
                    view_mode: ViewMode::Standard,
                },
            )
            .unwrap();

        assert!(store
            .add_camera(
                poi.id,
                CreateCameraRequest {
                    name: "extra".into(),
                    stream_url: "rtsp://w".into(),
                    role: CameraRole::General,
                    view_mode: ViewMode::Standard,
                },
            )
            .is_err());

        let consent_cam = store
            .add_camera(
                poi.id,
                CreateCameraRequest {
                    name: "c1".into(),
                    stream_url: "rtsp://z".into(),
                    role: CameraRole::Consent,
                    view_mode: ViewMode::Standard,
                },
            )
            .unwrap();
        assert_eq!(consent_cam.role, CameraRole::Consent);
    }

    #[test]
    fn grant_consent_increases_rate() {
        let mut store = AppStore::new_with_demo();
        let demo_id = store.list_pois()[0].poi.id;
        let before = store.get_poi(demo_id).unwrap().stats.consent_rate_percent;
        store.grant_consent(demo_id, None).unwrap();
        let after = store.get_poi(demo_id).unwrap().stats.consent_rate_percent;
        assert!(after > before);
    }
}
```

## `apps/api_py/auth.py`

```python
"""Password hashing and session tokens (stdlib only)."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return "pbkdf2$120000$" + salt.hex() + "$" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, digest_hex = stored.split("$", 3)
        if algo != "pbkdf2":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        got = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iters))
        return hmac.compare_digest(got, expected)
    except (ValueError, TypeError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expires(days: int = 14) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def is_blocked(blocked_until: Optional[str]) -> bool:
    if not blocked_until:
        return False
    try:
        until = datetime.fromisoformat(blocked_until.replace("Z", "+00:00"))
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        return until > datetime.now(timezone.utc)
    except ValueError:
        return False


def is_session_valid(expires_at: str) -> bool:
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp > datetime.now(timezone.utc)
    except ValueError:
        return False
```

## `apps/api_py/camera_health.py`

```python
"""Lightweight stream URL reachability probe (Phase 1 — no ffmpeg required)."""
from __future__ import annotations

import socket
import urllib.error
import urllib.request
from typing import Any, Dict
from urllib.parse import urlparse


def probe_stream_url(url: str, timeout: float = 2.5) -> Dict[str, Any]:
    if not url or not url.strip():
        return {"status": "invalid", "detail": "empty stream_url", "quality_score": 0}

    if url.startswith("local://"):
        return {"status": "local", "detail": "USB camera (local)", "quality_score": 95}

    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()

    if scheme in ("rtsp", "rtsps"):
        host = parsed.hostname
        if not host:
            return {"status": "invalid", "detail": "missing host"}
        port = parsed.port or (322 if scheme == "rtsps" else 554)
        return _with_score(_tcp_probe(host, port, timeout, label=f"{scheme}://{host}:{port}"))

    if scheme in ("http", "https"):
        return _with_score(_http_probe(url, timeout))

    if scheme == "rtmp":
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 1935
        return _with_score(_tcp_probe(host, port, timeout, label=f"rtmp://{host}:{port}"))

    if scheme in ("file", ""):
        return {"status": "skipped", "detail": f"scheme {scheme or '(none)'} not probed in POC", "quality_score": 50}

    return {"status": "unknown", "detail": f"unsupported scheme: {scheme}", "quality_score": 0}


def _with_score(result: Dict[str, Any]) -> Dict[str, Any]:
    status = result.get("status", "unknown")
    scores = {
        "reachable": 92,
        "local": 95,
        "skipped": 50,
        "invalid": 0,
        "unreachable": 0,
        "unknown": 20,
    }
    result["quality_score"] = scores.get(status, 30)
    return result


def _tcp_probe(host: str, port: int, timeout: float, label: str) -> Dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"status": "reachable", "detail": f"TCP ok ({label})"}
    except OSError as e:
        return {"status": "unreachable", "detail": f"{label}: {e}"}


def _http_probe(url: str, timeout: float) -> Dict[str, Any]:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {
                "status": "reachable",
                "detail": f"HTTP {resp.status}",
            }
    except urllib.error.HTTPError as e:
        if e.code < 500:
            return {"status": "reachable", "detail": f"HTTP {e.code}"}
        return {"status": "unreachable", "detail": str(e)}
    except Exception as e:
        return {"status": "unreachable", "detail": str(e)}
```

## `apps/api_py/compliance.py`

```python
"""Соответствие требованиям Грузии по персональным и биометрическим данным (PDPL)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from database import app_env, db_path

LEGAL_VERSION = "1.0.0-ge"
DOC_TYPES = (
    "terms_of_service",
    "privacy_policy",
    "personal_data_consent",
    "biometric_data_consent",
    "wallet_agreement",
)

DOC_TITLES = {
    "terms_of_service": "Пользовательское соглашение (Terms of Service)",
    "privacy_policy": "Политика конфиденциальности (Privacy Policy)",
    "personal_data_consent": "Согласие на обработку персональных данных",
    "biometric_data_consent": "Согласие на обработку биометрических данных",
    "wallet_agreement": "Договор об открытии электронного кошелька",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def legal_dir() -> Path:
    d = db_path().parent / "legal"
    d.mkdir(parents=True, exist_ok=True)
    return d


def require_data_key_in_prod() -> None:
    if app_env() == "prod" and not os.environ.get("CMIR_DATA_KEY", "").strip():
        raise RuntimeError("CMIR_DATA_KEY is required in production")


def _fernet():
    import base64

    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None
    key = os.environ.get("CMIR_DATA_KEY", "").strip()
    if not key:
        if app_env() == "prod":
            return None
        # lab/test only: stable key derived from DB path (not for production)
        seed = hashlib.sha256(str(db_path()).encode()).digest()
        key = base64.urlsafe_b64encode(seed).decode()
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        digest = hashlib.sha256(key.encode()).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_embedding(vec: list[float]) -> str:
    f = _fernet()
    if f is None:
        if app_env() == "prod":
            raise RuntimeError("cryptography/Fernet unavailable; cannot store biometrics")
        return json.dumps(vec)
    return f.encrypt(json.dumps(vec).encode()).decode()


def decrypt_embedding(blob: str) -> Optional[list[float]]:
    if not blob:
        return None
    # legacy plaintext JSON
    try:
        data = json.loads(blob)
        if isinstance(data, list):
            return [float(x) for x in data]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    f = _fernet()
    if f is None:
        return None
    try:
        return json.loads(f.decrypt(blob.encode()).decode())
    except Exception:
        return None


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("995") and len(digits) >= 12:
        return "+" + digits
    if len(digits) == 9:
        return "+995" + digits
    if digits:
        return "+" + digits
    raise ValueError("invalid phone")


def phone_to_email(phone: str) -> str:
    digits = re.sub(r"\D", "", normalize_phone(phone))
    return f"+{digits}@kiosk.cmir.ge"


def default_legal_text(doc_type: str) -> str:
    base = DOC_TITLES.get(doc_type, doc_type)
    return (
        f"{base}\n"
        f"Версия документа: {LEGAL_VERSION}\n"
        f"Дата вступления в силу: 2026-05-23\n\n"
        "Настоящий документ регулирует обработку персональных и биометрических данных "
        "в соответствии с Законом Грузии «О защите персональных данных» (PDPL), "
        "включая принципы законности, прозрачности, минимизации данных, ограничения цели "
        "и срока хранения. Оператор: Cmir Platform. Территория обработки: Грузия.\n\n"
        "Продолжая регистрацию, вы подтверждаете, что ознакомились с условиями документа "
        f"«{base}» и даёте информированное согласие в объёме, указанном в документе."
    )


def ensure_legal_documents(conn) -> None:
    for doc_type in DOC_TYPES:
        row = conn.execute(
            "SELECT id FROM legal_documents WHERE doc_type = ? AND version = ?",
            (doc_type, LEGAL_VERSION),
        ).fetchone()
        if row:
            continue
        text = default_legal_text(doc_type)
        fname = f"{doc_type}_{LEGAL_VERSION}.txt"
        path = legal_dir() / fname
        path.write_text(text, encoding="utf-8")
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        conn.execute(
            """
            INSERT INTO legal_documents (id, doc_type, version, title, content_hash, file_path, effective_from, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                doc_type,
                LEGAL_VERSION,
                DOC_TITLES[doc_type],
                content_hash,
                fname,
                "2026-05-23",
                now_iso(),
            ),
        )
    conn.commit()


def list_legal_documents(conn) -> list[dict[str, Any]]:
    ensure_legal_documents(conn)
    rows = conn.execute(
        "SELECT doc_type, version, title, content_hash, effective_from FROM legal_documents ORDER BY doc_type"
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        path = legal_dir() / conn.execute(
            "SELECT file_path FROM legal_documents WHERE doc_type = ? AND version = ?",
            (r["doc_type"], r["version"]),
        ).fetchone()["file_path"]
        d["content"] = path.read_text(encoding="utf-8") if path.is_file() else ""
        out.append(d)
    return out


def validate_acceptances(acceptances: dict) -> None:
    missing = [k for k in DOC_TYPES if not acceptances.get(k)]
    if missing:
        raise ValueError("all legal documents must be accepted: " + ", ".join(missing))


def audit_log(conn, action: str, user_id: str = "", poi_id: str = "", details: Optional[dict] = None) -> None:
    conn.execute(
        """
        INSERT INTO audit_log (id, action, user_id, poi_id, details_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), action, user_id or None, poi_id or None, json.dumps(details or {}), now_iso()),
    )


def blockchain_record(conn, user_id: str, payload: dict) -> dict:
    """Запись о регистрации пользователя (заглушка распределённого реестра)."""
    tx_hash = "0x" + hashlib.sha256(
        json.dumps({"user_id": user_id, **payload, "nonce": secrets.token_hex(8)}, sort_keys=True).encode()
    ).hexdigest()
    rid = str(uuid.uuid4())
    t = now_iso()
    conn.execute(
        """
        INSERT INTO blockchain_records (id, user_id, tx_hash, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (rid, user_id, tx_hash, json.dumps(payload), t),
    )
    return {"record_id": rid, "tx_hash": tx_hash, "created_at": t, "network": "cmir-ledger-stub"}
```

## `apps/api_py/database.py`

```python
"""SQLite persistence for Cmir core (users, sessions, consents, wallets, POI)."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

DEFAULT_DB = Path(__file__).resolve().parent / "data" / "cmir_test.db"


def app_env() -> str:
    return os.environ.get("CMIR_ENV", "test").lower()


def db_path() -> Path:
    explicit = os.environ.get("CMIR_DB_PATH", "")
    if explicit:
        return Path(explicit)
    base = Path(__file__).resolve().parent / "data"
    if app_env() == "prod":
        return base / "cmir_prod.db"
    return base / "cmir_test.db"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wallets (
    address TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    balance_st REAL NOT NULL DEFAULT 0,
    balance_ut REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pois (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    poi_type TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    promo_description TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    country TEXT NOT NULL DEFAULT '',
    consent_rate REAL NOT NULL DEFAULT 0,
    participants_24h INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cameras (
    id TEXT PRIMARY KEY,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    stream_url TEXT NOT NULL,
    role TEXT NOT NULL,
    view_mode TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    wallet_address TEXT NOT NULL REFERENCES wallets(address),
    face_embedding TEXT,
    consent_text_version TEXT NOT NULL,
    consented_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS poi_embeddings (
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    consent_id TEXT NOT NULL REFERENCES consents(id) ON DELETE CASCADE,
    embedding_json TEXT NOT NULL,
    PRIMARY KEY (poi_id, consent_id)
);

CREATE TABLE IF NOT EXISTS face_templates (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_id TEXT NOT NULL REFERENCES consents(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    pose TEXT NOT NULL DEFAULT 'center',
    yaw REAL,
    pitch REAL,
    embedding_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_face_templates_user ON face_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_face_templates_consent ON face_templates(consent_id);

CREATE TABLE IF NOT EXISTS donations (
    id TEXT PRIMARY KEY,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'GEL',
    message TEXT NOT NULL DEFAULT '',
    donor TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending_moderation',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS airtime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    wallet_address TEXT NOT NULL,
    seconds REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_consents_user ON consents(user_id);
CREATE INDEX IF NOT EXISTS idx_consents_poi ON consents(poi_id);
CREATE INDEX IF NOT EXISTS idx_cameras_poi ON cameras(poi_id);

CREATE TABLE IF NOT EXISTS view_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL,
    poi_id TEXT NOT NULL,
    seconds REAL NOT NULL,
    ad_revenue REAL NOT NULL,
    period_key TEXT NOT NULL,
    ut_earned REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_view_events_period ON view_events(period_key);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    favorite_menu_item TEXT NOT NULL DEFAULT '',
    registered_via TEXT NOT NULL DEFAULT 'web',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS legal_documents (
    id TEXT PRIMARY KEY,
    doc_type TEXT NOT NULL,
    version TEXT NOT NULL,
    title TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    file_path TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(doc_type, version)
);

CREATE TABLE IF NOT EXISTS consent_document_acceptances (
    id TEXT PRIMARY KEY,
    consent_id TEXT NOT NULL REFERENCES consents(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    doc_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    accepted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    user_id TEXT,
    poi_id TEXT,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blockchain_records (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tx_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_blockchain_user ON blockchain_records(user_id);

CREATE TABLE IF NOT EXISTS performance_streams (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'idle',
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signature_bindings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    consent_id TEXT REFERENCES consents(id) ON DELETE SET NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_perf_streams_user ON performance_streams(user_id);
CREATE INDEX IF NOT EXISTS idx_signature_user ON signature_bindings(user_id);

CREATE TABLE IF NOT EXISTS stream_recordings (
    id TEXT PRIMARY KEY,
    stream_id TEXT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    camera_role TEXT NOT NULL DEFAULT 'performance',
    title TEXT NOT NULL DEFAULT '',
    raw_path TEXT,
    clip_path TEXT,
    status TEXT NOT NULL DEFAULT 'recording',
    duration_sec REAL,
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS platform_links (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    username TEXT NOT NULL DEFAULT '',
    external_user_id TEXT,
    oauth_token TEXT,
    refresh_token TEXT,
    scopes TEXT,
    linked_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, platform)
);

CREATE TABLE IF NOT EXISTS platform_comments (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    external_comment_id TEXT NOT NULL,
    stream_recording_id TEXT,
    performance_stream_id TEXT,
    author_username TEXT,
    author_external_id TEXT,
    text TEXT NOT NULL,
    direction TEXT NOT NULL DEFAULT 'inbound',
    synced_at TEXT NOT NULL,
    UNIQUE(platform, external_comment_id)
);

CREATE TABLE IF NOT EXISTS platform_stream_targets (
    id TEXT PRIMARY KEY,
    stream_recording_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    external_broadcast_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recordings_user ON stream_recordings(user_id);
CREATE INDEX IF NOT EXISTS idx_platform_links_user ON platform_links(user_id);

CREATE TABLE IF NOT EXISTS face_presence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL,
    poi_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    seconds REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, camera_id, period_key)
);

CREATE INDEX IF NOT EXISTS idx_face_presence_cam_period ON face_presence(camera_id, period_key);
CREATE INDEX IF NOT EXISTS idx_face_presence_user ON face_presence(user_id);

CREATE TABLE IF NOT EXISTS face_presence_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL,
    poi_id TEXT NOT NULL,
    seconds REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_presence_events_camera_time
    ON face_presence_events(camera_id, recorded_at);

CREATE TABLE IF NOT EXISTS ad_payouts (
    id TEXT PRIMARY KEY,
    camera_id TEXT NOT NULL,
    poi_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    ad_amount REAL NOT NULL,
    user_pool REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ad_payout_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payout_id TEXT NOT NULL REFERENCES ad_payouts(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seconds REAL NOT NULL,
    share REAL NOT NULL,
    ut_earned REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS stream_presence_rewards (
    id TEXT PRIMARY KEY,
    stream_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL,
    presence_seconds REAL NOT NULL,
    ut_earned REAL NOT NULL DEFAULT 1,
    rewarded_at TEXT NOT NULL,
    UNIQUE(stream_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_stream_rewards_stream ON stream_presence_rewards(stream_id);
CREATE INDEX IF NOT EXISTS idx_stream_rewards_user ON stream_presence_rewards(user_id);
"""


MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'",
    "ALTER TABLE users ADD COLUMN blocked_until TEXT",
    "ALTER TABLE pois ADD COLUMN address TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE pois ADD COLUMN comment TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE pois ADD COLUMN mask_image TEXT",
    "ALTER TABLE cameras ADD COLUMN device_id TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE cameras ADD COLUMN slot_index INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE cameras ADD COLUMN is_preview INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE cameras ADD COLUMN source_type TEXT NOT NULL DEFAULT 'rtsp'",
    "ALTER TABLE cameras ADD COLUMN device_label TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE pois ADD COLUMN menu_items_json TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE performance_streams ADD COLUMN recording_id TEXT",
    "ALTER TABLE performance_streams ADD COLUMN clip_path TEXT",
    "ALTER TABLE performance_streams ADD COLUMN clip_status TEXT",
]


def migrate(conn: sqlite3.Connection) -> None:
    user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    poi_cols = {r[1] for r in conn.execute("PRAGMA table_info(pois)")}
    cam_cols = {r[1] for r in conn.execute("PRAGMA table_info(cameras)")}
    for sql in MIGRATIONS:
        col = sql.split("ADD COLUMN ")[1].split()[0]
        if col in ("role", "blocked_until") and col in user_cols:
            continue
        if col in ("address", "comment", "mask_image") and col in poi_cols:
            continue
        if col in ("device_id", "slot_index", "is_preview", "source_type", "device_label") and col in cam_cols:
            continue
        if col == "menu_items_json" and col in poi_cols:
            continue
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    migrate(conn)
    return conn


def masks_dir() -> Path:
    d = db_path().parent / "masks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return dict(row)
```

## `apps/api_py/face_profiles.py`

```python
"""Multi-pose face enrollment helpers (shared validation + normalize)."""
from __future__ import annotations

from typing import Any, List, Optional

PATCH_DIM = 32 * 32
REQUIRED_POSES = ("center", "left", "right", "up", "down")
MIN_TEMPLATES = 5


def _valid_vec(vec: Any) -> Optional[List[float]]:
    if not isinstance(vec, list) or len(vec) != PATCH_DIM:
        return None
    try:
        out = [float(x) for x in vec]
    except (TypeError, ValueError):
        return None
    return out


def normalize_face_templates(
    face_embedding: Any = None,
    face_embeddings: Any = None,
    *,
    require_multi: bool = False,
) -> List[dict]:
    """
    Приводит вход киоска к списку шаблонов:
    [{pose, embedding, yaw, pitch}, ...]
    """
    templates: List[dict] = []

    if isinstance(face_embeddings, list) and face_embeddings:
        for i, item in enumerate(face_embeddings):
            if isinstance(item, dict):
                vec = _valid_vec(item.get("embedding") or item.get("face_embedding"))
                pose = str(item.get("pose") or REQUIRED_POSES[min(i, len(REQUIRED_POSES) - 1)])
                yaw = item.get("yaw")
                pitch = item.get("pitch")
            else:
                vec = _valid_vec(item)
                pose = REQUIRED_POSES[min(i, len(REQUIRED_POSES) - 1)]
                yaw = pitch = None
            if not vec:
                continue
            templates.append(
                {
                    "pose": pose.lower().strip() or "center",
                    "embedding": vec,
                    "yaw": float(yaw) if yaw is not None else None,
                    "pitch": float(pitch) if pitch is not None else None,
                }
            )

    if not templates:
        vec = _valid_vec(face_embedding)
        if vec:
            templates.append({"pose": "center", "embedding": vec, "yaw": 0.0, "pitch": 0.0})

    if require_multi:
        poses = {t["pose"] for t in templates}
        missing = [p for p in REQUIRED_POSES if p not in poses]
        if len(templates) < MIN_TEMPLATES:
            raise ValueError(
                f"need at least {MIN_TEMPLATES} face poses (center/left/right/up/down), got {len(templates)}"
            )
        if missing:
            raise ValueError(f"missing face poses: {', '.join(missing)}")

    if not templates:
        raise ValueError(f"face_embedding must be {PATCH_DIM} floats or face_embeddings multi-pose list")

    return templates
```

## `apps/api_py/local_relay.py`

```python
"""USB-камера → RTMP MediaMTX → HLS для пользовательского контура."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Set

from preview_buffer import PreviewBuffer
from stream_paths import hls_playlist_ready, poi_hls_url, poi_rtmp_url, poi_stream_name

ROOT = Path(__file__).resolve().parents[2]
FACE_WORKER = ROOT / "apps" / "face-worker"
FFMPEG = os.environ.get("FFMPEG", shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg")
RELEASE_GRACE_SEC = 0.4


class LocalRelay:
    def __init__(self, store) -> None:
        self.store = store
        self._lock = threading.Lock()
        self._publishers: Dict[str, subprocess.Popen] = {}
        self._workers: Dict[str, subprocess.Popen] = {}
        self._consumers: Dict[str, Set[str]] = {}
        self._release_timers: Dict[str, threading.Timer] = {}
        self._preview = PreviewBuffer()
        self._device_cache: list[tuple[int, str]] = []
        self._device_cache_at = 0.0
        self._device_holder: Dict[int, str] = {}  # avfoundation index → poi_id

    @property
    def preview(self) -> PreviewBuffer:
        return self._preview

    def acquire(self, poi_id: str, client_id: str, wait_hls: bool = False) -> bool:
        if not client_id:
            client_id = "anonymous"
        with self._lock:
            timer = self._release_timers.pop(poi_id, None)
            if timer:
                timer.cancel()
            self._consumers.setdefault(poi_id, set()).add(client_id)
            row = self._row_for_poi(poi_id)
            if not row:
                return False
            # Never wait for HLS under the relay lock
            self._ensure_poi(row, wait_hls=False)
            self._preview.start_capture(poi_id)
        if wait_hls:
            return hls_playlist_ready(poi_hls_url(poi_id), timeout=3.0)
        return True

    def release(self, poi_id: str, client_id: str) -> None:
        if not client_id:
            client_id = "anonymous"
        with self._lock:
            clients = self._consumers.get(poi_id)
            if clients:
                clients.discard(client_id)
                if clients:
                    return
                self._consumers.pop(poi_id, None)
            # сразу гасим камеру — на iMac один device, нельзя оставлять ffmpeg
            self._stop_poi(poi_id)
            self._preview.stop_capture(poi_id)
            print(f"[relay] camera off poi {poi_id[:8]}… (release)")

    def force_stop(self, poi_id: str) -> None:
        """Полная остановка без ожидания клиентов (закрытие панели / смена страницы)."""
        with self._lock:
            timer = self._release_timers.pop(poi_id, None)
            if timer:
                timer.cancel()
            self._consumers.pop(poi_id, None)
            self._stop_poi(poi_id)
            self._preview.stop_capture(poi_id)

    def active_clients(self, poi_id: str) -> int:
        with self._lock:
            return len(self._consumers.get(poi_id, set()))

    def refresh(self) -> None:
        """Синхронизация конфигурации без автозапуска камер."""
        with self._lock:
            rows = self._local_camera_rows()
            configured = {r["poi_id"] for r in rows}
            for poi_id in list(self._publishers):
                if poi_id not in configured and not self._consumers.get(poi_id):
                    self._stop_poi(poi_id)

    def ensure_poi(self, poi_id: str, wait_hls: bool = True) -> bool:
        """Запуск только при наличии активных потребителей."""
        if self.active_clients(poi_id) == 0:
            return False
        row = self._row_for_poi(poi_id)
        if not row:
            return False
        with self._lock:
            self._ensure_poi(row, wait_hls=False)
        if wait_hls:
            return hls_playlist_ready(poi_hls_url(poi_id), timeout=2.5)
        return True

    def restart_poi(self, poi_id: str) -> None:
        with self._lock:
            self._stop_poi(poi_id)
        if self.active_clients(poi_id) > 0:
            self.ensure_poi(poi_id, wait_hls=False)

    def _schedule_stop(self, poi_id: str) -> None:
        old = self._release_timers.pop(poi_id, None)
        if old:
            old.cancel()

        def _stop() -> None:
            with self._lock:
                if self._consumers.get(poi_id):
                    return
                self._stop_poi(poi_id)
                self._preview.stop_capture(poi_id)
                print(f"[relay] camera off poi {poi_id[:8]}… (no viewers)")

        t = threading.Timer(RELEASE_GRACE_SEC, _stop)
        self._release_timers[poi_id] = t
        t.start()

    def _local_camera_rows(self):
        return self.store.conn.execute(
            """
            SELECT c.id AS camera_id, c.poi_id, c.device_id, c.device_label, c.stream_url, p.mask_image
            FROM cameras c
            JOIN pois p ON p.id = c.poi_id
            WHERE c.source_type = 'local_usb' AND c.is_active = 1 AND c.is_preview = 1
              AND (c.stream_url LIKE 'rtmp://%' OR c.stream_url LIKE 'local://%')
            """
        ).fetchall()

    def _row_for_poi(self, poi_id: str):
        return self.store.conn.execute(
            """
            SELECT c.id AS camera_id, c.poi_id, c.device_id, c.device_label, c.stream_url, p.mask_image
            FROM cameras c
            JOIN pois p ON p.id = c.poi_id
            WHERE c.poi_id = ? AND c.source_type = 'local_usb' AND c.is_active = 1 AND c.is_preview = 1
            LIMIT 1
            """,
            (poi_id,),
        ).fetchone()

    def _stop_poi(self, poi_id: str) -> None:
        for idx, holder in list(self._device_holder.items()):
            if holder == poi_id:
                self._device_holder.pop(idx, None)
        for bucket in (self._workers, self._publishers):
            proc = bucket.pop(poi_id, None)
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try:
                        proc.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        pass

    def _publisher_alive(self, poi_id: str) -> bool:
        pub = self._publishers.get(poi_id)
        return pub is not None and pub.poll() is None

    def _ensure_poi(self, row, wait_hls: bool = True) -> None:
        poi_id = row["poi_id"]
        if self._publisher_alive(poi_id):
            hls_url = poi_hls_url(poi_id)
            # Quick non-blocking readiness probe — never sleep under lock
            stale = wait_hls and not hls_playlist_ready(hls_url, timeout=0.25)
            if stale:
                print(f"[relay] stale publisher for poi {poi_id[:8]}… — restarting ffmpeg")
                self._stop_poi(poi_id)
            else:
                threading.Thread(
                    target=self._ensure_worker,
                    args=(poi_id, row["mask_image"], row["camera_id"] if "camera_id" in row.keys() else ""),
                    daemon=True,
                ).start()
                return

        if self._publishers.get(poi_id) and self._publishers[poi_id].poll() is not None:
            self._publishers.pop(poi_id, None)

        resolved = self._resolve_device_index(row["device_label"] or "", row["device_id"] or "")
        if resolved is None:
            print(f"[relay] USB not found for poi {poi_id[:8]}… label={row['device_label']!r}")
            return
        idx, source_name, stub = resolved
        # Одна физическая камера — не держим два ffmpeg на одном index
        holder = self._device_holder.get(idx)
        if holder and holder != poi_id:
            print(f"[relay] device {idx} held by {holder[:8]}… — stopping previous")
            self._stop_poi(holder)
            self._consumers.pop(holder, None)
            self._preview.stop_capture(holder)
        if stub:
            print(
                f"[relay] GoPro не найдена — заглушка webcam «{source_name}» "
                f"(index {idx}) poi {poi_id[:8]}…"
            )

        rtmp = poi_rtmp_url(poi_id)
        cmd = [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "avfoundation",
            "-pixel_format",
            "uyvy422",
            "-framerate",
            "30",
            "-video_size",
            "1280x720",
            "-i",
            f"{idx}:none",
            "-an",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-f",
            "flv",
            rtmp,
        ]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            self._publishers[poi_id] = proc
            self._device_holder[idx] = poi_id
            print(f"[relay] publish poi {poi_id[:8]}… -> {rtmp} (device {idx} «{source_name}»)")
        except OSError as e:
            print(f"[relay] ffmpeg failed: {e}")
            return

        if wait_hls:
            for _ in range(12):
                if hls_playlist_ready(poi_hls_url(poi_id), timeout=1.0):
                    break
                if proc.poll() is not None:
                    err = (proc.stderr.read() if proc.stderr else b"").decode(errors="replace")[:200]
                    print(f"[relay] ffmpeg exited: {err}")
                    self._publishers.pop(poi_id, None)
                    return
                time.sleep(0.3)

        threading.Thread(
            target=self._ensure_worker,
            args=(poi_id, row["mask_image"], row["camera_id"] if "camera_id" in row.keys() else ""),
            daemon=True,
        ).start()

    def _ensure_worker(self, poi_id: str, mask_image: Optional[str], camera_id: str = "") -> None:
        raw_url = poi_hls_url(poi_id)
        for _ in range(16):
            if hls_playlist_ready(raw_url, timeout=1.0):
                break
            time.sleep(0.3)
        else:
            print(f"[relay] raw HLS not ready for {poi_id[:8]}…, skip mask worker")
            return

        worker = self._workers.get(poi_id)
        if worker and worker.poll() is None:
            return

        py = FACE_WORKER / ".venv" / "bin" / "python"
        if not py.is_file():
            py = Path(sys.executable)
        stream = poi_stream_name(poi_id)
        rtsp_in = f"rtsp://127.0.0.1:8554/{stream}"
        rtmp_out = f"rtmp://127.0.0.1:1935/{stream}_avatar"
        cmd = [
            str(py),
            "-m",
            "cmir_face.worker",
            "--input",
            rtsp_in,
            "--output",
            rtmp_out,
            "--api-url",
            os.environ.get("CMIR_API_URL", "http://127.0.0.1:8090"),
            "--poi-id",
            poi_id,
            "--mask",
            "face-bar",
            "--track-smooth",
            "0.35",
            "--output-delay-ms",
            os.environ.get("CMIR_PRIVACY_DELAY_MS", "250"),
        ]
        if camera_id:
            cmd.extend(["--camera-id", camera_id])
        mask_path = self.store.get_mask_image_path(poi_id) if mask_image else None
        if mask_path and mask_path.is_file():
            cmd.extend(["--mask-image", str(mask_path)])
        env = os.environ.copy()
        env["PYTHONPATH"] = str(FACE_WORKER)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(FACE_WORKER),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            self._workers[poi_id] = proc
            print(f"[relay] mask worker poi {poi_id[:8]}… -> {stream}_avatar")
        except OSError as e:
            print(f"[relay] worker failed: {e}")

    def _resolve_device_index(self, label: str, device_id: str) -> Optional[tuple[int, str, bool]]:
        """
        Возвращает (avfoundation_index, name, stub).
        stub=True если искали GoPro, но взяли обычную веб-камеру.
        """
        devices = self._list_avfoundation_devices()
        if not devices:
            return None

        wants_gopro = "gopro" in (label or "").lower()
        gopro = next(((i, n) for i, n in devices if "gopro" in n.lower()), None)
        if gopro:
            return (gopro[0], gopro[1], False)

        label_l = (label or "").strip().lower()
        if label_l and not wants_gopro:
            for idx, name in devices:
                if label_l in name.lower() or name.lower() in label_l:
                    return (idx, name, False)
        if device_id and not wants_gopro:
            tail = device_id[-8:].lower()
            for idx, name in devices:
                if tail in name.lower():
                    return (idx, name, False)

        stub = self._pick_stub_webcam(devices)
        if stub:
            return (stub[0], stub[1], True)
        return None

    @staticmethod
    def _pick_stub_webcam(devices: list[tuple[int, str]]) -> Optional[tuple[int, str]]:
        skip_tokens = ("obs", "virtual", "continuity", "iphone", "blackhole", "capture screen")
        ranked: list[tuple[int, int, str]] = []
        for idx, name in devices:
            low = name.lower()
            if "gopro" in low:
                continue
            if any(t in low for t in skip_tokens):
                continue
            score = 0
            if "facetime" in low or "built-in" in low or "встроенн" in low:
                score = 3
            elif "webcam" in low or "usb" in low or "camera" in low or "камер" in low:
                score = 1
            ranked.append((score, idx, name))
        if not ranked:
            # крайний случай — первая камера из списка
            return devices[0]
        ranked.sort(key=lambda t: (-t[0], t[1]))
        _, idx, name = ranked[0]
        return (idx, name)

    def _list_avfoundation_devices(self) -> list[tuple[int, str]]:
        now = time.time()
        if self._device_cache and now - self._device_cache_at < 30:
            return self._device_cache
        if not Path(FFMPEG).exists() and not shutil.which(FFMPEG):
            return []
        try:
            out = subprocess.run(
                [FFMPEG, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True,
                timeout=8,
            )
            text = (out.stderr or "") + (out.stdout or "")
        except (OSError, subprocess.TimeoutExpired):
            return []
        devices: list[tuple[int, str]] = []
        in_video = False
        for line in text.splitlines():
            if "AVFoundation video devices" in line:
                in_video = True
                continue
            if "AVFoundation audio devices" in line:
                in_video = False
                continue
            if not in_video:
                continue
            m = re.search(r"\[(\d+)\]\s+(.+)", line)
            if m:
                devices.append((int(m.group(1)), m.group(2).strip()))
        self._device_cache = devices
        self._device_cache_at = now
        return devices
```

## `apps/api_py/platforms.py`

```python
"""Интеграции YouTube, Twitch, Instagram, TikTok — OAuth, стримы, комментарии, статистика."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, List

PLATFORMS = ("youtube", "twitch", "instagram", "tiktok")


class PlatformAdapter(ABC):
    name: str

    @abstractmethod
    def authorize_url(self, redirect_uri: str, state: str) -> str:
        ...

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        ...

    @abstractmethod
    def fetch_comments(self, access_token: str, broadcast_id: str, limit: int = 50) -> List[dict]:
        ...

    @abstractmethod
    def post_comment(self, access_token: str, broadcast_id: str, text: str) -> dict:
        ...

    @abstractmethod
    def fetch_user_stats(self, access_token: str, external_user_id: str) -> dict:
        ...

    @abstractmethod
    def start_multicast(self, access_token: str, ingest_url: str, title: str) -> dict:
        ...


class _StubAdapter(PlatformAdapter):
    """Каркас адаптера: OAuth-ключи через env CMIR_{PLATFORM}_CLIENT_ID / _SECRET."""

    def __init__(self, name: str, oauth_base: str, api_base: str) -> None:
        self.name = name
        self.oauth_base = oauth_base
        self.api_base = api_base

    def _client_id(self) -> str:
        return os.environ.get(f"CMIR_{self.name.upper()}_CLIENT_ID", "")

    def _client_secret(self) -> str:
        return os.environ.get(f"CMIR_{self.name.upper()}_CLIENT_SECRET", "")

    def authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self._client_id() or f"cmir-{self.name}-demo",
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "read write broadcast",
        }
        return f"{self.oauth_base}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self._client_id():
            return {
                "access_token": f"demo-{self.name}-{code[:8]}",
                "refresh_token": "",
                "external_user_id": f"demo_{self.name}",
                "username": f"demo_{self.name}",
            }
        data = urllib.parse.urlencode(
            {
                "client_id": self._client_id(),
                "client_secret": self._client_secret(),
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.api_base}/oauth/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())

    def fetch_comments(self, access_token: str, broadcast_id: str, limit: int = 50) -> List[dict]:
        return []

    def post_comment(self, access_token: str, broadcast_id: str, text: str) -> dict:
        return {"id": f"local-{self.name}", "text": text, "status": "queued"}

    def fetch_user_stats(self, access_token: str, external_user_id: str) -> dict:
        return {"platform": self.name, "followers": 0, "views": 0, "external_user_id": external_user_id}

    def start_multicast(self, access_token: str, ingest_url: str, title: str) -> dict:
        return {
            "platform": self.name,
            "status": "pending_credentials" if not self._client_id() else "starting",
            "ingest_url": ingest_url,
            "title": title,
        }


ADAPTERS: Dict[str, PlatformAdapter] = {
    "youtube": _StubAdapter("youtube", "https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com"),
    "twitch": _StubAdapter("twitch", "https://id.twitch.tv/oauth2/authorize", "https://id.twitch.tv/oauth2"),
    "instagram": _StubAdapter("instagram", "https://api.instagram.com/oauth/authorize", "https://api.instagram.com"),
    "tiktok": _StubAdapter("tiktok", "https://www.tiktok.com/v2/auth/authorize", "https://open.tiktokapis.com"),
}


def get_adapter(platform: str) -> PlatformAdapter:
    if platform not in ADAPTERS:
        raise ValueError(f"unsupported platform: {platform}")
    return ADAPTERS[platform]
```

## `apps/api_py/preview_buffer.py`

```python
"""10-секундный зацикленный клип превью — запись сразу после старта маскированного потока."""
from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from database import db_path
from stream_paths import hls_playlist_ready, poi_masked_hls_url, poi_stream_name

PREVIEW_SECONDS = 10
PRIVACY_WARMUP_SEC = 1.0
PREVIEW_TARGET_SEC = PREVIEW_SECONDS
HLS_WAIT_SEC = 45.0
FFMPEG = __import__("shutil").which("ffmpeg") or "/usr/local/bin/ffmpeg"


def clip_path(poi_id: str) -> Path:
    d = db_path().parent / "buffers" / poi_id.replace("-", "")
    d.mkdir(parents=True, exist_ok=True)
    return d / "preview_loop.mp4"


class PreviewBuffer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._threads: Dict[str, threading.Thread] = {}
        self._stop: Dict[str, threading.Event] = {}
        self._started_at: Dict[str, float] = {}
        self._recording_at: Dict[str, float] = {}
        self._ready: Dict[str, bool] = {}
        self._error: Dict[str, str] = {}

    def start_capture(self, poi_id: str) -> None:
        with self._lock:
            alive = poi_id in self._threads and self._threads[poi_id].is_alive()
            if alive and self._ready.get(poi_id):
                return
            if alive:
                return
            self._threads.pop(poi_id, None)
            self._ready.pop(poi_id, None)
            self._error.pop(poi_id, None)
            self._recording_at.pop(poi_id, None)
            self._started_at[poi_id] = time.time()
            ev = threading.Event()
            self._stop[poi_id] = ev
            t = threading.Thread(target=self._run, args=(poi_id, ev), daemon=True)
            self._threads[poi_id] = t
            t.start()

    def stop_capture(self, poi_id: str) -> None:
        with self._lock:
            ev = self._stop.pop(poi_id, None)
            if ev:
                ev.set()
            self._threads.pop(poi_id, None)
            self._started_at.pop(poi_id, None)
            self._recording_at.pop(poi_id, None)
            self._ready.pop(poi_id, None)
            self._error.pop(poi_id, None)
        path = clip_path(poi_id)
        path.unlink(missing_ok=True)

    def status(self, poi_id: str) -> dict:
        with self._lock:
            started = self._started_at.get(poi_id)
            recording = self._recording_at.get(poi_id)
            ready = self._ready.get(poi_id, False)
            err = self._error.get(poi_id)
        path = clip_path(poi_id)
        if ready and path.is_file() and path.stat().st_size > 0:
            buffered = PREVIEW_SECONDS
        elif recording:
            buffered = min(PREVIEW_SECONDS, int(time.time() - recording))
        elif started:
            buffered = 0
        else:
            buffered = 0
        return {
            "ready": ready and path.is_file() and path.stat().st_size > 0,
            "buffered_seconds": buffered,
            "target_seconds": PREVIEW_TARGET_SEC,
            "recording": bool(recording) and not ready,
            "error": err,
            "clip_url": f"/api/v1/pois/{poi_id}/preview-clip.mp4" if ready else None,
        }

    def _fail(self, poi_id: str, message: str) -> None:
        with self._lock:
            self._error[poi_id] = message
            self._recording_at.pop(poi_id, None)

    def _run(self, poi_id: str, stop: threading.Event) -> None:
        masked_hls = poi_masked_hls_url(poi_id)
        deadline = time.time() + HLS_WAIT_SEC
        while time.time() < deadline:
            if stop.is_set():
                return
            if hls_playlist_ready(masked_hls, timeout=0.8):
                break
            time.sleep(0.25)
        else:
            self._fail(poi_id, "Маскированный поток не готов — проверьте MediaMTX и face-worker")
            return

        if PRIVACY_WARMUP_SEC > 0:
            time.sleep(PRIVACY_WARMUP_SEC)
            if stop.is_set():
                return

        stream = poi_stream_name(poi_id) + "_avatar"
        rtsp = f"rtsp://127.0.0.1:8554/{stream}"
        out = clip_path(poi_id)
        tmp = out.with_suffix(".tmp.mp4")
        with self._lock:
            self._recording_at[poi_id] = time.time()

        cmd = [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-probesize",
            "32768",
            "-analyzeduration",
            "500000",
            "-i",
            rtsp,
            "-t",
            str(PREVIEW_SECONDS),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(tmp),
        ]
        try:
            proc = subprocess.run(cmd, timeout=PREVIEW_SECONDS + 35, capture_output=True, text=True)
            if stop.is_set():
                tmp.unlink(missing_ok=True)
                return
            if proc.returncode == 0 and tmp.is_file() and tmp.stat().st_size > 0:
                tmp.replace(out)
                with self._lock:
                    self._ready[poi_id] = True
                    self._recording_at.pop(poi_id, None)
                    self._error.pop(poi_id, None)
                print(f"[preview] clip ready poi {poi_id[:8]}… ({PREVIEW_SECONDS}s)")
            else:
                tmp.unlink(missing_ok=True)
                detail = (proc.stderr or "").strip().splitlines()[-1] if proc.stderr else ""
                self._fail(poi_id, detail or "ffmpeg не записал превью")
        except (OSError, subprocess.TimeoutExpired) as e:
            tmp.unlink(missing_ok=True)
            self._fail(poi_id, str(e))
        finally:
            with self._lock:
                self._recording_at.pop(poi_id, None)
```

## `apps/api_py/server.py`

```python
#!/usr/bin/env python3
"""
Cmir API — Python (Phase 2 core: SQLite users, auth, consents, wallets).
Port 8090.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sys
import http.cookiejar
import urllib.parse
import urllib.request
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from database import app_env  # noqa: E402
from camera_health import probe_stream_url  # noqa: E402
from local_relay import LocalRelay  # noqa: E402
from store import CAMERA_ROLES, PATCH_DIM, VIEW_MODES, Store  # noqa: E402
from stream_paths import (
    hls_direct_to_proxy,
    hls_playlist_ready,
    hls_proxy_url,
    masked_stream_hls,
    poi_hls_proxy_url,
    poi_hls_url,
    poi_masked_hls_proxy_url,
    poi_masked_hls_url,
    poi_stream_name,
    stream_url_to_hls,
)  # noqa: E402

HOST, PORT = "0.0.0.0", 8090
STORE = Store()
LOCAL_RELAY = LocalRelay(STORE)
_MTX_JAR = http.cookiejar.CookieJar()
_MTX_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_MTX_JAR))


def public_base_url(handler: BaseHTTPRequestHandler) -> str:
    host = handler.headers.get("Host") or f"localhost:{PORT}"
    return f"http://{host}"


def preview_clip_public_url(handler: BaseHTTPRequestHandler, clip_path: str) -> str:
    return f"{public_base_url(handler)}{clip_path}"


def proxy_hls_response(handler: BaseHTTPRequestHandler, rel_path: str) -> None:
    from urllib.parse import urljoin

    upstream = f"http://127.0.0.1:8888/{rel_path}"
    try:
        with _MTX_OPENER.open(upstream, timeout=15) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "application/octet-stream")
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            loc = e.headers["Location"]
            if loc.startswith("/"):
                loc = urljoin(upstream, loc)
            try:
                with _MTX_OPENER.open(loc, timeout=15) as resp:
                    data = resp.read()
                    ctype = resp.headers.get("Content-Type", "application/octet-stream")
            except (urllib.error.URLError, OSError, TimeoutError) as err:
                return json_response(handler, 502, {"success": False, "error": str(err)})
        else:
            body = e.read()
            handler.send_response(e.code)
            handler.send_header("Access-Control-Allow-Origin", "*")
            handler.send_header("Content-Type", e.headers.get("Content-Type", "text/plain"))
            handler.send_header("Content-Length", str(len(body)))
            handler.end_headers()
            handler.wfile.write(body)
            return
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return json_response(handler, 502, {"success": False, "error": str(e)})

    if rel_path.endswith(".m3u8"):
        base = rel_path.split("?")[0].rsplit("/", 1)[0]
        lines = []
        for line in data.decode(errors="replace").splitlines():
            if line.startswith("#") or not line.strip():
                lines.append(line)
                continue
            uri = line.strip()
            if uri.startswith("http://") or uri.startswith("https://"):
                parsed = urlparse(uri)
                seg = parsed.path.lstrip("/")
                if parsed.query:
                    seg += "?" + parsed.query
                lines.append(hls_proxy_url(seg))
            elif uri.startswith("/"):
                lines.append(hls_proxy_url(uri.lstrip("/")))
            else:
                lines.append(hls_proxy_url(f"{base}/{uri}"))
        data = "\n".join(lines).encode()

    handler.send_response(200)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Type", ctype if rel_path.endswith(".m3u8") else ctype)
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def json_response(handler: BaseHTTPRequestHandler, code: int, body: dict) -> None:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def bearer_token(handler: BaseHTTPRequestHandler) -> str:
    auth = handler.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def require_user(handler: BaseHTTPRequestHandler) -> Optional[dict]:
    user = STORE.user_from_token(bearer_token(handler))
    if not user:
        json_response(handler, 401, {"success": False, "error": "unauthorized"})
        return None
    return user


def require_admin(handler: BaseHTTPRequestHandler) -> Optional[dict]:
    user = require_user(handler)
    if user is None:
        return None
    if not STORE.is_admin(user):
        json_response(handler, 403, {"success": False, "error": "admin required"})
        return None
    return user


def _worker_authorized(handler: BaseHTTPRequestHandler) -> bool:
    """Face-worker: X-Cmir-Worker must match CMIR_WORKER_TOKEN (always required)."""
    expected = os.environ.get("CMIR_WORKER_TOKEN", "").strip()
    got = (handler.headers.get("X-Cmir-Worker") or "").strip()
    if not expected or not got:
        return False
    return secrets.compare_digest(expected, got)


def parse_multipart(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    """Minimal multipart parser for single file upload."""
    ctype = handler.headers.get("Content-Type", "")
    if "multipart/form-data" not in ctype:
        return {}
    m = re.search(r'boundary=(?:"([^"]+)"|([^\s;]+))', ctype)
    if not m:
        return {}
    boundary = (m.group(1) or m.group(2)).encode()
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length)
    parts = body.split(b"--" + boundary)
    out: dict[str, Any] = {}
    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        header, _, data = part.partition(b"\r\n\r\n")
        data = data.rstrip(b"\r\n")
        if data.endswith(b"--"):
            data = data[:-2]
        hdr = header.decode("utf-8", errors="replace")
        name_m = re.search(r'name="([^"]+)"', hdr)
        file_m = re.search(r'filename="([^"]*)"', hdr)
        if not name_m:
            continue
        name = name_m.group(1)
        if file_m and file_m.group(1):
            out[name] = {"filename": file_m.group(1), "data": data}
        else:
            out[name] = data.decode("utf-8", errors="replace").strip()
    return out


def handle_mask_image_upload(handler: BaseHTTPRequestHandler, poi_id: str) -> bool:
    """POST multipart mask — must run before JSON body read. Returns True if handled."""
    if require_admin(handler) is None:
        return True
    form = parse_multipart(handler)
    file_part = form.get("image") or form.get("file")
    if not isinstance(file_part, dict) or not file_part.get("data"):
        json_response(handler, 400, {"success": False, "error": "image file required"})
        return True
    fname = file_part.get("filename", "mask.png")
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "png"
    if ext not in ("png", "jpg", "jpeg", "webp"):
        ext = "png"
    try:
        STORE.save_mask_image(poi_id, file_part["data"], ext)
    except KeyError:
        json_response(handler, 404, {"success": False, "error": "poi not found"})
        return True
    LOCAL_RELAY.restart_poi(poi_id)
    json_response(
        handler,
        200,
        {"success": True, "data": {"mask_image_url": f"/api/v1/pois/{poi_id}/mask-image"}},
    )
    return True


def geocode_query(q: str) -> dict:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"format": "json", "limit": 1, "q": q}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Cmir/0.4.0 (local dev)"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read())
    if not data:
        raise ValueError("address not found")
    hit = data[0]
    return {
        "lat": float(hit["lat"]),
        "lon": float(hit["lon"]),
        "display_name": hit.get("display_name", q),
    }


def reverse_geocode(lat: float, lon: float) -> dict:
    url = "https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode(
        {"format": "json", "lat": lat, "lon": lon, "zoom": 18, "addressdetails": 1}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Cmir/0.4.0 (local dev)"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read())
    if not data or "error" in data:
        raise ValueError("location not found")
    addr = data.get("address") or {}
    house = addr.get("house_number", "")
    road = addr.get("road") or addr.get("pedestrian") or addr.get("footway") or ""
    street = f"{road} {house}".strip() if road or house else ""
    return {
        "lat": float(data.get("lat", lat)),
        "lon": float(data.get("lon", lon)),
        "display_name": data.get("display_name") or street or f"{lat:.6f}, {lon:.6f}",
        "street": street,
        "building": addr.get("building") or addr.get("amenity") or "",
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[api] {args[0]}")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]
        qs = parse_qs(urlparse(self.path).query)
        city = qs.get("city", [None])[0]
        country = qs.get("country", [None])[0]

        if path == "/health":
            return json_response(
                self,
                200,
                {"status": "healthy", "service": "cmir-api-py", "version": "0.4.0", "phase": "2-core", "environment": app_env()},
            )

        if path == "/api/v1/geocode":
            q = qs.get("q", [""])[0].strip()
            if not q:
                return json_response(self, 400, {"success": False, "error": "q required"})
            try:
                data = geocode_query(q)
            except ValueError as e:
                return json_response(self, 404, {"success": False, "error": str(e)})
            except OSError as e:
                return json_response(self, 502, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/reverse-geocode":
            try:
                lat = float(qs.get("lat", [""])[0])
                lon = float(qs.get("lon", [""])[0])
            except (TypeError, ValueError):
                return json_response(self, 400, {"success": False, "error": "lat and lon required"})
            try:
                data = reverse_geocode(lat, lon)
            except ValueError as e:
                return json_response(self, 404, {"success": False, "error": str(e)})
            except OSError as e:
                return json_response(self, 502, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/auth/me":
            user = require_user(self)
            if user is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.user_public(user)})

        if path == "/api/v1/legal/documents":
            from compliance import list_legal_documents

            return json_response(
                self, 200, {"success": True, "data": list_legal_documents(STORE.conn)}
            )

        if len(parts) >= 4 and parts[0] == "api" and parts[1] == "v1" and parts[2] == "hls":
            rel = "/".join(parts[3:])
            q = urlparse(self.path).query
            if q:
                rel = f"{rel}?{q}"
            return proxy_hls_response(self, rel)

        if path == "/api/v1/auth/platforms":
            user = require_user(self)
            if user is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.list_platform_links(user["id"])})

        if path == "/api/v1/auth/recordings":
            user = require_user(self)
            if user is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.list_user_recordings(user["id"])})

        if len(parts) == 5 and parts[2] == "recordings" and parts[4] == "clip.mp4":
            user = require_user(self)
            if user is None:
                return
            rec = STORE.conn.execute(
                "SELECT clip_path FROM stream_recordings WHERE id = ? AND user_id = ?",
                (parts[3], user["id"]),
            ).fetchone()
            if not rec or not rec["clip_path"]:
                return json_response(self, 404, {"success": False, "error": "clip not found"})
            from pathlib import Path

            path = Path(rec["clip_path"])
            if not path.is_file():
                return json_response(self, 404, {"success": False, "error": "file missing"})
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if len(parts) == 5 and parts[2] == "platforms" and parts[4] == "authorize":
            user = require_user(self)
            if user is None:
                return
            from platforms import get_adapter

            platform = parts[3]
            try:
                adapter = get_adapter(platform)
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            redirect = f"http://127.0.0.1:{PORT}/api/v1/platforms/{platform}/oauth-callback"
            state = f"{user['id']}:{secrets.token_urlsafe(8)}"
            return json_response(
                self,
                200,
                {"success": True, "data": {"authorize_url": adapter.authorize_url(redirect, state), "state": state}},
            )

        if len(parts) == 5 and parts[2] == "platforms" and parts[4] == "oauth-callback":
            qs = parse_qs(urlparse(self.path).query)
            code = (qs.get("code") or [""])[0]
            state = (qs.get("state") or [""])[0]
            platform = parts[3]
            user_id = state.split(":")[0] if state else ""
            if not code or not user_id:
                return json_response(self, 400, {"success": False, "error": "invalid oauth callback"})
            from platforms import get_adapter

            try:
                adapter = get_adapter(platform)
                redirect = f"http://127.0.0.1:{PORT}/api/v1/platforms/{platform}/oauth-callback"
                token_data = adapter.exchange_code(code, redirect)
                data = STORE.platform_oauth_complete(user_id, platform, token_data)
            except (ValueError, KeyError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            self.send_response(302)
            self.send_header("Location", "/index.html#account")
            self.end_headers()
            return

        if len(parts) == 5 and parts[2] == "platforms" and parts[4] == "comments":
            user = require_user(self)
            if user is None:
                return
            qs = parse_qs(urlparse(self.path).query)
            broadcast_id = (qs.get("broadcast_id") or [""])[0]
            try:
                data = STORE.sync_platform_comments(user["id"], parts[3], broadcast_id)
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "preview-clip":
            poi_id = parts[3]
            st = LOCAL_RELAY.preview.status(poi_id)
            if st.get("clip_url"):
                st = {
                    **st,
                    "clip_url": preview_clip_public_url(self, st["clip_url"]),
                }
            return json_response(self, 200, {"success": True, "data": st})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "preview-clip.mp4":
            from preview_buffer import clip_path

            path = clip_path(parts[3])
            if not path.is_file():
                return json_response(self, 404, {"success": False, "error": "preview not ready"})
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "menu-items":
            try:
                items = STORE.poi_menu_items(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": items})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "kiosk-stream":
            poi_id = parts[3]
            cam = STORE.conn.execute(
                """
                SELECT id FROM cameras WHERE poi_id = ? AND role = 'consent' AND is_active = 1
                ORDER BY slot_index LIMIT 1
                """,
                (poi_id,),
            ).fetchone()
            if not cam:
                cam = STORE.conn.execute(
                    """
                    SELECT id FROM cameras WHERE poi_id = ? AND is_active = 1 AND is_preview = 1
                    LIMIT 1
                    """,
                    (poi_id,),
                ).fetchone()
            if not cam:
                return json_response(self, 404, {"success": False, "error": "no camera"})
            cam_obj = STORE.get_camera(cam["id"])
            is_local = cam_obj.source_type == "local_usb" or cam_obj.stream_url.startswith("local://")
            client_id = qs.get("client_id", [""])[0] or "kiosk"
            if is_local:
                LOCAL_RELAY.acquire(poi_id, client_id, wait_hls=True)
            masked_direct = masked_stream_hls(cam_obj.stream_url, poi_id)
            raw_direct = stream_url_to_hls(cam_obj.stream_url, poi_id)
            if is_local:
                masked = poi_masked_hls_proxy_url(poi_id)
                raw = poi_hls_proxy_url(poi_id)
                m_ready = hls_playlist_ready(poi_masked_hls_url(poi_id))
                r_ready = hls_playlist_ready(poi_hls_url(poi_id))
            else:
                masked = hls_direct_to_proxy(masked_direct)
                raw = hls_direct_to_proxy(raw_direct)
                m_ready = hls_playlist_ready(masked_direct) if masked_direct else False
                r_ready = hls_playlist_ready(raw_direct) if raw_direct else False
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "data": {
                        "masked_hls_url": masked if m_ready else None,
                        "hls_url": None,
                        "live_hls_url": masked if m_ready else None,
                        "stream_ready": m_ready,
                        "masked_ready": m_ready,
                        "privacy_buffered": m_ready,
                    },
                },
            )

        if path == "/api/v1/consented-faces":
            if not _worker_authorized(self):
                return json_response(self, 401, {"success": False, "error": "worker token required"})
            return json_response(
                self,
                200,
                {"success": True, "data": {"faces": STORE.global_consented_faces()}},
            )

        if path == "/api/v1/face-presence":
            user = require_user(self)
            if user is None:
                return
            qs_cam = qs.get("camera_id", [None])[0]
            qs_period = qs.get("period_key", [None])[0]
            if STORE.is_admin(user):
                qs_user = qs.get("user_id", [None])[0]
                data = STORE.list_face_presence(user_id=qs_user, camera_id=qs_cam, period_key=qs_period)
            else:
                data = STORE.list_face_presence(user_id=user["id"], camera_id=qs_cam, period_key=qs_period)
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/pois":
            return json_response(self, 200, {"success": True, "data": STORE.list_pois()})

        if path == "/api/v1/tops/consent":
            items = STORE.sorted_tops("consent", city, country)
            return json_response(
                self, 200, {"success": True, "data": items, "filter": {"city": city, "country": country}}
            )

        if path == "/api/v1/tops/participants":
            items = STORE.sorted_tops("participants", city, country)
            return json_response(
                self, 200, {"success": True, "data": items, "filter": {"city": city, "country": country}}
            )

        if path == "/api/v1/donations":
            poi_f = qs.get("poi_id", [None])[0]
            return json_response(self, 200, {"success": True, "data": STORE.list_donations(poi_f)})

        if len(parts) == 4 and parts[0] == "api" and parts[1] == "v1" and parts[2] == "pois":
            poi_id = parts[3]
            try:
                data = STORE.poi_payload(poi_id)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "embeddings":
            if not (_worker_authorized(self) or STORE.is_admin(STORE.user_from_token(bearer_token(self)) or {})):
                return json_response(self, 401, {"success": False, "error": "worker or admin required"})
            poi_id = parts[3]
            try:
                embs = STORE.poi_embeddings(poi_id)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(
                self,
                200,
                {"success": True, "data": {"poi_id": poi_id, "embeddings": embs, "count": len(embs)}},
            )

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "scene":
            try:
                data = STORE.scene_description(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 4 and parts[2] == "cameras":
            cam = STORE.get_camera(parts[3])
            if not cam:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            return json_response(self, 200, {"success": True, "data": asdict(cam)})

        if len(parts) == 5 and parts[2] == "cameras" and parts[4] == "health":
            cam = STORE.get_camera(parts[3])
            if not cam:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            probe = probe_stream_url(cam.stream_url)
            data = {
                "camera_id": cam.id,
                "poi_id": cam.poi_id,
                "stream_url": cam.stream_url,
                "is_active": cam.is_active,
                **probe,
            }
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "cameras" and parts[4] == "playback":
            cam = STORE.get_camera(parts[3])
            if not cam:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            is_local = cam.source_type == "local_usb" or cam.stream_url.startswith("local://")
            client_id = qs.get("client_id", [""])[0] or "playback-anon"
            if is_local:
                LOCAL_RELAY.acquire(cam.poi_id, client_id, wait_hls=True)
            hls_direct = stream_url_to_hls(cam.stream_url, cam.poi_id)
            masked_direct = masked_stream_hls(cam.stream_url, cam.poi_id)
            stream_ready = hls_playlist_ready(hls_direct) if hls_direct else False
            masked_ready = hls_playlist_ready(masked_direct) if masked_direct else False
            if is_local:
                hls = poi_hls_proxy_url(cam.poi_id)
                masked = poi_masked_hls_proxy_url(cam.poi_id)
            else:
                hls = hls_direct_to_proxy(hls_direct)
                masked = hls_direct_to_proxy(masked_direct)
            preview = LOCAL_RELAY.preview.status(cam.poi_id) if is_local else {"ready": False}
            if preview.get("clip_url"):
                preview = {**preview, "clip_url": preview_clip_public_url(self, preview["clip_url"])}
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "data": {
                        "camera_id": cam.id,
                        "poi_id": cam.poi_id,
                        "stream_url": cam.stream_url,
                        "source_type": cam.source_type,
                        "hls_url": hls if (masked_ready or not is_local) and stream_ready else None,
                        "masked_hls_url": masked if masked_ready else None,
                        "fallback_hls_url": None,
                        "live_hls_url": masked if masked_ready else None,
                        "stream_ready": masked_ready if is_local else stream_ready,
                        "masked_ready": masked_ready,
                        "privacy_buffered": masked_ready,
                        "preview_clip": preview,
                        "rtsp_url": cam.stream_url if cam.stream_url.startswith("rtsp") else None,
                    },
                },
            )

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "mask-image":
            path = STORE.get_mask_image_path(parts[3])
            if not path:
                return json_response(self, 404, {"success": False, "error": "no mask image"})
            data = path.read_bytes()
            ext = path.suffix.lower()
            mime = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
            }.get(ext, "image/png")
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path == "/api/v1/admin/network-quality":
            if require_admin(self) is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.network_quality()})

        if path == "/api/v1/admin/stats":
            if require_admin(self) is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.admin_stats()})

        if path == "/api/v1/admin/users":
            if require_admin(self) is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.list_users()})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "airtime":
            try:
                data = STORE.list_airtime(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 4 and parts[2] == "wallets":
            w = STORE.get_wallet(parts[3])
            if not w:
                return json_response(self, 404, {"success": False, "error": "wallet not found"})
            return json_response(self, 200, {"success": True, "data": w})

        if path == "/api/v1/cameras/health-all":
            data = []
            for row in STORE.conn.execute("SELECT id FROM cameras WHERE is_active = 1").fetchall():
                cam = STORE.get_camera(row["id"])
                if cam:
                    probe = probe_stream_url(cam.stream_url)
                    data.append(
                        {
                            "camera_id": cam.id,
                            "poi_id": cam.poi_id,
                            "stream_url": cam.stream_url,
                            "is_active": cam.is_active,
                            **probe,
                        }
                    )
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "admin" and parts[4] == "health-history":
            hist = STORE.health_snapshots.get(parts[3], [])
            return json_response(self, 200, {"success": True, "data": hist})

        if path == "/api/v1/performance/streams":
            user = require_user(self)
            if user is None:
                return
            qs = parse_qs(urlparse(self.path).query)
            camera_id = (qs.get("camera_id") or [""])[0]
            if not camera_id:
                return json_response(self, 400, {"success": False, "error": "camera_id required"})
            return json_response(
                self,
                200,
                {"success": True, "data": STORE.performance_stream_list(user["id"], camera_id)},
            )

        json_response(self, 404, {"success": False, "error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "mask-image":
            handle_mask_image_upload(self, parts[3])
            return

        body = self._read_json()

        if path == "/api/v1/auth/register":
            try:
                user = STORE.register_user(
                    body.get("email", ""),
                    body.get("password", ""),
                    body.get("display_name", ""),
                )
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": user})

        if path == "/api/v1/auth/login":
            try:
                data = STORE.login_user(body.get("email", ""), body.get("password", ""))
            except ValueError as e:
                return json_response(self, 401, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/auth/logout":
            STORE.logout_user(bearer_token(self))
            return json_response(self, 200, {"success": True, "message": "logged out"})

        if path == "/api/v1/pois":
            if require_admin(self) is None:
                return
            try:
                poi = STORE.create_poi(body)
            except (KeyError, ValueError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": asdict(poi)})

        if path == "/api/v1/admin/users":
            if require_admin(self) is None:
                return
            try:
                user = STORE.create_user_admin(body)
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": user})

        if len(parts) == 6 and parts[2] == "admin" and parts[3] == "users" and parts[5] == "block":
            if require_admin(self) is None:
                return
            user_id = parts[4]
            hours = float(body.get("hours", 24))
            from datetime import datetime, timedelta, timezone

            until = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
            if body.get("until"):
                until = body["until"]
            try:
                user = STORE.block_user(user_id, until)
            except (KeyError, ValueError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": user})

        if len(parts) == 6 and parts[2] == "admin" and parts[3] == "users" and parts[5] == "unblock":
            if require_admin(self) is None:
                return
            try:
                user = STORE.unblock_user(parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "user not found"})
            return json_response(self, 200, {"success": True, "data": user})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "cameras":
            if require_admin(self) is None:
                return
            poi_id = parts[3]
            if body.get("view_mode") not in VIEW_MODES:
                return json_response(
                    self, 400, {"success": False, "error": f"view_mode must be one of {sorted(VIEW_MODES)}"}
                )
            if body.get("role") not in CAMERA_ROLES:
                return json_response(
                    self, 400, {"success": False, "error": f"role must be one of {sorted(CAMERA_ROLES)}"}
                )
            try:
                cam = STORE.add_camera(poi_id, body)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            warn = STORE.validate_cameras(poi_id)
            payload = asdict(cam)
            if warn:
                payload["validation_warning"] = warn
            return json_response(self, 200, {"success": True, "data": payload})

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "stream" and parts[5] == "acquire":
            poi_id = parts[3]
            if app_env() == "prod" and require_user(self) is None:
                return
            cid = body.get("client_id") or "anonymous"
            wait = bool(body.get("wait_hls", True))
            # browser_usb: клиент держит FaceTime через getUserMedia — освобождаем ffmpeg
            if body.get("browser_usb") or body.get("publish") is False:
                LOCAL_RELAY.force_stop(poi_id)
                return json_response(
                    self,
                    200,
                    {
                        "success": True,
                        "data": {
                            "acquired": True,
                            "local_usb": True,
                            "browser_usb": True,
                            "clients": LOCAL_RELAY.active_clients(poi_id),
                        },
                    },
                )
            row = LOCAL_RELAY._row_for_poi(poi_id)
            if not row:
                return json_response(
                    self,
                    200,
                    {"success": True, "data": {"acquired": True, "local_usb": False, "clients": 0}},
                )
            ok = LOCAL_RELAY.acquire(poi_id, cid, wait_hls=wait)
            preview = LOCAL_RELAY.preview.status(poi_id)
            if preview.get("clip_url"):
                preview = {**preview, "clip_url": preview_clip_public_url(self, preview["clip_url"])}
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "data": {
                        "acquired": ok,
                        "local_usb": True,
                        "clients": LOCAL_RELAY.active_clients(poi_id),
                        "preview_clip": preview,
                    },
                },
            )

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "stream" and parts[5] == "release":
            poi_id = parts[3]
            cid = body.get("client_id") or "anonymous"
            if body.get("force"):
                if require_admin(self) is None:
                    return
                LOCAL_RELAY.force_stop(poi_id)
            else:
                if app_env() == "prod" and require_user(self) is None:
                    return
                LOCAL_RELAY.release(poi_id, cid)
            return json_response(
                self,
                200,
                {"success": True, "data": {"clients": LOCAL_RELAY.active_clients(poi_id)}},
            )

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "kiosk-register":
            poi_id = parts[3]
            emb = body.get("face_embedding")
            embs = body.get("face_embeddings")
            acceptances = body.get("acceptances") or {}
            try:
                data = STORE.kiosk_register(
                    poi_id,
                    body.get("full_name", ""),
                    body.get("phone", ""),
                    body.get("favorite_menu_item", ""),
                    emb if isinstance(emb, list) else None,
                    acceptances,
                    client_meta={"ip": self.client_address[0]},
                    embeddings=embs if isinstance(embs, list) else None,
                    require_multi=True,
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            LOCAL_RELAY.restart_poi(poi_id)
            return json_response(
                self,
                200,
                {"success": True, "data": data, "message": data.get("message", "")},
            )

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "signature-bind":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.bind_signature(user["id"], parts[3])
            except ValueError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/performance/streams":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.performance_stream_start(
                    user["id"],
                    body.get("camera_id", ""),
                    body.get("title", ""),
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/general/streams":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.general_stream_start(
                    user["id"],
                    body.get("camera_id", ""),
                    body.get("title", ""),
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 6 and parts[2] == "general" and parts[3] == "streams" and parts[5] == "stop":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.general_stream_stop(user["id"], parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "recording not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/auth/platforms/link":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.link_platform_username(
                    user["id"], body.get("platform", ""), body.get("username", "")
                )
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "platforms" and parts[4] == "comment":
            user = require_user(self)
            if user is None:
                return
            from platforms import get_adapter

            platform = parts[3]
            try:
                link = STORE.conn.execute(
                    "SELECT oauth_token FROM platform_links WHERE user_id = ? AND platform = ?",
                    (user["id"], platform),
                ).fetchone()
                if not link or not link["oauth_token"]:
                    raise ValueError("platform oauth required")
                adapter = get_adapter(platform)
                data = adapter.post_comment(
                    link["oauth_token"], body.get("broadcast_id", ""), body.get("text", "")
                )
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 6 and parts[2] == "performance" and parts[3] == "streams" and parts[5] == "stop":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.performance_stream_stop(user["id"], parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "stream not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "consent":
            user = require_user(self)
            if user is None:
                return
            poi_id = parts[3]
            emb = body.get("face_embedding")
            if isinstance(emb, list) and len(emb) != PATCH_DIM:
                return json_response(
                    self,
                    400,
                    {"success": False, "error": f"face_embedding must be {PATCH_DIM} floats"},
                )
            try:
                rec = STORE.grant_consent(poi_id, user["id"], emb)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except ValueError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "data": rec,
                    "message": "Consent recorded; linked to your wallet",
                },
            )

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "cameras" and parts[5] == "sync":
            if require_admin(self) is None:
                return
            try:
                data = STORE.sync_poi_cameras(parts[3], body.get("cameras", []))
            except (KeyError, ValueError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            LOCAL_RELAY.refresh()
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/views":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.record_view(
                    user["id"],
                    body.get("camera_id", ""),
                    float(body.get("seconds", 0)),
                    float(body.get("ad_revenue", 0.01)),
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/face-match":
            emb = body.get("embedding")
            if not isinstance(emb, list):
                return json_response(self, 400, {"success": False, "error": "embedding required"})
            try:
                vec = [float(x) for x in emb]
            except (TypeError, ValueError):
                return json_response(self, 400, {"success": False, "error": "invalid embedding"})
            hit = STORE.match_face_embedding(
                vec,
                prior_user_id=str(body.get("prior_user_id") or ""),
            )
            if not hit:
                return json_response(self, 200, {"success": True, "data": {"matched": False}})
            return json_response(self, 200, {"success": True, "data": hit})

        if path == "/api/v1/face-presence":
            # face-worker: пакет presence с worker-token; пользователь — только self
            items = body.get("presence")
            if items is None and body.get("user_id") and body.get("camera_id"):
                items = [
                    {
                        "user_id": body.get("user_id"),
                        "camera_id": body.get("camera_id"),
                        "seconds": body.get("seconds", 0),
                    }
                ]
            if not isinstance(items, list) or not items:
                return json_response(self, 400, {"success": False, "error": "presence[] required"})
            worker_ok = _worker_authorized(self)
            user = None
            if not worker_ok:
                user = require_user(self)
                if user is None:
                    return
            results = []
            for it in items:
                uid = it.get("user_id") or (user["id"] if user else "")
                if user and not STORE.is_admin(user) and uid != user["id"]:
                    return json_response(self, 403, {"success": False, "error": "forbidden"})
                try:
                    results.append(
                        STORE.record_face_presence(
                            uid,
                            it.get("camera_id") or body.get("camera_id", ""),
                            float(it.get("seconds", 0)),
                            it.get("period_key"),
                        )
                    )
                except KeyError:
                    return json_response(self, 404, {"success": False, "error": "not found"})
                except ValueError as e:
                    return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": {"results": results}})

        if path == "/api/v1/admin/reset-test-pois":
            if require_admin(self) is None:
                return
            try:
                n = STORE.clear_all_pois()
            except ValueError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": {"deleted": n}})

        if path == "/api/v1/admin/seed-demo":
            if require_admin(self) is None:
                return
            try:
                created = STORE.ensure_demo_fixtures()
            except ValueError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            return json_response(
                self,
                200,
                {"success": True, "data": {"created": created, "pois": STORE.list_pois()}},
            )

        if path == "/api/v1/admin/health-snapshot":
            snap = STORE.record_health_snapshot(
                body.get("camera_id", ""),
                body.get("status", "unknown"),
                body.get("detail", ""),
            )
            return json_response(self, 200, {"success": True, "data": snap})

        if path == "/api/v1/donations":
            poi_id = body.get("poi_id", "")
            try:
                d = STORE.add_donation(
                    poi_id,
                    float(body.get("amount", 0)),
                    body.get("message", ""),
                    body.get("donor", "anonymous"),
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            return json_response(self, 200, {"success": True, "data": d})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "airtime":
            try:
                entry = STORE.add_airtime(
                    parts[3], body.get("wallet", ""), float(body.get("seconds", 0))
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            return json_response(self, 200, {"success": True, "data": entry})

        json_response(self, 404, {"success": False, "error": "not found"})

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]
        body = self._read_json()

        if path == "/api/v1/auth/profile":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.update_user_profile(user["id"], body)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "user not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 4 and parts[2] == "pois":
            if require_admin(self) is None:
                return
            try:
                STORE.update_poi(parts[3], body)
                data = STORE.poi_payload(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 4 and parts[2] == "cameras":
            if require_admin(self) is None:
                return
            try:
                cam = STORE.update_camera(parts[3], body)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            warn = STORE.validate_cameras(cam.poi_id)
            payload = asdict(cam)
            if warn:
                payload["validation_warning"] = warn
            return json_response(self, 200, {"success": True, "data": payload})

        if len(parts) == 5 and parts[2] == "admin" and parts[3] == "users":
            if require_admin(self) is None:
                return
            try:
                user = STORE.update_user_admin(parts[4], body)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "user not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": user})

        json_response(self, 404, {"success": False, "error": "not found"})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]

        if len(parts) == 4 and parts[2] == "pois":
            if require_admin(self) is None:
                return
            try:
                STORE.delete_poi(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            return json_response(self, 200, {"success": True, "message": "poi deleted"})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "mask-image":
            if require_admin(self) is None:
                return
            STORE.delete_mask_image(parts[3])
            LOCAL_RELAY.restart_poi(parts[3])
            return json_response(self, 200, {"success": True, "message": "mask removed"})

        if len(parts) == 5 and parts[2] == "admin" and parts[3] == "users":
            if require_admin(self) is None:
                return
            try:
                STORE.delete_user(parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "user not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "message": "user deleted"})

        if len(parts) == 5 and parts[2] == "auth" and parts[3] == "platforms":
            user = require_user(self)
            if user is None:
                return
            try:
                STORE.unlink_platform(user["id"], parts[4])
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "message": "platform unlinked"})

        if len(parts) == 5 and parts[2] == "performance" and parts[3] == "streams":
            user = require_user(self)
            if user is None:
                return
            try:
                STORE.performance_stream_delete(user["id"], parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "stream not found"})
            return json_response(self, 200, {"success": True, "message": "stream deleted"})

        if len(parts) == 4 and parts[2] == "cameras":
            if require_admin(self) is None:
                return
            try:
                poi_id = STORE.delete_camera(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            warn = STORE.validate_cameras(poi_id)
            return json_response(
                self, 200, {"success": True, "message": "camera deleted", "validation_warning": warn}
            )

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "consent":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.revoke_consent(parts[3], parts[5], user_id=user["id"])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        json_response(self, 404, {"success": False, "error": "not found"})


def main() -> None:
    print(f"Cmir API (Python) http://{HOST}:{PORT} — SQLite core")
    HTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
```

## `apps/api_py/store.py`

```python
"""Persistent store — SQLite backend for Cmir core."""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from auth import hash_password, is_blocked, is_session_valid, new_session_token, session_expires, verify_password
from compliance import (
    LEGAL_VERSION,
    audit_log,
    blockchain_record,
    decrypt_embedding,
    encrypt_embedding,
    ensure_legal_documents,
    list_legal_documents,
    normalize_phone,
    phone_to_email,
    require_data_key_in_prod,
    validate_acceptances,
)
from database import app_env, connect, masks_dir, row_to_dict
from face_profiles import MIN_TEMPLATES, REQUIRED_POSES, normalize_face_templates
from stream_paths import poi_rtmp_url
from stream_recorder import RECORDER

PATCH_DIM = 32 * 32
# Доля рекламного бюджета, распределяемая зрителям-в-кадре (utility tokens)
AD_USER_POOL_RATIO = 0.5
# 1 единица денежной выручки рекламы → столько UT при полном пуле
AD_UT_PER_REVENUE = 100.0
VIEW_MODES = frozenset({"fisheye", "standard", "zoom2x"})
CAMERA_ROLES = frozenset({"general", "consent", "performance"})


class PoiType(str, Enum):
    LIVE_CAM = "live_cam"
    SOCIAL_EVENT = "social_event"
    VENUE = "venue"

    def min_cameras(self) -> int:
        return {PoiType.LIVE_CAM: 1, PoiType.SOCIAL_EVENT: 2, PoiType.VENUE: 3}[self]

    def min_consent_cameras(self) -> int:
        return {PoiType.LIVE_CAM: 0, PoiType.SOCIAL_EVENT: 1, PoiType.VENUE: 1}[self]

    def min_performance_cameras(self) -> int:
        return {PoiType.LIVE_CAM: 0, PoiType.SOCIAL_EVENT: 0, PoiType.VENUE: 1}[self]


POI_TYPES = {e.value: e for e in PoiType}

DEMO_POI_NAMES = (
    "Demo: Social Event — Пингвинья вечеринка",
    "Тестовое место",
)


@dataclass
class Poi:
    id: str
    name: str
    description: str
    poi_type: str
    latitude: float
    longitude: float
    promo_description: str
    city: str
    country: str
    created_at: str
    updated_at: str


@dataclass
class Camera:
    id: str
    poi_id: str
    name: str
    stream_url: str
    role: str
    view_mode: str
    is_active: bool
    created_at: str
    device_id: str = ""
    device_label: str = ""
    slot_index: int = 0
    is_preview: bool = False
    source_type: str = "rtsp"


def _row_to_camera(row: sqlite3.Row) -> Camera:
    return Camera(
        id=row["id"],
        poi_id=row["poi_id"],
        name=row["name"],
        stream_url=row["stream_url"] or "",
        role=row["role"],
        view_mode=row["view_mode"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        device_id=row["device_id"] if "device_id" in row.keys() else "",
        device_label=row["device_label"] if "device_label" in row.keys() else "",
        slot_index=int(row["slot_index"]) if "slot_index" in row.keys() else 0,
        is_preview=bool(row["is_preview"]) if "is_preview" in row.keys() else False,
        source_type=row["source_type"] if "source_type" in row.keys() else "rtsp",
    )


@dataclass
class ConsentRecord:
    id: str
    poi_id: str
    user_id: str
    wallet_address: str
    consented_at: str
    consent_text_version: str
    has_embedding: bool


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self) -> None:
        require_data_key_in_prod()
        self.conn = connect()
        self.health_snapshots: Dict[str, List[dict]] = {}
        self.last_consent_id: Dict[str, str] = {}
        self._reload_last_consents()
        self._ensure_admin_user()
        if app_env() != "prod":
            try:
                self.ensure_demo_fixtures()
            except Exception:
                pass

    def _ensure_admin_user(self) -> None:
        import os

        pwd = os.environ.get("CMIR_ADMIN_PASSWORD", "").strip()
        if app_env() == "prod":
            if not pwd:
                raise RuntimeError("CMIR_ADMIN_PASSWORD is required in production")
        else:
            pwd = pwd or "admin"
        row = self.conn.execute("SELECT id FROM users WHERE email = ?", ("admin",)).fetchone()
        if row:
            self.conn.execute(
                "UPDATE users SET role = 'admin', password_hash = ? WHERE email = ?",
                (hash_password(pwd), "admin"),
            )
            self.conn.commit()
            self._ensure_wallet(row["id"])
            return
        uid = str(uuid.uuid4())
        t = now_iso()
        self.conn.execute(
            """
            INSERT INTO users (id, email, password_hash, display_name, role, blocked_until, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'admin', NULL, ?, ?)
            """,
            (uid, "admin", hash_password(pwd), "Administrator", t, t),
        )
        self.conn.commit()
        self._ensure_wallet(uid)

    def _camera_dict(self, row: sqlite3.Row) -> dict:
        d = row_to_dict(row) or {}
        d["is_active"] = bool(d.get("is_active", 0))
        d["is_preview"] = bool(d.get("is_preview", 0))
        return d

    def get_preview_camera(self, poi_id: str) -> Optional[dict]:
        row = self.conn.execute(
            """
            SELECT * FROM cameras
            WHERE poi_id = ? AND role = 'general' AND is_active = 1 AND is_preview = 1
            LIMIT 1
            """,
            (poi_id,),
        ).fetchone()
        if not row:
            row = self.conn.execute(
                """
                SELECT * FROM cameras
                WHERE poi_id = ? AND role = 'general' AND is_active = 1
                ORDER BY slot_index, created_at
                LIMIT 1
                """,
                (poi_id,),
            ).fetchone()
        return self._camera_dict(row) if row else None

    def _reload_last_consents(self) -> None:
        rows = self.conn.execute(
            """
            SELECT poi_id, id FROM consents
            WHERE revoked_at IS NULL
            ORDER BY consented_at ASC
            """
        ).fetchall()
        self.last_consent_id = {}
        for r in rows:
            self.last_consent_id[r["poi_id"]] = r["id"]

    # --- Auth ---

    def register_user(self, email: str, password: str, display_name: str = "") -> dict:
        email = email.strip().lower()
        if not email or "@" not in email:
            raise ValueError("invalid email")
        if len(password) < 8:
            raise ValueError("password must be at least 8 characters")
        uid = str(uuid.uuid4())
        t = now_iso()
        try:
            self.conn.execute(
                """
                INSERT INTO users (id, email, password_hash, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (uid, email, hash_password(password), display_name or email.split("@")[0], t, t),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("email already registered")
        self._ensure_wallet(uid)
        self.conn.commit()
        return self.user_public(self.get_user(uid))

    def login_user(self, email: str, password: str) -> dict:
        """Вход по email или телефону (киоск создаёт аккаунт вида +995…@kiosk.cmir.ge)."""
        ident = (email or "").strip()
        candidates = []
        if ident:
            candidates.append(ident.lower())
        if ident and ident.lower() != "admin":
            try:
                candidates.append(phone_to_email(ident).lower())
            except ValueError:
                pass
        row = None
        for cand in candidates:
            row = self.conn.execute("SELECT * FROM users WHERE email = ?", (cand,)).fetchone()
            if row:
                break
        if not row or not verify_password(password, row["password_hash"]):
            raise ValueError("invalid credentials")
        if is_blocked(row["blocked_until"]):
            raise ValueError("account blocked until " + (row["blocked_until"] or ""))
        token = new_session_token()
        t = now_iso()
        exp = session_expires()
        self.conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, row["id"], exp, t),
        )
        self.conn.commit()
        return {
            "token": token,
            "expires_at": exp,
            "user": self.user_public(row_to_dict(row)),
        }

    def logout_user(self, token: str) -> None:
        self.conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        self.conn.commit()

    def user_from_token(self, token: str) -> Optional[dict]:
        if not token:
            return None
        row = self.conn.execute(
            """
            SELECT u.*, s.expires_at AS session_expires
            FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
        if not row or not is_session_valid(row["session_expires"]):
            return None
        return row_to_dict(row)

    def get_user(self, user_id: str) -> Optional[dict]:
        return row_to_dict(self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    def user_public(self, user: Optional[dict]) -> dict:
        if not user:
            raise KeyError("user not found")
        wallet = self.conn.execute(
            "SELECT address, balance_st, balance_ut, created_at FROM wallets WHERE user_id = ?",
            (user["id"],),
        ).fetchone()
        consents = self.conn.execute(
            """
            SELECT id, poi_id, wallet_address, consented_at, consent_text_version,
                   CASE WHEN face_embedding IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
            FROM consents WHERE user_id = ? AND revoked_at IS NULL
            ORDER BY consented_at DESC
            """,
            (user["id"],),
        ).fetchall()
        return {
            "id": user["id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "role": user.get("role") or "user",
            "blocked_until": user.get("blocked_until"),
            "created_at": user["created_at"],
            "wallet": row_to_dict(wallet),
            "consents": [row_to_dict(c) for c in consents],
            "profile": self.get_user_profile(user["id"]),
        }

    def is_admin(self, user: dict) -> bool:
        return (user.get("role") or "user") == "admin"

    # --- Admin: users ---

    def list_users(self) -> List[dict]:
        rows = self.conn.execute(
            "SELECT id, email, display_name, role, blocked_until, created_at, updated_at FROM users ORDER BY created_at"
        ).fetchall()
        out = []
        for r in rows:
            d = row_to_dict(r)
            w = self.conn.execute(
                "SELECT address, balance_st, balance_ut FROM wallets WHERE user_id = ?", (d["id"],)
            ).fetchone()
            d["wallet"] = row_to_dict(w)
            out.append(d)
        return out

    def create_user_admin(self, body: dict) -> dict:
        email = body.get("email", "").strip().lower()
        password = body.get("password", "")
        display_name = body.get("display_name", "") or email.split("@")[0]
        role = body.get("role", "user")
        if role not in ("user", "admin"):
            raise ValueError("role must be user or admin")
        if email == "admin":
            raise ValueError("reserved email")
        if not email or ("@" not in email and role != "admin"):
            raise ValueError("invalid email")
        if len(password) < 8:
            raise ValueError("password must be at least 8 characters")
        uid = str(uuid.uuid4())
        t = now_iso()
        try:
            self.conn.execute(
                """
                INSERT INTO users (id, email, password_hash, display_name, role, blocked_until, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (uid, email, hash_password(password), display_name, role, t, t),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("email already registered")
        return row_to_dict(self.get_user(uid))

    def update_user_admin(self, user_id: str, body: dict) -> dict:
        row = self.get_user(user_id)
        if not row:
            raise KeyError("user not found")
        fields, vals = [], []
        if "email" in body:
            email = body["email"].strip().lower()
            if email == "admin" and row["email"] != "admin":
                raise ValueError("reserved email")
            fields.append("email = ?")
            vals.append(email)
        if "display_name" in body:
            fields.append("display_name = ?")
            vals.append(body["display_name"])
        if "password" in body and body["password"]:
            if len(body["password"]) < 8:
                raise ValueError("password must be at least 8 characters")
            fields.append("password_hash = ?")
            vals.append(hash_password(body["password"]))
        if "role" in body:
            if body["role"] not in ("user", "admin"):
                raise ValueError("role must be user or admin")
            if row["email"] == "admin" and body["role"] != "admin":
                raise ValueError("cannot demote default admin")
            fields.append("role = ?")
            vals.append(body["role"])
        if not fields:
            return row_to_dict(row)
        fields.append("updated_at = ?")
        vals.append(now_iso())
        vals.append(user_id)
        self.conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", vals)
        self.conn.commit()
        return row_to_dict(self.get_user(user_id))

    def delete_user(self, user_id: str) -> None:
        row = self.get_user(user_id)
        if not row:
            raise KeyError("user not found")
        if row["email"] == "admin":
            raise ValueError("cannot delete default admin")
        self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

    def block_user(self, user_id: str, until: str) -> dict:
        row = self.get_user(user_id)
        if not row:
            raise KeyError("user not found")
        if row["email"] == "admin":
            raise ValueError("cannot block admin")
        self.conn.execute(
            "UPDATE users SET blocked_until = ?, updated_at = ? WHERE id = ?",
            (until, now_iso(), user_id),
        )
        self.conn.commit()
        return row_to_dict(self.get_user(user_id))

    def unblock_user(self, user_id: str) -> dict:
        row = self.get_user(user_id)
        if not row:
            raise KeyError("user not found")
        self.conn.execute(
            "UPDATE users SET blocked_until = NULL, updated_at = ? WHERE id = ?",
            (now_iso(), user_id),
        )
        self.conn.commit()
        return row_to_dict(self.get_user(user_id))

    # --- POI / cameras ---

    def poi_payload(self, poi_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM pois WHERE id = ?", (poi_id,)).fetchone()
        if not row:
            raise KeyError("poi not found")
        p = row_to_dict(row)
        cams = [
            self._camera_dict(c)
            for c in self.conn.execute(
                "SELECT * FROM cameras WHERE poi_id = ? ORDER BY slot_index, created_at",
                (poi_id,),
            ).fetchall()
        ]
        rate = float(p["consent_rate"])
        return {
            **{k: p[k] for k in (
                "id", "name", "description", "poi_type", "latitude", "longitude",
                "promo_description", "city", "country", "created_at", "updated_at",
            )},
            "address": p.get("address") or "",
            "comment": p.get("comment") or "",
            "mask_image_url": f"/api/v1/pois/{poi_id}/mask-image" if p.get("mask_image") else None,
            "cameras": cams,
            "stats": {
                "poi_id": poi_id,
                "consent_rate_percent": rate,
                "participant_count_24h": int(p["participants_24h"]),
                "avatar_faces_ratio": 1.0 - rate / 100.0,
            },
        }

    def list_pois(self) -> List[dict]:
        self._maybe_restore_demo_fixtures()
        ids = [r["id"] for r in self.conn.execute("SELECT id FROM pois ORDER BY created_at").fetchall()]
        return [self.poi_payload(pid) for pid in ids]

    def _maybe_restore_demo_fixtures(self) -> None:
        """В test-среде восстанавливает демо-места, если карта пуста или нет эталонных POI."""
        if app_env() == "prod":
            return
        count = int(self.conn.execute("SELECT COUNT(*) AS c FROM pois").fetchone()["c"])
        missing_demo = any(not self._poi_id_by_name(name) for name in DEMO_POI_NAMES)
        if count == 0 or missing_demo:
            try:
                self.ensure_demo_fixtures()
            except Exception:
                pass

    def create_poi(self, body: dict) -> Poi:
        poi_id = str(uuid.uuid4())
        t = now_iso()
        self.conn.execute(
            """
            INSERT INTO pois (id, name, description, poi_type, latitude, longitude,
                promo_description, city, country, address, comment, consent_rate, participants_24h, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (
                poi_id,
                body["name"],
                body.get("description", body.get("comment", "")),
                body.get("poi_type", "live_cam"),
                float(body["latitude"]),
                float(body["longitude"]),
                body.get("promo_description", ""),
                body.get("city", ""),
                body.get("country", ""),
                body.get("address", ""),
                body.get("comment", body.get("description", "")),
                t,
                t,
            ),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM pois WHERE id = ?", (poi_id,)).fetchone()
        return Poi(**{k: row[k] for k in (
            "id", "name", "description", "poi_type", "latitude", "longitude",
            "promo_description", "city", "country", "created_at", "updated_at",
        )})

    def validate_cameras(self, poi_id: str) -> Optional[str]:
        pt = PoiType(self.conn.execute("SELECT poi_type FROM pois WHERE id = ?", (poi_id,)).fetchone()["poi_type"])
        cams = self.conn.execute("SELECT role FROM cameras WHERE poi_id = ?", (poi_id,)).fetchall()
        if len(cams) < pt.min_cameras():
            return f"requires at least {pt.min_cameras()} cameras"
        consent = sum(1 for c in cams if c["role"] == "consent")
        if consent < pt.min_consent_cameras():
            return f"requires at least {pt.min_consent_cameras()} consent cameras"
        perf = sum(1 for c in cams if c["role"] == "performance")
        if perf < pt.min_performance_cameras():
            return f"requires at least {pt.min_performance_cameras()} performance cameras"
        return None

    def add_camera(self, poi_id: str, body: dict) -> Camera:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        cid = str(uuid.uuid4())
        t = now_iso()
        is_active = 1 if body.get("is_active", True) else 0
        is_preview = 1 if body.get("is_preview") else 0
        if is_preview:
            self.conn.execute(
                "UPDATE cameras SET is_preview = 0 WHERE poi_id = ? AND role = 'general'",
                (poi_id,),
            )
        self.conn.execute(
            """
            INSERT INTO cameras (id, poi_id, name, stream_url, role, view_mode, is_active,
                device_id, slot_index, is_preview, source_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                poi_id,
                body["name"],
                body.get("stream_url", ""),
                body.get("role", "general"),
                body.get("view_mode", "standard"),
                is_active,
                body.get("device_id", ""),
                int(body.get("slot_index", 0)),
                is_preview,
                body.get("source_type", "rtsp"),
                t,
            ),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM cameras WHERE id = ?", (cid,)).fetchone()
        return _row_to_camera(row)

    def update_poi(self, poi_id: str, body: dict) -> Poi:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        fields = []
        vals: list[Any] = []
        for key in ("name", "description", "promo_description", "city", "country", "address", "comment"):
            if key in body:
                fields.append(f"{key} = ?")
                vals.append(body[key])
        if "latitude" in body:
            fields.append("latitude = ?")
            vals.append(float(body["latitude"]))
        if "longitude" in body:
            fields.append("longitude = ?")
            vals.append(float(body["longitude"]))
        fields.append("updated_at = ?")
        vals.append(now_iso())
        vals.append(poi_id)
        self.conn.execute(f"UPDATE pois SET {', '.join(fields)} WHERE id = ?", vals)
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM pois WHERE id = ?", (poi_id,)).fetchone()
        return Poi(**{k: row[k] for k in (
            "id", "name", "description", "poi_type", "latitude", "longitude",
            "promo_description", "city", "country", "created_at", "updated_at",
        )})

    def update_camera(self, camera_id: str, body: dict) -> Camera:
        row = self.conn.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        if not row:
            raise KeyError("camera not found")
        fields, vals = [], []
        for key in ("name", "stream_url", "role", "view_mode", "device_id", "source_type"):
            if key in body:
                if key == "role" and body["role"] not in CAMERA_ROLES:
                    raise ValueError(f"role must be one of {sorted(CAMERA_ROLES)}")
                if key == "view_mode" and body["view_mode"] not in VIEW_MODES:
                    raise ValueError(f"view_mode must be one of {sorted(VIEW_MODES)}")
                fields.append(f"{key} = ?")
                vals.append(body[key])
        if "slot_index" in body:
            fields.append("slot_index = ?")
            vals.append(int(body["slot_index"]))
        if "is_active" in body:
            fields.append("is_active = ?")
            vals.append(1 if body["is_active"] else 0)
        if body.get("is_preview"):
            self.conn.execute(
                "UPDATE cameras SET is_preview = 0 WHERE poi_id = ? AND role = 'general'",
                (row["poi_id"],),
            )
            fields.append("is_preview = ?")
            vals.append(1)
        elif "is_preview" in body:
            fields.append("is_preview = ?")
            vals.append(0)
        if fields:
            vals.append(camera_id)
            self.conn.execute(f"UPDATE cameras SET {', '.join(fields)} WHERE id = ?", vals)
            self.conn.commit()
        row = self.conn.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        return _row_to_camera(row)

    def delete_camera(self, camera_id: str) -> str:
        row = self.conn.execute("SELECT poi_id FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        if not row:
            raise KeyError("camera not found")
        self.conn.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
        self.conn.commit()
        return row["poi_id"]

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        row = self.conn.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        if not row:
            return None
        return _row_to_camera(row)

    def sync_poi_cameras(self, poi_id: str, cameras: List[dict]) -> List[dict]:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        if len(cameras) > 5:
            raise ValueError("max 5 cameras per poi")
        self.conn.execute("DELETE FROM cameras WHERE poi_id = ?", (poi_id,))
        t = now_iso()
        preview_marked = False
        for i, cam in enumerate(cameras):
            role = cam.get("role", "general")
            if role not in CAMERA_ROLES:
                raise ValueError(f"role must be one of {sorted(CAMERA_ROLES)}")
            cid = str(uuid.uuid4())
            is_preview = bool(cam.get("is_preview")) and not preview_marked and role == "general"
            if is_preview:
                preview_marked = True
            device_id = cam.get("device_id", "")
            device_label = cam.get("device_label", "")
            source_type = cam.get("source_type", "local_usb" if device_id else "rtsp")
            if device_id and is_preview:
                stream_url = poi_rtmp_url(poi_id)
            elif device_id:
                stream_url = cam.get("stream_url") or f"local://{device_id}"
            else:
                stream_url = cam.get("stream_url") or ""
            self.conn.execute(
                """
                INSERT INTO cameras (id, poi_id, name, stream_url, role, view_mode, is_active,
                    device_id, device_label, slot_index, is_preview, source_type, created_at)
                VALUES (?, ?, ?, ?, ?, 'standard', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    poi_id,
                    cam.get("name") or f"Камера {i + 1}",
                    stream_url,
                    role,
                    1 if cam.get("is_active", True) else 0,
                    device_id,
                    device_label,
                    int(cam.get("slot_index", i)),
                    1 if is_preview else 0,
                    source_type,
                    t,
                ),
            )
        self.conn.commit()
        rows = self.conn.execute(
            "SELECT * FROM cameras WHERE poi_id = ? ORDER BY slot_index, role",
            (poi_id,),
        ).fetchall()
        return [self._camera_dict(r) for r in rows]

    def network_quality(self) -> dict:
        from camera_health import probe_stream_url

        rows = self.conn.execute("SELECT * FROM cameras WHERE is_active = 1").fetchall()
        items = []
        for row in rows:
            cam = self._camera_dict(row)
            probe = probe_stream_url(cam["stream_url"])
            items.append({**cam, **probe})
        scores = [int(x.get("quality_score", 0)) for x in items]
        aggregate = round(sum(scores) / len(scores), 1) if scores else 0.0
        if aggregate >= 85:
            grade = "excellent"
        elif aggregate >= 65:
            grade = "good"
        elif aggregate >= 40:
            grade = "fair"
        else:
            grade = "poor"
        return {
            "environment": app_env(),
            "cameras": items,
            "aggregate_score": aggregate,
            "grade": grade,
            "camera_count": len(items),
        }

    def _period_key(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")

    def record_view(
        self, user_id: str, camera_id: str, seconds: float, ad_revenue: float = 0.01
    ) -> dict:
        user = self.get_user(user_id)
        if not user:
            raise KeyError("user not found")
        if self.is_admin(user):
            wallet = self._ensure_wallet(user_id)
            return {
                "recorded": False,
                "reason": "admin views excluded",
                "wallet_address": wallet,
            }
        cam = self.get_camera(camera_id)
        if not cam or not cam.is_active:
            raise KeyError("camera not found")
        wallet = self._ensure_wallet(user_id)
        period = self._period_key()
        unique_before = self.conn.execute(
            "SELECT COUNT(DISTINCT user_id) AS c FROM view_events WHERE period_key = ?",
            (period,),
        ).fetchone()["c"]
        seen = self.conn.execute(
            "SELECT 1 FROM view_events WHERE period_key = ? AND user_id = ? LIMIT 1",
            (period, user_id),
        ).fetchone()
        unique = unique_before if seen else unique_before + 1
        ut = round((float(ad_revenue) / 2.0) * (1.0 / max(unique, 1)), 6)
        t = now_iso()
        self.conn.execute(
            """
            INSERT INTO view_events (user_id, camera_id, poi_id, seconds, ad_revenue, period_key, ut_earned, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, camera_id, cam.poi_id, seconds, ad_revenue, period, ut, t),
        )
        self.conn.execute(
            "UPDATE wallets SET balance_ut = ROUND(balance_ut + ?, 4) WHERE user_id = ?",
            (ut, user_id),
        )
        self.conn.commit()
        return {
            "recorded": True,
            "ut_earned": ut,
            "unique_viewers_in_period": unique,
            "wallet_address": wallet,
            "period_key": period,
        }

    def clear_all_pois(self) -> int:
        """Test env cleanup — remove all POI (and cascaded cameras)."""
        if app_env() == "prod":
            raise ValueError("refusing to clear POIs in production")
        n = self.conn.execute("SELECT COUNT(*) AS c FROM pois").fetchone()["c"]
        self.conn.execute("DELETE FROM pois")
        self.conn.commit()
        deleted = int(n)
        if app_env() != "prod":
            try:
                self.ensure_demo_fixtures()
            except Exception:
                pass
        return deleted

    def ensure_demo_fixtures(self) -> List[str]:
        """Идемпотентно восстанавливает демо-места для test-среды (карта, киоск, перфоманс)."""
        if app_env() == "prod":
            return []
        created: List[str] = []
        created.extend(self._ensure_demo_social_event())
        created.extend(self._ensure_demo_test_place())
        return created

    def _poi_id_by_name(self, name: str) -> Optional[str]:
        row = self.conn.execute("SELECT id FROM pois WHERE name = ?", (name,)).fetchone()
        return row["id"] if row else None

    def _camera_exists(self, poi_id: str, role: str, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM cameras WHERE poi_id = ? AND role = ? AND name = ?",
            (poi_id, role, name),
        ).fetchone()
        return row is not None

    def _ensure_demo_social_event(self) -> List[str]:
        name = "Demo: Social Event — Пингвинья вечеринка"
        poi_id = self._poi_id_by_name(name)
        created: List[str] = []
        if not poi_id:
            poi = self.create_poi(
                {
                    "name": name,
                    "description": "Тестовая точка для Фазы 0",
                    "comment": "Демо: общий план, согласие, перфоманс",
                    "poi_type": "venue",
                    "latitude": 41.7151,
                    "longitude": 44.8271,
                    "promo_description": "Лучшее место в городе для live-трансляций.",
                    "address": "Тбилиси, проспект Руставели 1",
                    "city": "Tbilisi",
                    "country": "GE",
                }
            )
            poi_id = str(poi.id)
            created.append(name)
            self.conn.execute(
                "UPDATE pois SET consent_rate = 42, participants_24h = 17 WHERE id = ?",
                (poi_id,),
            )
            self.conn.commit()
        specs = [
            ("General A", "general", "fisheye", "rtsp://127.0.0.1:8554/gopro_main", True, 0),
            ("General B", "general", "zoom2x", "rtsp://127.0.0.1:8554/demo_general_b", False, 1),
            ("Consent kiosk", "consent", "standard", "rtsp://127.0.0.1:8554/demo_consent", False, 2),
            ("Performance table", "performance", "standard", "rtsp://127.0.0.1:8554/demo_performance", False, 3),
        ]
        for cam_name, role, mode, url, is_preview, slot in specs:
            if self._camera_exists(poi_id, role, cam_name):
                continue
            self.add_camera(
                poi_id,
                {
                    "name": cam_name,
                    "stream_url": url,
                    "role": role,
                    "view_mode": mode,
                    "slot_index": slot,
                    "is_preview": is_preview,
                    "is_active": True,
                    "source_type": "rtsp",
                },
            )
            created.append(f"{name} / {cam_name}")
        return created

    def _ensure_demo_test_place(self) -> List[str]:
        name = "Тестовое место"
        poi_id = self._poi_id_by_name(name)
        created: List[str] = []
        if not poi_id:
            poi = self.create_poi(
                {
                    "name": name,
                    "address": "Тбилиси, Руставели 1",
                    "comment": "Демо для админ-панели",
                    "poi_type": "live_cam",
                    "latitude": 41.7089,
                    "longitude": 44.7989,
                    "city": "Tbilisi",
                    "country": "GE",
                }
            )
            poi_id = str(poi.id)
            created.append(name)
        if not self._camera_exists(poi_id, "general", "Камера 1"):
            self.add_camera(
                poi_id,
                {
                    "name": "Камера 1",
                    "stream_url": "rtsp://127.0.0.1:8554/gopro_main",
                    "role": "general",
                    "view_mode": "standard",
                    "slot_index": 0,
                    "is_preview": True,
                    "is_active": True,
                    "source_type": "rtsp",
                },
            )
            created.append(f"{name} / Камера 1")
        return created

    # --- Consent + wallet (linked to user) ---

    def _ensure_wallet(self, user_id: str) -> str:
        row = self.conn.execute("SELECT address FROM wallets WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return row["address"]
        addr = f"0xcmir{uuid.uuid4().hex}"
        t = now_iso()
        self.conn.execute(
            "INSERT INTO wallets (address, user_id, balance_st, balance_ut, created_at) VALUES (?, ?, 0, 100, ?)",
            (addr, user_id, t),
        )
        return addr

    def delete_poi(self, poi_id: str) -> None:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        self.delete_mask_image(poi_id)
        self.conn.execute("DELETE FROM pois WHERE id = ?", (poi_id,))
        self.conn.commit()

    def save_mask_image(self, poi_id: str, data: bytes, ext: str = "png") -> str:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        self.delete_mask_image(poi_id, keep_db=False)
        fname = f"{poi_id}.{ext}"
        path = masks_dir() / fname
        path.write_bytes(data)
        self.conn.execute(
            "UPDATE pois SET mask_image = ?, updated_at = ? WHERE id = ?",
            (fname, now_iso(), poi_id),
        )
        self.conn.commit()
        return fname

    def get_mask_image_path(self, poi_id: str) -> Optional[Path]:
        row = self.conn.execute("SELECT mask_image FROM pois WHERE id = ?", (poi_id,)).fetchone()
        if not row or not row["mask_image"]:
            return None
        path = masks_dir() / row["mask_image"]
        return path if path.is_file() else None

    def delete_mask_image(self, poi_id: str, keep_db: bool = True) -> None:
        path = self.get_mask_image_path(poi_id)
        if path:
            path.unlink(missing_ok=True)
        if keep_db:
            self.conn.execute(
                "UPDATE pois SET mask_image = NULL, updated_at = ? WHERE id = ?",
                (now_iso(), poi_id),
            )
            self.conn.commit()

    def grant_consent(
        self,
        poi_id: str,
        user_id: str,
        embedding: Optional[List[float]] = None,
        embeddings: Optional[List[Any]] = None,
        *,
        require_multi: bool = False,
    ) -> dict:
        user = self.get_user(user_id)
        if user and is_blocked(user.get("blocked_until")):
            raise ValueError("account blocked")
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        templates = normalize_face_templates(
            embedding, embeddings, require_multi=require_multi
        )
        wallet = self._ensure_wallet(user_id)
        cid = str(uuid.uuid4())
        t = now_iso()
        primary = templates[0]["embedding"]
        emb_json = encrypt_embedding(primary)
        self.conn.execute(
            """
            INSERT INTO consents (id, user_id, poi_id, wallet_address, face_embedding,
                consent_text_version, consented_at, revoked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (cid, user_id, poi_id, wallet, emb_json, LEGAL_VERSION, t),
        )
        self.conn.execute(
            "INSERT INTO poi_embeddings (poi_id, consent_id, embedding_json) VALUES (?, ?, ?)",
            (poi_id, cid, emb_json),
        )
        for tpl in templates:
            self.conn.execute(
                """
                INSERT INTO face_templates
                    (id, user_id, consent_id, poi_id, pose, yaw, pitch, embedding_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    user_id,
                    cid,
                    poi_id,
                    tpl["pose"],
                    tpl.get("yaw"),
                    tpl.get("pitch"),
                    encrypt_embedding(tpl["embedding"]),
                    t,
                ),
            )
        row = self.conn.execute("SELECT consent_rate, participants_24h FROM pois WHERE id = ?", (poi_id,)).fetchone()
        rate = min(100.0, float(row["consent_rate"]) + 5.0)
        parts = int(row["participants_24h"]) + 1
        self.conn.execute(
            "UPDATE pois SET consent_rate = ?, participants_24h = ?, updated_at = ? WHERE id = ?",
            (rate, parts, t, poi_id),
        )
        self.conn.commit()
        self.last_consent_id[poi_id] = cid
        return {
            "id": cid,
            "poi_id": poi_id,
            "user_id": user_id,
            "wallet_address": wallet,
            "consented_at": t,
            "consent_text_version": LEGAL_VERSION,
            "has_embedding": True,
            "template_count": len(templates),
            "poses": [t["pose"] for t in templates],
        }

    def poi_menu_items(self, poi_id: str) -> List[str]:
        row = self.conn.execute("SELECT menu_items_json FROM pois WHERE id = ?", (poi_id,)).fetchone()
        if not row:
            raise KeyError("poi not found")
        try:
            items = json.loads(row["menu_items_json"] or "[]")
        except json.JSONDecodeError:
            items = []
        if not items:
            items = ["Бургер", "Пицца", "Коктейль", "Салат", "Десерт", "Кофе"]
        return items

    def kiosk_register(
        self,
        poi_id: str,
        full_name: str,
        phone: str,
        favorite_menu_item: str,
        embedding: Optional[List[float]],
        acceptances: dict,
        client_meta: Optional[dict] = None,
        embeddings: Optional[List[Any]] = None,
        *,
        require_multi: bool = False,
    ) -> dict:
        validate_acceptances(acceptances)
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        if not (full_name or "").strip():
            raise ValueError("full_name required")
        if not (favorite_menu_item or "").strip():
            raise ValueError("favorite_menu_item required")
        # Валидация поз до создания пользователя
        normalize_face_templates(embedding, embeddings, require_multi=require_multi)

        ensure_legal_documents(self.conn)
        docs = {d["doc_type"]: d for d in list_legal_documents(self.conn)}
        phone_norm = normalize_phone(phone)
        email = phone_to_email(phone_norm)
        t = now_iso()

        row = self.conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        temporary_password: Optional[str] = None
        if row:
            user_id = row["id"]
            self.conn.execute(
                "UPDATE users SET display_name = ?, updated_at = ? WHERE id = ?",
                (full_name.strip(), t, user_id),
            )
        else:
            user_id = str(uuid.uuid4())
            temporary_password = secrets.token_urlsafe(12)
            self.conn.execute(
                """
                INSERT INTO users (id, email, password_hash, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, email, hash_password(temporary_password), full_name.strip(), t, t),
            )
            self._ensure_wallet(user_id)

        prof = self.conn.execute("SELECT 1 FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        if prof:
            self.conn.execute(
                """
                UPDATE user_profiles SET full_name = ?, phone = ?, favorite_menu_item = ?,
                    registered_via = 'kiosk', updated_at = ? WHERE user_id = ?
                """,
                (full_name.strip(), phone_norm, favorite_menu_item.strip(), t, user_id),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO user_profiles (user_id, full_name, phone, favorite_menu_item, registered_via, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'kiosk', ?, ?)
                """,
                (user_id, full_name.strip(), phone_norm, favorite_menu_item.strip(), t, t),
            )

        consent = self.grant_consent(
            poi_id,
            user_id,
            embedding,
            embeddings,
            require_multi=require_multi,
        )
        for doc_type in acceptances:
            if doc_type not in docs:
                continue
            doc = docs[doc_type]
            self.conn.execute(
                """
                INSERT INTO consent_document_acceptances
                    (id, consent_id, doc_type, doc_version, content_hash, accepted_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    consent["id"],
                    doc_type,
                    doc["version"],
                    doc["content_hash"],
                    t,
                ),
            )

        chain = blockchain_record(
            self.conn,
            user_id,
            {
                "event": "user_registered",
                "poi_id": poi_id,
                "consent_id": consent["id"],
                "legal_version": LEGAL_VERSION,
                "phone_hash": hashlib.sha256(phone_norm.encode()).hexdigest(),
            },
        )
        audit_log(
            self.conn,
            "kiosk_register",
            user_id=user_id,
            poi_id=poi_id,
            details={"consent_id": consent["id"], "client": client_meta or {}},
        )
        self.conn.commit()
        wallet = self.conn.execute(
            "SELECT address, balance_st, balance_ut FROM wallets WHERE user_id = ?", (user_id,)
        ).fetchone()
        token = new_session_token()
        exp = session_expires()
        self.conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, user_id, exp, t),
        )
        self.conn.commit()
        out = {
            "user_id": user_id,
            "display_name": full_name.strip(),
            "phone": phone_norm,
            "login_email": email,
            "favorite_menu_item": favorite_menu_item.strip(),
            "consent": consent,
            "wallet": row_to_dict(wallet),
            "blockchain": chain,
            "auth": {"token": token, "expires_at": exp},
            "account_url": "/index.html#account",
            "message": "Регистрация завершена. Маска будет снята при распознавании лица на камерах.",
        }
        if temporary_password:
            out["temporary_password"] = temporary_password
            out["message"] += (
                f" Сохраните вход: телефон {phone_norm} (или {email})"
                f" и пароль {temporary_password}."
            )
        return out

    def revoke_consent(self, poi_id: str, consent_id: str, user_id: Optional[str] = None) -> dict:
        if consent_id == "latest":
            consent_id = self.last_consent_id.get(poi_id, "")
        q = "SELECT * FROM consents WHERE poi_id = ? AND id = ? AND revoked_at IS NULL"
        params: list[Any] = [poi_id, consent_id]
        if user_id:
            q += " AND user_id = ?"
            params.append(user_id)
        row = self.conn.execute(q, params).fetchone()
        if not row:
            raise KeyError("consent not found")
        t = now_iso()
        self.conn.execute(
            "UPDATE consents SET revoked_at = ?, face_embedding = NULL WHERE id = ?",
            (t, consent_id),
        )
        self.conn.execute(
            "DELETE FROM poi_embeddings WHERE poi_id = ? AND consent_id = ?",
            (poi_id, consent_id),
        )
        self.conn.execute("DELETE FROM face_templates WHERE consent_id = ?", (consent_id,))
        remaining = self.conn.execute(
            "SELECT COUNT(*) AS c FROM poi_embeddings WHERE poi_id = ?", (poi_id,)
        ).fetchone()["c"]
        prow = self.conn.execute("SELECT consent_rate FROM pois WHERE id = ?", (poi_id,)).fetchone()
        rate = max(0.0, float(prow["consent_rate"]) - 5.0)
        self.conn.execute("UPDATE pois SET consent_rate = ?, updated_at = ? WHERE id = ?", (rate, t, poi_id))
        self.conn.commit()
        return {"poi_id": poi_id, "consent_id": consent_id, "embeddings_remaining": remaining}

    def poi_embeddings(self, poi_id: str) -> List[List[float]]:
        rows = self.conn.execute(
            """
            SELECT e.embedding_json FROM face_templates e
            JOIN consents c ON c.id = e.consent_id
            WHERE e.poi_id = ? AND c.revoked_at IS NULL
            """,
            (poi_id,),
        ).fetchall()
        out = []
        for r in rows:
            emb = decrypt_embedding(r["embedding_json"] or "")
            if emb and len(emb) == PATCH_DIM:
                out.append(emb)
        if out:
            return out
        rows = self.conn.execute(
            """
            SELECT e.embedding_json FROM poi_embeddings e
            JOIN consents c ON c.id = e.consent_id
            WHERE e.poi_id = ? AND c.revoked_at IS NULL
            """,
            (poi_id,),
        ).fetchall()
        for r in rows:
            emb = decrypt_embedding(r["embedding_json"] or "")
            if emb and len(emb) == PATCH_DIM:
                out.append(emb)
        return out

    def global_consented_faces(self) -> List[dict]:
        """Один пользователь → все pose-шаблоны для устойчивого матчинга на потоке."""
        rows = self.conn.execute(
            """
            SELECT u.id AS user_id,
                   COALESCE(NULLIF(p.full_name, ''), u.display_name) AS display_name,
                   t.pose,
                   t.yaw,
                   t.pitch,
                   t.embedding_json
            FROM face_templates t
            JOIN consents c ON c.id = t.consent_id
            JOIN users u ON u.id = c.user_id
            LEFT JOIN user_profiles p ON p.user_id = u.id
            WHERE c.revoked_at IS NULL
            ORDER BY u.id, t.created_at
            """
        ).fetchall()
        by_user: Dict[str, dict] = {}
        for r in rows:
            uid = r["user_id"]
            emb = decrypt_embedding(r["embedding_json"] or "")
            if not emb or len(emb) != PATCH_DIM:
                continue
            entry = by_user.setdefault(
                uid,
                {
                    "user_id": uid,
                    "display_name": r["display_name"] or "",
                    "embedding": emb,
                    "embeddings": [],
                    "templates": [],
                },
            )
            entry["embeddings"].append(emb)
            entry["templates"].append(
                {
                    "pose": r["pose"],
                    "yaw": r["yaw"],
                    "pitch": r["pitch"],
                    "embedding": emb,
                }
            )

        legacy = self.conn.execute(
            """
            SELECT u.id AS user_id,
                   COALESCE(NULLIF(p.full_name, ''), u.display_name) AS display_name,
                   e.embedding_json
            FROM poi_embeddings e
            JOIN consents c ON c.id = e.consent_id
            JOIN users u ON u.id = c.user_id
            LEFT JOIN user_profiles p ON p.user_id = u.id
            WHERE c.revoked_at IS NULL
            """
        ).fetchall()
        for r in legacy:
            uid = r["user_id"]
            if uid in by_user:
                continue
            emb = decrypt_embedding(r["embedding_json"] or "")
            if not emb or len(emb) != PATCH_DIM:
                continue
            by_user[uid] = {
                "user_id": uid,
                "display_name": r["display_name"] or "",
                "embedding": emb,
                "embeddings": [emb],
                "templates": [{"pose": "center", "embedding": emb}],
            }

        return list(by_user.values())

    def match_face_embedding(
        self,
        embedding: List[float],
        *,
        threshold: float = 0.82,
        hold_threshold: float = 0.75,
        prior_user_id: str = "",
    ) -> Optional[dict]:
        """Server-side match — returns identity without exposing gallery vectors."""
        if not embedding or len(embedding) != PATCH_DIM:
            return None

        def _norm(v: List[float]) -> List[float]:
            n = sum(x * x for x in v) ** 0.5
            if n < 1e-9:
                return v
            return [x / n for x in v]

        def _cosine(a: List[float], b: List[float]) -> float:
            if len(a) != len(b):
                return 0.0
            return float(sum(x * y for x, y in zip(a, b)))

        query = _norm(embedding)
        faces = self.global_consented_faces()
        best: Optional[dict] = None
        best_score = hold_threshold if prior_user_id else threshold
        for face in faces:
            thr = hold_threshold if prior_user_id and face["user_id"] == prior_user_id else threshold
            score = 0.0
            for emb in face.get("embeddings") or []:
                score = max(score, _cosine(query, _norm(emb)))
            if not face.get("embeddings") and face.get("embedding"):
                score = _cosine(query, _norm(face["embedding"]))
            if score >= thr and score >= best_score:
                best_score = score
                best = {
                    "matched": True,
                    "user_id": face["user_id"],
                    "display_name": face.get("display_name") or "",
                    "score": round(score, 4),
                }
        return best

    def filter_poi_ids(self, city: Optional[str], country: Optional[str]) -> List[str]:
        q = "SELECT id, city, country FROM pois"
        out = []
        for r in self.conn.execute(q).fetchall():
            if city and (r["city"] or "").lower() != city.lower():
                continue
            if country and (r["country"] or "").upper() != country.upper():
                continue
            out.append(r["id"])
        return out

    def sorted_tops(self, key: str, city: Optional[str], country: Optional[str]) -> List[dict]:
        ids = self.filter_poi_ids(city, country)
        items = [self.poi_payload(pid) for pid in ids]
        if key == "consent":
            items.sort(key=lambda x: x["stats"]["consent_rate_percent"], reverse=True)
        else:
            items.sort(key=lambda x: x["stats"]["participant_count_24h"], reverse=True)
        return items

    def get_wallet(self, address: str) -> Optional[dict]:
        row = self.conn.execute(
            """
            SELECT w.*, u.email, u.display_name
            FROM wallets w JOIN users u ON u.id = w.user_id
            WHERE w.address = ?
            """,
            (address,),
        ).fetchone()
        if not row:
            return None
        d = row_to_dict(row)
        return {
            "address": d["address"],
            "user_id": d["user_id"],
            "email": d["email"],
            "display_name": d["display_name"],
            "balance_st": d["balance_st"],
            "balance_ut": d["balance_ut"],
            "created_at": d["created_at"],
        }

    def add_airtime(self, poi_id: str, wallet: str, seconds: float) -> dict:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        t = now_iso()
        self.conn.execute(
            "INSERT INTO airtime (poi_id, wallet_address, seconds, recorded_at) VALUES (?, ?, ?, ?)",
            (poi_id, wallet, seconds, t),
        )
        w = self.conn.execute("SELECT balance_st, balance_ut FROM wallets WHERE address = ?", (wallet,)).fetchone()
        if w:
            st = round(float(w["balance_st"]) + seconds * 0.01, 4)
            ut = round(float(w["balance_ut"]) + seconds * 0.05, 2)
            self.conn.execute(
                "UPDATE wallets SET balance_st = ?, balance_ut = ? WHERE address = ?",
                (st, ut, wallet),
            )
        self.conn.commit()
        return {"wallet": wallet, "seconds": seconds, "at": t}

    def record_face_presence(
        self, user_id: str, camera_id: str, seconds: float, period_key: Optional[str] = None
    ) -> dict:
        """Накопить секунды присутствия зарегистрированного лица на камере (период = час UTC)."""
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        user = self.get_user(user_id)
        if not user:
            raise KeyError("user not found")
        if self.is_admin(user):
            return {"recorded": False, "reason": "admin excluded"}
        cam = self.get_camera(camera_id)
        if not cam or not cam.is_active:
            raise KeyError("camera not found")
        # Только пользователи с активным согласием
        consent = self.conn.execute(
            "SELECT 1 FROM consents WHERE user_id = ? AND revoked_at IS NULL LIMIT 1",
            (user_id,),
        ).fetchone()
        if not consent:
            raise ValueError("active consent required")
        period = period_key or self._period_key()
        t = now_iso()
        existing = self.conn.execute(
            """
            SELECT id, seconds FROM face_presence
            WHERE user_id = ? AND camera_id = ? AND period_key = ?
            """,
            (user_id, camera_id, period),
        ).fetchone()
        if existing:
            new_sec = float(existing["seconds"]) + float(seconds)
            self.conn.execute(
                "UPDATE face_presence SET seconds = ?, updated_at = ? WHERE id = ?",
                (new_sec, t, existing["id"]),
            )
        else:
            new_sec = float(seconds)
            self.conn.execute(
                """
                INSERT INTO face_presence (user_id, camera_id, poi_id, period_key, seconds, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, camera_id, cam.poi_id, period, new_sec, t),
            )
        self.conn.execute(
            """
            INSERT INTO face_presence_events (user_id, camera_id, poi_id, seconds, recorded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, camera_id, cam.poi_id, float(seconds), t),
        )
        self.conn.commit()
        return {
            "recorded": True,
            "user_id": user_id,
            "camera_id": camera_id,
            "poi_id": cam.poi_id,
            "period_key": period,
            "seconds_total": new_sec,
            "seconds_added": float(seconds),
        }

    def list_face_presence(
        self,
        user_id: Optional[str] = None,
        camera_id: Optional[str] = None,
        period_key: Optional[str] = None,
    ) -> List[dict]:
        q = """
            SELECT fp.*, u.display_name, c.name AS camera_name
            FROM face_presence fp
            JOIN users u ON u.id = fp.user_id
            LEFT JOIN cameras c ON c.id = fp.camera_id
            WHERE 1=1
        """
        params: list[Any] = []
        if user_id:
            q += " AND fp.user_id = ?"
            params.append(user_id)
        if camera_id:
            q += " AND fp.camera_id = ?"
            params.append(camera_id)
        if period_key:
            q += " AND fp.period_key = ?"
            params.append(period_key)
        q += " ORDER BY fp.updated_at DESC"
        return [row_to_dict(r) for r in self.conn.execute(q, params).fetchall()]

    def distribute_ad_revenue(
        self,
        camera_id: str,
        ad_amount: float,
        period_key: Optional[str] = None,
        user_pool_ratio: float = AD_USER_POOL_RATIO,
    ) -> dict:
        """
        Работодатель оплатил рекламу на трансляции камеры.
        Пул user_pool = ad_amount * user_pool_ratio конвертируется в UT и делится
        пропорционально секундам присутствия лиц в кадре за period_key (час).
        """
        if ad_amount <= 0:
            raise ValueError("ad_amount must be positive")
        cam = self.get_camera(camera_id)
        if not cam:
            raise KeyError("camera not found")
        period = period_key or self._period_key()
        rows = self.conn.execute(
            """
            SELECT user_id, seconds FROM face_presence
            WHERE camera_id = ? AND period_key = ? AND seconds > 0
            """,
            (camera_id, period),
        ).fetchall()
        total_sec = sum(float(r["seconds"]) for r in rows)
        payout_id = str(uuid.uuid4())
        t = now_iso()
        user_pool = float(ad_amount) * float(user_pool_ratio)
        ut_pool = user_pool * AD_UT_PER_REVENUE
        self.conn.execute(
            """
            INSERT INTO ad_payouts (id, camera_id, poi_id, period_key, ad_amount, user_pool, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (payout_id, camera_id, cam.poi_id, period, float(ad_amount), user_pool, t),
        )
        shares: List[dict] = []
        if total_sec <= 0 or not rows:
            self.conn.commit()
            return {
                "payout_id": payout_id,
                "camera_id": camera_id,
                "period_key": period,
                "ad_amount": float(ad_amount),
                "user_pool": user_pool,
                "ut_pool": ut_pool,
                "total_presence_seconds": 0.0,
                "shares": [],
                "message": "Нет присутствия в кадре за период — UT не начислены",
            }
        for r in rows:
            sec = float(r["seconds"])
            share = sec / total_sec
            ut = round(ut_pool * share, 6)
            uid = r["user_id"]
            self.conn.execute(
                """
                INSERT INTO ad_payout_shares (payout_id, user_id, seconds, share, ut_earned)
                VALUES (?, ?, ?, ?, ?)
                """,
                (payout_id, uid, sec, share, ut),
            )
            self._ensure_wallet(uid)
            self.conn.execute(
                "UPDATE wallets SET balance_ut = ROUND(balance_ut + ?, 4) WHERE user_id = ?",
                (ut, uid),
            )
            shares.append(
                {
                    "user_id": uid,
                    "seconds": sec,
                    "share": round(share, 6),
                    "ut_earned": ut,
                }
            )
        self.conn.commit()
        return {
            "payout_id": payout_id,
            "camera_id": camera_id,
            "poi_id": cam.poi_id,
            "period_key": period,
            "ad_amount": float(ad_amount),
            "user_pool": user_pool,
            "ut_pool": ut_pool,
            "total_presence_seconds": total_sec,
            "shares": shares,
        }

    def list_airtime(self, poi_id: str) -> List[dict]:
        return [
            row_to_dict(r)
            for r in self.conn.execute(
                "SELECT wallet_address AS wallet, seconds, recorded_at AS at FROM airtime WHERE poi_id = ? ORDER BY id",
                (poi_id,),
            ).fetchall()
        ]

    def add_donation(self, poi_id: str, amount: float, message: str, donor: str) -> dict:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        did = str(uuid.uuid4())
        t = now_iso()
        self.conn.execute(
            """
            INSERT INTO donations (id, poi_id, amount, currency, message, donor, status, created_at)
            VALUES (?, ?, ?, 'GEL', ?, ?, 'pending_moderation', ?)
            """,
            (did, poi_id, amount, message, donor, t),
        )
        self.conn.commit()
        return {
            "id": did,
            "poi_id": poi_id,
            "amount": amount,
            "currency": "GEL",
            "message": message,
            "donor": donor,
            "status": "pending_moderation",
            "created_at": t,
        }

    def list_donations(self, poi_id: Optional[str] = None) -> List[dict]:
        if poi_id:
            rows = self.conn.execute("SELECT * FROM donations WHERE poi_id = ? ORDER BY created_at DESC", (poi_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM donations ORDER BY created_at DESC").fetchall()
        return [row_to_dict(r) for r in rows]

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        return row_to_dict(
            self.conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        )

    def update_user_profile(self, user_id: str, body: dict) -> dict:
        user = self.get_user(user_id)
        if not user:
            raise KeyError("user not found")
        t = now_iso()
        if "email" in body:
            email = body["email"].strip().lower()
            if not email or "@" not in email:
                raise ValueError("invalid email")
            self.conn.execute("UPDATE users SET email = ?, updated_at = ? WHERE id = ?", (email, t, user_id))
        prof = self.get_user_profile(user_id)
        phone = body.get("phone")
        fav = body.get("favorite_menu_item")
        if phone:
            phone = normalize_phone(phone)
        if prof:
            self.conn.execute(
                """
                UPDATE user_profiles SET
                    phone = COALESCE(?, phone),
                    favorite_menu_item = COALESCE(?, favorite_menu_item),
                    updated_at = ?
                WHERE user_id = ?
                """,
                (phone, fav.strip() if fav else None, t, user_id),
            )
        elif phone or fav:
            self.conn.execute(
                """
                INSERT INTO user_profiles (user_id, full_name, phone, favorite_menu_item, registered_via, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'web', ?, ?)
                """,
                (user_id, user.get("display_name", ""), phone or "", (fav or "").strip(), t, t),
            )
        self.conn.commit()
        return {
            "user": self.user_public(self.get_user(user_id)),
            "profile": self.get_user_profile(user_id),
        }

    def admin_stats(self) -> dict:
        users = self.conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        wallets = self.conn.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(balance_st),0) AS st, COALESCE(SUM(balance_ut),0) AS ut FROM wallets"
        ).fetchone()
        pois = self.conn.execute("SELECT COUNT(*) AS c FROM pois").fetchone()["c"]
        cams = self.conn.execute(
            "SELECT role, COUNT(*) AS c FROM cameras WHERE is_active = 1 GROUP BY role"
        ).fetchall()
        consents = self.conn.execute(
            "SELECT COUNT(*) AS c FROM consents WHERE revoked_at IS NULL"
        ).fetchone()["c"]
        profiles = self.conn.execute("SELECT COUNT(*) AS c FROM user_profiles").fetchone()["c"]
        perf_streams = self.conn.execute("SELECT COUNT(*) AS c FROM performance_streams").fetchone()["c"]
        bindings = self.conn.execute(
            "SELECT COUNT(*) AS c FROM signature_bindings WHERE active = 1"
        ).fetchone()["c"]
        views = self.conn.execute("SELECT COALESCE(SUM(seconds),0) AS s FROM view_events").fetchone()["s"]
        quality = self.network_quality()
        top_pois = self.sorted_tops("consent", None, None)[:5]
        return {
            "users_total": users,
            "wallets_total": wallets["c"],
            "balance_st_total": float(wallets["st"]),
            "balance_ut_total": float(wallets["ut"]),
            "pois_total": pois,
            "consents_active": consents,
            "profiles_total": profiles,
            "performance_streams_total": perf_streams,
            "signature_bindings_active": bindings,
            "view_seconds_total": float(views),
            "cameras_by_role": {r["role"]: r["c"] for r in cams},
            "network_quality": quality,
            "top_pois_consent": top_pois,
        }

    def bind_signature(self, user_id: str, poi_id: str) -> dict:
        row = self.conn.execute(
            """
            SELECT id FROM consents WHERE user_id = ? AND poi_id = ? AND revoked_at IS NULL
            ORDER BY consented_at DESC LIMIT 1
            """,
            (user_id, poi_id),
        ).fetchone()
        if not row:
            raise ValueError("no active consent for this poi")
        t = now_iso()
        self.conn.execute(
            "UPDATE signature_bindings SET active = 0 WHERE user_id = ? AND poi_id = ?",
            (user_id, poi_id),
        )
        bid = str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO signature_bindings (id, user_id, poi_id, consent_id, active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (bid, user_id, poi_id, row["id"], t),
        )
        self.conn.commit()
        audit_log(self.conn, "signature_bind", user_id=user_id, poi_id=poi_id, details={"binding_id": bid})
        self.conn.commit()
        return {"binding_id": bid, "poi_id": poi_id, "consent_id": row["id"], "active": True}

    def performance_stream_list(self, user_id: str, camera_id: str) -> List[dict]:
        rows = self.conn.execute(
            """
            SELECT * FROM performance_streams
            WHERE user_id = ? AND camera_id = ?
            ORDER BY created_at DESC
            """,
            (user_id, camera_id),
        ).fetchall()
        return [row_to_dict(r) for r in rows]

    def performance_stream_start(self, user_id: str, camera_id: str, title: str = "") -> dict:
        cam = self.get_camera(camera_id)
        if not cam or cam.role != "performance":
            raise ValueError("camera must be performance role")
        t = now_iso()
        sid = str(uuid.uuid4())
        rid = str(uuid.uuid4())
        RECORDER.start(rid, cam.poi_id)
        self.conn.execute(
            """
            INSERT INTO performance_streams
                (id, user_id, poi_id, camera_id, title, status, started_at, ended_at,
                 created_at, updated_at, recording_id, clip_path, clip_status)
            VALUES (?, ?, ?, ?, ?, 'live', ?, NULL, ?, ?, ?, NULL, 'recording')
            """,
            (sid, user_id, cam.poi_id, camera_id, title or "Эфир", t, t, t, rid),
        )
        self.conn.execute(
            """
            INSERT INTO stream_recordings
                (id, stream_id, user_id, poi_id, camera_id, camera_role, title, status,
                 started_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'performance', ?, 'recording', ?, ?, ?)
            """,
            (rid, sid, user_id, cam.poi_id, camera_id, title or "Эфир", t, t, t),
        )
        self.conn.commit()
        return row_to_dict(self.conn.execute("SELECT * FROM performance_streams WHERE id = ?", (sid,)).fetchone())

    @staticmethod
    def _parse_iso(ts: str) -> datetime:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def reward_stream_participants(
        self,
        stream_id: str,
        camera_id: str,
        started_at: str,
        ended_at: Optional[str] = None,
    ) -> dict:
        """
        После эфира: 1 UT = полное время стрима.
        Участник получает долю: presence_seconds / stream_duration (макс. 1 UT).
        """
        finished = ended_at or now_iso()
        try:
            stream_duration = max(
                0.0,
                (self._parse_iso(finished) - self._parse_iso(started_at)).total_seconds(),
            )
        except ValueError:
            stream_duration = 0.0

        existing = self.conn.execute(
            """
            SELECT r.user_id, r.presence_seconds, r.ut_earned, u.display_name
            FROM stream_presence_rewards r
            JOIN users u ON u.id = r.user_id
            WHERE r.stream_id = ?
            ORDER BY u.display_name
            """,
            (stream_id,),
        ).fetchall()
        if existing:
            return {
                "stream_id": stream_id,
                "stream_duration_seconds": stream_duration,
                "full_stream_ut": 1.0,
                "participants": [row_to_dict(r) for r in existing],
                "already_rewarded": True,
            }

        rows = self.conn.execute(
            """
            SELECT e.user_id, SUM(e.seconds) AS presence_seconds, u.display_name
            FROM face_presence_events e
            JOIN users u ON u.id = e.user_id
            WHERE e.camera_id = ? AND e.recorded_at >= ? AND e.recorded_at <= ?
            GROUP BY e.user_id, u.display_name
            ORDER BY u.display_name
            """,
            (camera_id, started_at, finished),
        ).fetchall()
        participants = []
        for r in rows:
            uid = r["user_id"]
            reward_id = str(uuid.uuid4())
            seconds = float(r["presence_seconds"])
            if stream_duration <= 0:
                ut = 0.0
            else:
                ut = round(min(1.0, seconds / stream_duration), 6)
            if ut <= 0:
                continue
            self._ensure_wallet(uid)
            self.conn.execute(
                "UPDATE wallets SET balance_ut = ROUND(balance_ut + ?, 4) WHERE user_id = ?",
                (ut, uid),
            )
            self.conn.execute(
                """
                INSERT INTO stream_presence_rewards
                    (id, stream_id, user_id, camera_id, presence_seconds, ut_earned, rewarded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (reward_id, stream_id, uid, camera_id, seconds, ut, finished),
            )
            participants.append(
                {
                    "user_id": uid,
                    "display_name": r["display_name"],
                    "presence_seconds": seconds,
                    "share": round(seconds / stream_duration, 6) if stream_duration > 0 else 0.0,
                    "ut_earned": ut,
                }
            )
        self.conn.commit()
        return {
            "stream_id": stream_id,
            "stream_duration_seconds": stream_duration,
            "full_stream_ut": 1.0,
            "participants": participants,
            "already_rewarded": False,
        }

    def performance_stream_stop(self, user_id: str, stream_id: str) -> dict:
        row = self._perf_stream_owned(user_id, stream_id)
        t = now_iso()
        clip_path = None
        clip_status = "saved"
        recording_id = row.get("recording_id")
        if recording_id:
            raw = RECORDER.stop(recording_id)
            if raw:
                clip = RECORDER.process_clip(recording_id, raw)
                clip_path = str(clip) if clip else str(raw)
                clip_status = "ready"
                self.conn.execute(
                    """
                    UPDATE stream_recordings SET raw_path = ?, clip_path = ?, status = ?,
                        ended_at = ?, updated_at = ? WHERE id = ?
                    """,
                    (str(raw), clip_path, clip_status, t, t, recording_id),
                )
            else:
                clip_status = "failed"
                self.conn.execute(
                    "UPDATE stream_recordings SET status = 'failed', ended_at = ?, updated_at = ? WHERE id = ?",
                    (t, t, recording_id),
                )
        self.conn.execute(
            """
            UPDATE performance_streams SET status = 'saved', ended_at = ?, updated_at = ?,
                clip_path = ?, clip_status = ? WHERE id = ?
            """,
            (t, t, clip_path, clip_status, stream_id),
        )
        self.conn.commit()
        rewards = self.reward_stream_participants(
            stream_id,
            row["camera_id"],
            row["started_at"],
            t,
        )
        result = row_to_dict(
            self.conn.execute("SELECT * FROM performance_streams WHERE id = ?", (stream_id,)).fetchone()
        )
        result["rewards"] = rewards
        return result

    def general_stream_start(self, user_id: str, camera_id: str, title: str = "") -> dict:
        cam = self.get_camera(camera_id)
        if not cam or cam.role != "general":
            raise ValueError("camera must be general role")
        consent = self.conn.execute(
            "SELECT 1 FROM consents WHERE user_id = ? AND poi_id = ? AND revoked_at IS NULL",
            (user_id, cam.poi_id),
        ).fetchone()
        if not consent:
            raise ValueError("active consent required for this poi")
        t = now_iso()
        rid = str(uuid.uuid4())
        RECORDER.start(rid, cam.poi_id)
        self.conn.execute(
            """
            INSERT INTO stream_recordings
                (id, stream_id, user_id, poi_id, camera_id, camera_role, title, status,
                 started_at, created_at, updated_at)
            VALUES (?, NULL, ?, ?, ?, 'general', ?, 'recording', ?, ?, ?)
            """,
            (rid, user_id, cam.poi_id, camera_id, title or "Запись", t, t, t),
        )
        self.conn.commit()
        return row_to_dict(self.conn.execute("SELECT * FROM stream_recordings WHERE id = ?", (rid,)).fetchone())

    def general_stream_stop(self, user_id: str, recording_id: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM stream_recordings WHERE id = ? AND user_id = ?", (recording_id, user_id)
        ).fetchone()
        if not row:
            raise KeyError("recording not found")
        t = now_iso()
        raw = RECORDER.stop(recording_id)
        clip_path = None
        status = "failed"
        if raw:
            clip = RECORDER.process_clip(recording_id, raw)
            clip_path = str(clip) if clip else str(raw)
            status = "ready"
        self.conn.execute(
            """
            UPDATE stream_recordings SET raw_path = ?, clip_path = ?, status = ?,
                ended_at = ?, updated_at = ? WHERE id = ?
            """,
            (str(raw) if raw else None, clip_path, status, t, t, recording_id),
        )
        self.conn.commit()
        rewards = self.reward_stream_participants(
            recording_id,
            row["camera_id"],
            row["started_at"],
            t,
        )
        result = row_to_dict(
            self.conn.execute("SELECT * FROM stream_recordings WHERE id = ?", (recording_id,)).fetchone()
        )
        result["rewards"] = rewards
        return result

    def list_user_recordings(self, user_id: str) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM stream_recordings WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [row_to_dict(r) for r in rows]

    def list_platform_links(self, user_id: str) -> List[dict]:
        rows = self.conn.execute(
            "SELECT id, platform, username, external_user_id, linked_at, updated_at FROM platform_links WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [row_to_dict(r) for r in rows]

    def link_platform_username(self, user_id: str, platform: str, username: str) -> dict:
        from platforms import PLATFORMS

        if platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {PLATFORMS}")
        if not (username or "").strip():
            raise ValueError("username required")
        t = now_iso()
        existing = self.conn.execute(
            "SELECT id FROM platform_links WHERE user_id = ? AND platform = ?", (user_id, platform)
        ).fetchone()
        if existing:
            self.conn.execute(
                "UPDATE platform_links SET username = ?, updated_at = ? WHERE id = ?",
                (username.strip(), t, existing["id"]),
            )
            lid = existing["id"]
        else:
            lid = str(uuid.uuid4())
            self.conn.execute(
                """
                INSERT INTO platform_links (id, user_id, platform, username, linked_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (lid, user_id, platform, username.strip(), t, t),
            )
        self.conn.commit()
        return row_to_dict(self.conn.execute("SELECT * FROM platform_links WHERE id = ?", (lid,)).fetchone())

    def unlink_platform(self, user_id: str, platform: str) -> None:
        self.conn.execute("DELETE FROM platform_links WHERE user_id = ? AND platform = ?", (user_id, platform))
        self.conn.commit()

    def platform_oauth_complete(self, user_id: str, platform: str, token_data: dict) -> dict:
        from platforms import PLATFORMS

        if platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {PLATFORMS}")
        t = now_iso()
        username = token_data.get("username") or token_data.get("login") or ""
        ext_id = token_data.get("external_user_id") or ""
        access = token_data.get("access_token") or ""
        refresh = token_data.get("refresh_token") or ""
        existing = self.conn.execute(
            "SELECT id FROM platform_links WHERE user_id = ? AND platform = ?", (user_id, platform)
        ).fetchone()
        if existing:
            self.conn.execute(
                """
                UPDATE platform_links SET username = ?, external_user_id = ?, oauth_token = ?,
                    refresh_token = ?, updated_at = ? WHERE id = ?
                """,
                (username, ext_id, access, refresh, t, existing["id"]),
            )
            lid = existing["id"]
        else:
            lid = str(uuid.uuid4())
            self.conn.execute(
                """
                INSERT INTO platform_links
                    (id, user_id, platform, username, external_user_id, oauth_token, refresh_token, linked_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (lid, user_id, platform, username, ext_id, access, refresh, t, t),
            )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id, platform, username, external_user_id, linked_at FROM platform_links WHERE id = ?",
            (lid,),
        ).fetchone()
        return row_to_dict(row)

    def sync_platform_comments(self, user_id: str, platform: str, broadcast_id: str) -> List[dict]:
        from platforms import get_adapter

        link = self.conn.execute(
            "SELECT * FROM platform_links WHERE user_id = ? AND platform = ?", (user_id, platform)
        ).fetchone()
        if not link or not link["oauth_token"]:
            raise ValueError("platform not linked with oauth")
        adapter = get_adapter(platform)
        comments = adapter.fetch_comments(link["oauth_token"], broadcast_id)
        t = now_iso()
        out = []
        for c in comments:
            cid = str(uuid.uuid4())
            ext = c.get("id", str(uuid.uuid4()))
            self.conn.execute(
                """
                INSERT OR IGNORE INTO platform_comments
                    (id, platform, external_comment_id, author_username, text, direction, synced_at)
                VALUES (?, ?, ?, ?, ?, 'inbound', ?)
                """,
                (cid, platform, ext, c.get("author", ""), c.get("text", ""), t),
            )
            out.append(c)
        self.conn.commit()
        return out

    def performance_stream_delete(self, user_id: str, stream_id: str) -> None:
        self._perf_stream_owned(user_id, stream_id)
        self.conn.execute("DELETE FROM performance_streams WHERE id = ?", (stream_id,))
        self.conn.commit()

    def _perf_stream_owned(self, user_id: str, stream_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM performance_streams WHERE id = ?", (stream_id,)).fetchone()
        if not row or row["user_id"] != user_id:
            raise KeyError("stream not found")
        return row_to_dict(row)

    def scene_description(self, poi_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM pois WHERE id = ?", (poi_id,)).fetchone()
        if not row:
            raise KeyError("poi not found")
        rate = float(row["consent_rate"])
        avatar_ratio = 1.0 - rate / 100.0
        real_ratio = rate / 100.0
        if avatar_ratio > real_ratio:
            mood = "fun"
            text = "Сейчас в кадре в основном гости с плашками — заходите, тут оживлённо!"
        else:
            mood = "promo"
            text = row["promo_description"] or f"Загляните в {row['name']} — лучшее место в районе."
        return {
            "poi_id": poi_id,
            "mood": mood,
            "description": text,
            "consent_rate_percent": rate,
            "avatar_ratio": avatar_ratio,
        }

    def record_health_snapshot(self, camera_id: str, status: str, detail: str) -> dict:
        snap = {"at": now_iso(), "status": status, "detail": detail}
        self.health_snapshots.setdefault(camera_id, []).append(snap)
        self.health_snapshots[camera_id] = self.health_snapshots[camera_id][-50:]
        return snap
```

## `apps/api_py/stream_paths.py`

```python
"""Имена потоков MediaMTX для мест и камер."""
from __future__ import annotations

RTMP_HOST = "127.0.0.1"
RTMP_PORT = 1935
HLS_HOST = "127.0.0.1"
HLS_PORT = 8888


def poi_stream_name(poi_id: str) -> str:
    return "poi_" + poi_id.replace("-", "")


def poi_rtmp_url(poi_id: str) -> str:
    return f"rtmp://{RTMP_HOST}:{RTMP_PORT}/{poi_stream_name(poi_id)}"


def poi_hls_url(poi_id: str) -> str:
    return f"http://{HLS_HOST}:{HLS_PORT}/{poi_stream_name(poi_id)}/index.m3u8"


def poi_masked_hls_url(poi_id: str) -> str:
    return f"http://{HLS_HOST}:{HLS_PORT}/{poi_stream_name(poi_id)}_avatar/index.m3u8"


def hls_proxy_url(stream_rel: str, api_port: int = 8090) -> str:
    """Same-origin HLS через API (обход cookie MediaMTX в браузере)."""
    rel = stream_rel.lstrip("/")
    return f"http://127.0.0.1:{api_port}/api/v1/hls/{rel}"


def poi_hls_proxy_url(poi_id: str, api_port: int = 8090) -> str:
    return hls_proxy_url(f"{poi_stream_name(poi_id)}/index.m3u8", api_port)


def poi_masked_hls_proxy_url(poi_id: str, api_port: int = 8090) -> str:
    return hls_proxy_url(f"{poi_stream_name(poi_id)}_avatar/index.m3u8", api_port)


def hls_direct_to_proxy(direct_url: str | None, api_port: int = 8090) -> str | None:
    """http://127.0.0.1:8888/gopro_main/index.m3u8 → API-прокси."""
    if not direct_url:
        return None
    from urllib.parse import urlparse

    parsed = urlparse(direct_url)
    rel = parsed.path.lstrip("/")
    if parsed.query:
        rel += "?" + parsed.query
    return hls_proxy_url(rel, api_port)


def stream_url_to_hls(stream_url: str, poi_id: str = "") -> str | None:
    if not stream_url:
        return None
    if stream_url.startswith("local://") and poi_id:
        return poi_hls_url(poi_id)
    if stream_url.startswith("rtmp://"):
        from urllib.parse import urlparse

        path = urlparse(stream_url).path.strip("/")
        if not path:
            return None
        host = urlparse(stream_url).hostname or HLS_HOST
        return f"http://{host}:{HLS_PORT}/{path}/index.m3u8"
    if "8554/" in stream_url:
        from urllib.parse import urlparse

        path = stream_url.split("8554/", 1)[1].split("?")[0].strip("/")
        host = urlparse(stream_url).hostname or HLS_HOST
        return f"http://{host}:{HLS_PORT}/{path}/index.m3u8"
    if stream_url.endswith(".m3u8"):
        return stream_url
    return None


def masked_stream_hls(stream_url: str, poi_id: str = "") -> str | None:
    if stream_url.startswith("local://") and poi_id:
        return poi_masked_hls_url(poi_id)
    if stream_url.startswith("rtmp://"):
        from urllib.parse import urlparse

        path = urlparse(stream_url).path.strip("/")
        if not path:
            return None
        host = urlparse(stream_url).hostname or HLS_HOST
        if path.endswith("_main"):
            masked = path[:-5] + "_avatar"
        else:
            masked = path + "_avatar"
        return f"http://{host}:{HLS_PORT}/{masked}/index.m3u8"
    if "8554/" not in stream_url:
        return None
    from urllib.parse import urlparse

    path = stream_url.split("8554/", 1)[1].split("?")[0].strip("/")
    if path.endswith("_main"):
        masked = path[:-5] + "_avatar"
    elif path == "gopro_main":
        masked = "gopro_avatar"
    else:
        masked = path + "_masked"
    host = urlparse(stream_url).hostname or HLS_HOST
    return f"http://{host}:{HLS_PORT}/{masked}/index.m3u8"


def hls_playlist_ready(url: str, timeout: float = 2.0) -> bool:
    if not url:
        return False
    import http.cookiejar
    import urllib.error
    import urllib.request
    from urllib.parse import urljoin

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        with opener.open(url, timeout=timeout) as resp:
            chunk = resp.read(256)
            return b"EXTM3U" in chunk
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            loc = e.headers["Location"]
            if loc.startswith("/"):
                loc = urljoin(url, loc)
            try:
                with opener.open(loc, timeout=timeout) as resp:
                    return b"EXTM3U" in resp.read(256)
            except (urllib.error.URLError, OSError, TimeoutError, urllib.error.HTTPError):
                return False
        if e.code == 404:
            return False
        try:
            return b"EXTM3U" in e.read(256)
        except Exception:
            return False
    except (urllib.error.URLError, OSError, TimeoutError):
        return False
```

## `apps/api_py/stream_recorder.py`

```python
"""Запись и нарезка стримов с маскированных камер (общий план / перфоманс)."""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Dict, Optional

from database import db_path
from stream_paths import poi_stream_name

FFMPEG = __import__("shutil").which("ffmpeg") or "/usr/local/bin/ffmpeg"


def recording_dir(recording_id: str) -> Path:
    d = db_path().parent / "recordings" / recording_id.replace("-", "")
    d.mkdir(parents=True, exist_ok=True)
    return d


class StreamRecorder:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._procs: Dict[str, subprocess.Popen] = {}
        self._raw_paths: Dict[str, Path] = {}

    def start(self, recording_id: str, poi_id: str) -> Path:
        stream = poi_stream_name(poi_id) + "_avatar"
        rtsp = f"rtsp://127.0.0.1:8554/{stream}"
        out_dir = recording_dir(recording_id)
        raw = out_dir / "raw.mp4"
        cmd = [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-i",
            rtsp,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            str(raw),
        ]
        with self._lock:
            old = self._procs.pop(recording_id, None)
            if old and old.poll() is None:
                old.terminate()
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._procs[recording_id] = proc
            self._raw_paths[recording_id] = raw
        print(f"[recorder] started {recording_id[:8]}… -> {raw}")
        return raw

    def stop(self, recording_id: str) -> Optional[Path]:
        with self._lock:
            proc = self._procs.pop(recording_id, None)
            raw = self._raw_paths.get(recording_id)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
        if raw and raw.is_file() and raw.stat().st_size > 0:
            return raw
        return None

    def process_clip(self, recording_id: str, raw: Path) -> Optional[Path]:
        if not raw.is_file() or raw.stat().st_size == 0:
            return None
        clip = raw.parent / "clip.mp4"
        cmd = [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(raw),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(clip),
        ]
        try:
            subprocess.run(cmd, check=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return raw if raw.is_file() else None
        return clip if clip.is_file() and clip.stat().st_size > 0 else raw

    def process_async(self, recording_id: str, raw: Path, on_done) -> None:
        def _run() -> None:
            clip = self.process_clip(recording_id, raw)
            on_done(clip or raw)

        threading.Thread(target=_run, daemon=True).start()


RECORDER = StreamRecorder()
```

## `apps/consent-kiosk/index.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cmir — регистрация и согласие</title>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.7/dist/hls.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #0a1628;
      color: #e8eef7;
      min-height: 100vh;
    }
    .wrap {
      max-width: 1100px;
      margin: 0 auto;
      padding: 1.5rem;
      display: grid;
      gap: 1.25rem;
      grid-template-columns: 1fr 1fr;
    }
    @media (max-width: 860px) { .wrap { grid-template-columns: 1fr; } }
    h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .sub { opacity: 0.75; font-size: 0.9rem; margin-bottom: 1rem; }
    .card {
      background: #132238;
      border-radius: 16px;
      padding: 1.25rem;
      border: 1px solid #243552;
    }
    .video-box {
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      background: #000;
      aspect-ratio: 16/10;
    }
    .video-box .mask-overlay-canvas {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 2;
      background: #000;
    }
    video.live-source-hidden {
      position: absolute; width: 1px; height: 1px; opacity: 0;
      pointer-events: none; z-index: -1;
    }
    .kiosk-locked { opacity: 0.55; pointer-events: none; }
    video { width: 100%; height: 100%; object-fit: cover; display: block; }
    .video-label {
      position: absolute; bottom: 8px; left: 8px;
      background: rgba(0,0,0,0.55); padding: 4px 10px; border-radius: 8px;
      font-size: 0.75rem;
    }
    label { display: block; font-size: 0.85rem; margin: 0.75rem 0 0.25rem; opacity: 0.9; }
    input, select {
      width: 100%; padding: 0.65rem 0.75rem; border-radius: 10px;
      border: 1px solid #3a4d66; background: #0f1419; color: #fff;
    }
    .docs { margin-top: 0.75rem; max-height: 280px; overflow-y: auto; }
    .doc-row {
      display: grid; grid-template-columns: 1fr auto; gap: 0.5rem;
      align-items: start; padding: 0.6rem 0; border-bottom: 1px solid #243552;
    }
    .doc-row:last-child { border-bottom: none; }
    .doc-title { font-size: 0.88rem; font-weight: 600; }
    .doc-link { font-size: 0.78rem; color: #6ecfff; cursor: pointer; margin-top: 0.2rem; display: inline-block; }
    .doc-check { display: flex; align-items: center; gap: 0.35rem; font-size: 0.82rem; white-space: nowrap; }
    .doc-check input { width: auto; }
    .btn-main {
      width: 100%; margin-top: 1rem; padding: 1rem;
      font-size: 1.1rem; font-weight: 700; border: none; border-radius: 12px;
      background: linear-gradient(135deg, #2ecc71, #27ae60); color: #062012;
      cursor: pointer;
    }
    .btn-main:disabled { opacity: 0.45; cursor: not-allowed; }
    #status { margin-top: 0.75rem; font-size: 0.85rem; min-height: 1.2em; }
    #status.err { color: #ff8a8a; }
    #status.ok { color: #7dffb0; }
    .modal {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7);
      align-items: center; justify-content: center; z-index: 50; padding: 1rem;
    }
    .modal.open { display: flex; }
    .modal-inner {
      background: #132238; border-radius: 14px; max-width: 560px; width: 100%;
      max-height: 80vh; overflow: hidden; display: flex; flex-direction: column;
    }
    .modal-head { padding: 1rem; border-bottom: 1px solid #243552; display: flex; justify-content: space-between; }
    .modal-body { padding: 1rem; overflow-y: auto; font-size: 0.85rem; line-height: 1.55; white-space: pre-wrap; }
    .modal-close { background: none; border: none; color: #fff; font-size: 1.25rem; cursor: pointer; }
    a { color: #6ecfff; }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="card">
      <h1>Камера согласия</h1>
      <p class="sub">До регистрации ваше лицо отображается с маской на всех камерах заведения.</p>
      <div class="video-box privacy-composite">
        <video id="live" class="live-source-hidden" autoplay playsinline muted></video>
        <canvas id="liveMaskCanvas" class="mask-overlay-canvas"></canvas>
        <span class="video-label" id="liveLabel">Подключение…</span>
      </div>
      <p style="margin-top:0.75rem;font-size:0.8rem;opacity:0.7" id="poiName"></p>
    </section>

    <section class="card" id="panelRegister">
      <h1>Регистрация</h1>
      <p class="sub">Заполните данные, подтвердите документы и снимите профиль лица со всех ракурсов (прямо / влево / вправо / вверх / вниз).</p>

      <div id="enrollBox" style="margin:0.75rem 0;padding:0.75rem;border-radius:12px;background:#0f1a2a;border:1px solid #243552;display:none">
        <p id="enrollStatus" style="font-size:0.9rem;margin-bottom:0.5rem">Подготовка съёмки лица…</p>
        <div id="enrollSteps" style="display:flex;gap:0.35rem;flex-wrap:wrap"></div>
      </div>

      <label for="fullName">ФИО</label>
      <input id="fullName" placeholder="Иванов Иван Иванович" autocomplete="name" />

      <label for="phone">Телефон</label>
      <input id="phone" type="tel" placeholder="+995 5XX XX XX XX" autocomplete="tel" />

      <label for="menuItem">Любимый пункт меню заведения</label>
      <select id="menuItem"><option value="">Загрузка…</option></select>

      <div class="docs" id="docsList"></div>

      <button type="button" class="btn-main" id="btnRegister" disabled>Регистрация и начало веселья!</button>
      <div id="status"></div>
      <p id="accountLink" style="margin-top:0.75rem;display:none"><a href="../index.html#account">Личный кабинет →</a></p>
    </section>
  </div>

  <div class="modal" id="docModal">
    <div class="modal-inner">
      <div class="modal-head">
        <strong id="modalTitle">Документ</strong>
        <button type="button" class="modal-close" id="modalClose">×</button>
      </div>
      <div class="modal-body" id="modalBody"></div>
    </div>
  </div>

  <p style="text-align:center;padding:1rem;font-size:0.8rem;opacity:0.6">
    <a href="../index.html">← На главную</a>
  </p>

  <script type="module">
    import { getToken, setToken } from '../js/api.js';
    import { startMaskedPageCamera } from '../js/live-camera.js';
    import { ENROLL_POSES, PoseEnrollment, yawPitchFromBbox, yawPitchFromMatrix } from '../js/face-enroll.js';

    const API = localStorage.getItem('cmir_api') || 'http://localhost:8090';
    const qs = new URLSearchParams(location.search);
    let poiId = qs.get('poi') || localStorage.getItem('cmir_kiosk_poi') || '';
    let documents = [];
    const DOC_KEYS = [
      'terms_of_service',
      'privacy_policy',
      'personal_data_consent',
      'biometric_data_consent',
      'wallet_agreement',
    ];
    const accepted = Object.fromEntries(DOC_KEYS.map((k) => [k, false]));

    const live = document.getElementById('live');
    const liveLabel = document.getElementById('liveLabel');
    const btn = document.getElementById('btnRegister');
    const statusEl = document.getElementById('status');
    let hls = null;
    let liveView = null;
    let kioskLocked = false;
    let faceDetector = null;
    let lastFaceBox = null;

    function getClientId() {
      let id = sessionStorage.getItem('cmir_kiosk_client');
      if (!id) {
        id = globalThis.crypto?.randomUUID?.() || `k-${Date.now()}`;
        sessionStorage.setItem('cmir_kiosk_client', id);
      }
      return id;
    }

    async function acquireStream() {
      // browser USB — не запускаем ffmpeg
      await resolvePoi();
    }

    function releaseStream() {
      if (!poiId) return;
      navigator.sendBeacon(
        `${API}/api/v1/pois/${poiId}/stream/release`,
        new Blob(
          [JSON.stringify({ client_id: getClientId(), force: false })],
          { type: 'application/json' },
        ),
      );
    }

    function stopEverything() {
      stopLive();
      releaseStream();
    }

    window.addEventListener('pagehide', stopEverything);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') stopEverything();
    });

    async function api(method, path, body) {
      const opts = { method, headers: { 'Content-Type': 'application/json' } };
      if (body !== undefined) opts.body = JSON.stringify(body);
      const res = await fetch(API + path, opts);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.error || res.statusText);
      return json;
    }

    function setStatus(msg, ok) {
      statusEl.textContent = msg || '';
      statusEl.className = ok ? 'ok' : msg ? 'err' : '';
    }

    function userHasConsent(u) {
      return Array.isArray(u?.consents) && u.consents.length > 0;
    }

    function lockKioskRegistered(name, message) {
      kioskLocked = true;
      btn.disabled = true;
      btn.textContent = 'Вы уже зарегистрированы';
      document.getElementById('panelRegister').classList.add('kiosk-locked');
      document.getElementById('fullName').disabled = true;
      document.getElementById('phone').disabled = true;
      document.getElementById('menuItem').disabled = true;
      document.querySelectorAll('#docsList input').forEach((cb) => { cb.disabled = true; });
      document.getElementById('accountLink').style.display = 'block';
      setStatus(message || `${name || 'Пользователь'}: согласие активно, маска не применяется.`, true);
      liveLabel.textContent = name ? `${name} — в кадре без маски` : 'Согласие уже дано';
    }

    function wireLiveView(view) {
      if (!view) return;
      view.onRecognized = ({ name }) => {
        if (name && !kioskLocked) lockKioskRegistered(name, `${name}: вы распознаны, регистрация не нужна.`);
      };
    }

    async function checkExistingRegistration() {
      const token = getToken();
      if (!token) return;
      try {
        const me = (await api('GET', '/api/v1/auth/me')).data;
        if (userHasConsent(me)) {
          lockKioskRegistered(me.display_name, 'Вы уже вошли в аккаунт с активным согласием.');
        }
      } catch (_) {}
    }

    function updateBtn() {
      if (kioskLocked) {
        btn.disabled = true;
        return;
      }
      const formOk = document.getElementById('fullName').value.trim()
        && document.getElementById('phone').value.trim()
        && document.getElementById('menuItem').value;
      const docsOk = DOC_KEYS.every((k) => accepted[k]);
      btn.disabled = !(formOk && docsOk);
    }

    function renderDocs() {
      const box = document.getElementById('docsList');
      box.innerHTML = documents.map((d) => `
        <div class="doc-row" data-type="${d.doc_type}">
          <div>
            <div class="doc-title">${d.title}</div>
            <span class="doc-link" data-open="${d.doc_type}">Прочитать документ</span>
          </div>
          <label class="doc-check">
            <input type="checkbox" data-doc="${d.doc_type}" />
            Согласен
          </label>
        </div>
      `).join('');
      box.querySelectorAll('[data-open]').forEach((el) => {
        el.onclick = () => openDoc(el.dataset.open);
      });
      box.querySelectorAll('input[data-doc]').forEach((cb) => {
        cb.onchange = () => {
          accepted[cb.dataset.doc] = cb.checked;
          updateBtn();
        };
      });
    }

    function openDoc(type) {
      const doc = documents.find((d) => d.doc_type === type);
      if (!doc) return;
      document.getElementById('modalTitle').textContent = doc.title;
      document.getElementById('modalBody').textContent = doc.content;
      document.getElementById('docModal').classList.add('open');
    }
    document.getElementById('modalClose').onclick = () => document.getElementById('docModal').classList.remove('open');

    function pickKioskPoi(list) {
      if (poiId) {
        const hit = list.find((p) => p.id === poiId);
        if (hit) return hit;
      }
      const local = list.find((p) =>
        (p.cameras || []).some((c) => c.is_active && c.source_type === 'local_usb'),
      );
      if (local) return local;
      const saved = localStorage.getItem('cmir_kiosk_poi');
      if (saved) {
        const hit = list.find((p) => p.id === saved);
        if (hit) return hit;
      }
      return (
        list.find((p) => (p.cameras || []).some((c) => c.role === 'consent' && c.is_active))
        || list[0]
      );
    }

    function previewCamera(poi) {
      const cams = (poi?.cameras || []).filter((c) => c.is_active);
      return cams.find((c) => c.role === 'consent') || cams.find((c) => c.is_preview) || cams[0] || null;
    }

    async function resolvePoi() {
      const res = await fetch(`${API}/api/v1/pois`);
      const json = await res.json();
      const list = json.data || [];
      const poi = pickKioskPoi(list);
      if (!poi) throw new Error('Нет места (POI). Создайте в админке.');
      poiId = poi.id;
      localStorage.setItem('cmir_kiosk_poi', poiId);
      document.getElementById('poiName').textContent = `Заведение: ${poi.name}`;
    }

    async function loadMenu() {
      const items = (await api('GET', `/api/v1/pois/${poiId}/menu-items`)).data || [];
      const sel = document.getElementById('menuItem');
      sel.innerHTML = '<option value="">— выберите —</option>'
        + items.map((i) => `<option value="${i}">${i}</option>`).join('');
      sel.onchange = updateBtn;
    }

    async function loadDocs() {
      documents = (await api('GET', '/api/v1/legal/documents')).data || [];
      renderDocs();
    }

    function stopHls() {
      if (hls) { hls.destroy(); hls = null; }
      live.removeAttribute('src');
    }

    function stopLive() {
      if (liveView) {
        liveView.stop();
        liveView = null;
      }
      stopHls();
    }

    async function startLiveStream() {
      const poisRes = await fetch(`${API}/api/v1/pois`);
      const poi = (await poisRes.json()).data?.find((p) => p.id === poiId);
      const cam = previewCamera(poi);
      if (!cam) {
        liveLabel.textContent = 'Нет камеры у места';
        return;
      }
      liveLabel.textContent = 'Подключение…';
      stopLive();
      const maskCanvas = document.getElementById('liveMaskCanvas');
      if (maskCanvas) maskCanvas.style.opacity = '0';
      try {
        const fallbacks = (poi?.cameras || []).filter((c) => c.is_active && c.id !== cam?.id);
        const result = await startMaskedPageCamera({
          video: live,
          canvas: document.getElementById('liveMaskCanvas'),
          cam,
          poi,
          fallbackCams: fallbacks,
          apiBase: API,
          clientId: getClientId(),
          usbOnly: true,
          onStatus: (msg) => { if (msg) liveLabel.textContent = msg; },
        });
        liveView = result.view;
        hls = result.hls;
        wireLiveView(liveView);
        liveLabel.textContent = kioskLocked ? liveLabel.textContent : 'Прямой эфир (с маской)';
      } catch (e) {
        liveLabel.textContent = e.message || 'Поток недоступен';
        setTimeout(() => startLiveStream(), 3000);
      }
    }

    async function initFaceDetector() {
      try {
        const mp = await import('https://cdn.jsdelivr.net/npm/@mediapipe/face_detection@0.4/face_detection.js');
        const { FaceDetection } = mp;
        faceDetector = new FaceDetection({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection@0.4/${f}` });
        faceDetector.setOptions({ model: 'short', minDetectionConfidence: 0.5 });
        faceDetector.onResults((res) => {
          const det = res.detections?.[0];
          if (!det?.boundingBox) { lastFaceBox = null; return; }
          const bb = det.boundingBox;
          lastFaceBox = { x: bb.xCenter - bb.width / 2, y: bb.yCenter - bb.height / 2, w: bb.width, h: bb.height };
        });
        const tick = async () => {
          if (live.readyState >= 2 && faceDetector) {
            await faceDetector.send({ image: live });
          }
          requestAnimationFrame(tick);
        };
        tick();
      } catch (_) {
        console.warn('MediaPipe unavailable, using center crop');
      }
    }

    function captureEmbedding() {
      const w = 32, h = 32;
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = live.videoWidth || 640;
      canvas.height = live.videoHeight || 480;
      ctx.drawImage(live, 0, 0, canvas.width, canvas.height);
      let sx = 0, sy = 0, sw = canvas.width, sh = canvas.height;
      if (lastFaceBox) {
        sx = Math.max(0, lastFaceBox.x * canvas.width);
        sy = Math.max(0, lastFaceBox.y * canvas.height);
        sw = Math.min(canvas.width - sx, lastFaceBox.w * canvas.width);
        sh = Math.min(canvas.height - sy, lastFaceBox.h * canvas.height);
      } else {
        const side = Math.min(canvas.width, canvas.height) * 0.5;
        sx = (canvas.width - side) / 2;
        sy = (canvas.height - side) / 2;
        sw = sh = side;
      }
      const out = document.createElement('canvas');
      out.width = w; out.height = h;
      out.getContext('2d').drawImage(canvas, sx, sy, sw, sh, 0, 0, w, h);
      const img = out.getContext('2d').getImageData(0, 0, w, h);
      const gray = new Float32Array(w * h);
      for (let i = 0; i < w * h; i++) {
        const o = i * 4;
        gray[i] = (img.data[o] + img.data[o + 1] + img.data[o + 2]) / (3 * 255);
      }
      let norm = 0;
      for (let i = 0; i < gray.length; i++) norm += gray[i] * gray[i];
      norm = Math.sqrt(norm) || 1;
      return Array.from(gray, (v) => v / norm);
    }

    let lastPose = { yaw: 0, pitch: 0 };
    let landmarker = null;

    function renderEnrollSteps(donePoses = []) {
      const box = document.getElementById('enrollSteps');
      if (!box) return;
      box.innerHTML = ENROLL_POSES.map((p) => {
        const ok = donePoses.includes(p.id);
        return `<span style="padding:0.25rem 0.55rem;border-radius:999px;font-size:0.75rem;background:${ok ? '#1e6b45' : '#243552'}">${ok ? '✓ ' : ''}${p.id}</span>`;
      }).join('');
    }

    async function initLandmarker() {
      try {
        const vision = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14');
        const { FaceLandmarker, FilesetResolver } = vision;
        const files = await FilesetResolver.forVisionTasks(
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm',
        );
        landmarker = await FaceLandmarker.createFromOptions(files, {
          baseOptions: {
            modelAssetPath:
              'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
            delegate: 'GPU',
          },
          runningMode: 'VIDEO',
          numFaces: 4,
          outputFacialTransformationMatrixes: true,
        });
      } catch (e) {
        console.warn('FaceLandmarker unavailable', e);
        landmarker = null;
      }
    }

    function samplePose() {
      if (landmarker && live.readyState >= 2) {
        try {
          const res = landmarker.detectForVideo(live, performance.now());
          const m = res.facialTransformationMatrixes?.[0]?.data || res.facialTransformationMatrixes?.[0];
          if (m) {
            lastPose = yawPitchFromMatrix(m);
            return lastPose;
          }
        } catch (_) {}
      }
      const bb = liveView?.lastFaceBbox;
      if (bb) {
        lastPose = yawPitchFromBbox(bb, live.videoWidth, live.videoHeight);
        return lastPose;
      }
      return lastPose;
    }

    btn.onclick = async () => {
      if (kioskLocked) return;
      btn.disabled = true;
      const enrollBox = document.getElementById('enrollBox');
      const enrollStatus = document.getElementById('enrollStatus');
      enrollBox.style.display = 'block';
      renderEnrollSteps([]);
      setStatus('Съёмка профиля лица: покрутите головой по подсказкам…');
      try {
        if (live.readyState < 2 && !liveView) throw new Error('Дождитесь появления изображения с камеры');
        if (!landmarker) await initLandmarker();
        const enrollment = new PoseEnrollment({
          onStatus: (msg) => {
            enrollStatus.textContent = msg;
            setStatus(msg);
            renderEnrollSteps(enrollment.templates.map((t) => t.pose));
          },
          captureSignature: () => liveView?.getLastFaceSignature() || captureEmbedding(),
          getPose: samplePose,
        });
        const templates = await enrollment.run();
        if (templates.length < ENROLL_POSES.length) {
          throw new Error('Не удалось снять все ракурсы лица — попробуйте ещё раз');
        }
        setStatus('Сохранение данных и биометрии…');
        const payload = {
          full_name: document.getElementById('fullName').value.trim(),
          phone: document.getElementById('phone').value.trim(),
          favorite_menu_item: document.getElementById('menuItem').value,
          face_embedding: templates[0].embedding,
          face_embeddings: templates,
          acceptances: Object.fromEntries(DOC_KEYS.map((k) => [k, true])),
        };
        const res = await api('POST', `/api/v1/pois/${poiId}/kiosk-register`, payload);
        if (res.data?.auth?.token) setToken(res.data.auth.token);
        if (res.data?.user) localStorage.setItem("cmir_user", JSON.stringify(res.data.user));
        document.getElementById('accountLink').style.display = 'block';
        lockKioskRegistered(
          document.getElementById('fullName').value.trim() || res.data?.user?.display_name,
          `${res.message}\nКошелёк: ${res.data.wallet?.address || '—'}\nПрофиль лица: ${templates.length} ракурсов\nBlockchain: ${res.data.blockchain?.tx_hash || '—'}${
            res.data?.temporary_password
              ? `\nВход позже: телефон ${res.data.phone} · пароль ${res.data.temporary_password}`
              : ''
          }`,
        );
      } catch (e) {
        setStatus(e.message);
        if (!kioskLocked) btn.disabled = false;
      }
    };

    ['input', 'change'].forEach((ev) => {
      document.getElementById('fullName').addEventListener(ev, updateBtn);
      document.getElementById('phone').addEventListener(ev, updateBtn);
    });

    try {
      await checkExistingRegistration();
      await acquireStream();
      await Promise.all([loadMenu(), loadDocs(), startLiveStream()]);
      updateBtn();
    } catch (e) {
      setStatus(e.message);
    }
  </script>
</body>
</html>
```

## `apps/face-worker/README.md`

````markdown
# Cmir Face Worker (Phase 0 POC)

Детекция лиц и наложение аватаров на видеопоток.

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m cmir_face.worker --input ../ingest/samples/demo.mp4 --output /tmp/cmir_out.mp4
```

## Следующие шаги

- [ ] MediaPipe face detection
- [ ] Overlay PNG avatars
- [ ] Consent embedding match (stub)
- [ ] Push to RTSP/HLS
````

## `apps/face-worker/cmir_face/__init__.py`

```python
"""Cmir computer vision pipeline."""

__version__ = "0.1.0"
```

## `apps/face-worker/cmir_face/avatar_sprite.py`

```python
"""Stylized static emoji avatars for privacy overlay."""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

EMOJI_IDS = ("stylized", "cool", "grin", "smile", "neutral")
_CACHE: Dict[Tuple[str, int], np.ndarray] = {}

# Между компактным (≈1.0) и крупным (≈1.82): закрывает лицо без «шлема»
DEFAULT_OVERLAY_SCALE = 1.48


def _draw_stylized_mascot(size: int) -> np.ndarray:
    """Стикер-стиль: градиент, обводка, звёздные глаза, улыбка с языком."""
    import cv2

    img = np.zeros((size, size, 4), dtype=np.uint8)
    cx, cy = size // 2, size // 2
    r = int(size * 0.44)

    # мягкий градиент (оранжево-жёлтый)
    for y in range(size):
        t = y / max(size - 1, 1)
        col = (
            int(70 + 40 * t),
            int(190 + 30 * t),
            int(255 - 20 * t),
            255,
        )
        cv2.ellipse(img, (cx, cy), (r, r), 0, 0, 360, col, -1, lineType=cv2.LINE_AA)

    # блик
    cv2.ellipse(
        img,
        (cx - r // 3, cy - r // 3),
        (r // 3, r // 4),
        0,
        0,
        360,
        (200, 240, 255, 255),
        -1,
        lineType=cv2.LINE_AA,
    )

    # толстая обводка
    cv2.circle(img, (cx, cy), r, (20, 80, 160, 255), max(3, size // 32), lineType=cv2.LINE_AA)
    cv2.circle(img, (cx, cy), r - 2, (40, 120, 200, 255), 1, lineType=cv2.LINE_AA)

    # румянец
    cheek_y = cy + int(size * 0.05)
    for dx in (-int(size * 0.22), int(size * 0.22)):
        cv2.ellipse(
            img,
            (cx + dx, cheek_y),
            (int(size * 0.07), int(size * 0.05)),
            0,
            0,
            360,
            (120, 140, 255, 255),
            -1,
            lineType=cv2.LINE_AA,
        )

    # звёздные глаза
    eye_y = cy - int(size * 0.1)
    eye_dx = int(size * 0.17)

    def star(ex: int, ey: int, rad: int) -> None:
        pts = []
        for i in range(10):
            ang = i * np.pi / 5 - np.pi / 2
            rr = rad if i % 2 == 0 else rad * 0.45
            pts.append([int(ex + rr * np.cos(ang)), int(ey + rr * np.sin(ang))])
        cv2.fillPoly(img, [np.array(pts, dtype=np.int32)], (30, 30, 40, 255), lineType=cv2.LINE_AA)
        cv2.circle(img, (ex, ey), max(2, rad // 3), (255, 255, 255, 255), -1, lineType=cv2.LINE_AA)

    star(cx - eye_dx, eye_y, int(size * 0.065))
    star(cx + eye_dx, eye_y, int(size * 0.065))

    # рот + язык
    mouth_y = cy + int(size * 0.16)
    cv2.ellipse(
        img,
        (cx, mouth_y),
        (int(size * 0.2), int(size * 0.11)),
        0,
        0,
        180,
        (40, 30, 30, 255),
        -1,
        lineType=cv2.LINE_AA,
    )
    cv2.ellipse(
        img,
        (cx, mouth_y + int(size * 0.06)),
        (int(size * 0.07), int(size * 0.05)),
        0,
        0,
        180,
        (80, 100, 255, 255),
        -1,
        lineType=cv2.LINE_AA,
    )
    return img


def _draw_vector_smiley(size: int, style: str) -> np.ndarray:
    if style == "stylized":
        return _draw_stylized_mascot(size)
    import cv2

    img = np.zeros((size, size, 4), dtype=np.uint8)
    cx, cy = size // 2, size // 2
    r = int(size * 0.46)
    cv2.circle(img, (cx, cy), r, (80, 210, 255, 255), -1, lineType=cv2.LINE_AA)
    return img


def get_sprite(emoji_id: str = "stylized", size: int = 384) -> np.ndarray:
    emoji_id = emoji_id if emoji_id in EMOJI_IDS else "stylized"
    key = (emoji_id, size)
    if key in _CACHE:
        return _CACHE[key]
    sprite = _draw_vector_smiley(size, emoji_id)
    _CACHE[key] = sprite
    return sprite


def overlay_sprite(
    frame: np.ndarray,
    x: int,
    y: int,
    bw: int,
    bh: int,
    sprite: np.ndarray,
    scale: float = DEFAULT_OVERLAY_SCALE,
) -> None:
    """Непрозрачный оверлей: сплошной диск + жёсткая маска спрайта (лицо не просвечивает)."""
    import cv2

    fh, fw = frame.shape[:2]
    base = max(bw, bh, 28)
    side = int(base * scale)
    resized = cv2.resize(sprite, (side, side), interpolation=cv2.INTER_LINEAR)

    cx = x + bw // 2
    cy = y + int(bh * 0.46)
    x1, y1 = cx - side // 2, cy - side // 2
    x2, y2 = x1 + side, y1 + side

    if x2 <= 0 or y2 <= 0 or x1 >= fw or y1 >= fh:
        return

    # Сплошной фон под маской — закрывает лицо даже в прозрачных зонах спрайта
    backing_r = max(12, int(side * 0.44))
    cv2.circle(
        frame,
        (cx, cy),
        backing_r,
        (55, 175, 250),
        -1,
        lineType=cv2.LINE_AA,
    )

    sx1, sy1 = max(0, -x1), max(0, -y1)
    dx1, dy1 = max(0, x1), max(0, y1)
    sx2 = sx1 + min(fw, x2) - dx1
    sy2 = sy1 + min(fh, y2) - dy1
    if sx2 <= sx1 or sy2 <= sy1:
        return

    patch = resized[sy1:sy2, sx1:sx2]
    roi = frame[dy1 : dy1 + patch.shape[0], dx1 : dx1 + patch.shape[1]]
    if patch.shape[2] == 4:
        alpha = patch[:, :, 3]
        bgr = patch[:, :, :3]
        mask = alpha > 20
        roi[mask] = bgr[mask]
    else:
        roi[:] = patch
```

## `apps/face-worker/cmir_face/embeddings.py`

```python
"""POC + multi-pose face signatures for consent matching.

Matching: best cosine score across all enrolled pose templates per user.
Patch pipeline uses histogram equalization for lighting robustness.
Optional InsightFace/ArcFace can be wired later; multi-pose templates are
the primary fix for angled heads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

PATCH_SIZE = 32
MATCH_THRESHOLD = 0.82  # multi-pose templates allow slightly lower than single-pose 0.85
CONSENT_CAM_THRESHOLD = 0.88
HOLD_FRAMES = 18  # hysteresis: keep consented after a hit to avoid flicker masks


def patch_from_bbox(frame: np.ndarray, x: int, y: int, bw: int, bh: int) -> np.ndarray:
    """Extract normalized grayscale signature from face bounding box."""
    h, w = frame.shape[:2]
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w, x + bw)
    y2 = min(h, y + bh)
    if x2 <= x1 or y2 <= y1:
        return np.zeros(PATCH_SIZE * PATCH_SIZE, dtype=np.float32)
    crop = frame[y1:y2, x1:x2]
    import cv2

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        gray = clahe.apply(gray)
    except Exception:
        gray = cv2.equalizeHist(gray)
    resized = cv2.resize(gray, (PATCH_SIZE, PATCH_SIZE))
    vec = resized.astype(np.float32).flatten() / 255.0
    norm = np.linalg.norm(vec)
    if norm > 1e-6:
        vec /= norm
    return vec


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return 0.0
    return float(np.dot(a, b))


def _vectors_for_face(face: dict) -> List[np.ndarray]:
    out: List[np.ndarray] = []
    for key in ("embeddings",):
        for item in face.get(key) or []:
            vec = np.array(item, dtype=np.float32)
            if vec.size == PATCH_SIZE * PATCH_SIZE:
                n = np.linalg.norm(vec)
                out.append(vec / n if n > 1e-6 else vec)
    for tpl in face.get("templates") or []:
        raw = tpl.get("embedding") if isinstance(tpl, dict) else tpl
        vec = np.array(raw or [], dtype=np.float32)
        if vec.size == PATCH_SIZE * PATCH_SIZE:
            n = np.linalg.norm(vec)
            out.append(vec / n if n > 1e-6 else vec)
    if not out and face.get("embedding") is not None:
        vec = np.array(face.get("embedding") or [], dtype=np.float32)
        if vec.size == PATCH_SIZE * PATCH_SIZE:
            n = np.linalg.norm(vec)
            out.append(vec / n if n > 1e-6 else vec)
    return out


def best_match_score(signature: np.ndarray, face: dict) -> float:
    best = 0.0
    for vec in _vectors_for_face(face):
        best = max(best, cosine_similarity(signature, vec))
    return best


def is_consented(
    signature: np.ndarray,
    consented: Sequence,
    threshold: float = MATCH_THRESHOLD,
) -> bool:
    faces: List[dict] = []
    for item in consented:
        if isinstance(item, dict):
            faces.append(item)
        else:
            faces.append({"embedding": np.asarray(item, dtype=np.float32).tolist()})
    return match_consented_face(signature, faces, threshold=threshold) is not None


def load_embeddings_json(path: str) -> List[np.ndarray]:
    p = Path(path)
    if not p.is_file():
        return []
    data = json.loads(p.read_text())
    out: List[np.ndarray] = []
    for item in data.get("embeddings", []):
        vec = np.array(item, dtype=np.float32)
        if vec.size == PATCH_SIZE * PATCH_SIZE:
            out.append(vec)
    return out


def match_consented_name(
    signature: np.ndarray,
    faces: List[dict],
    threshold: float = MATCH_THRESHOLD,
) -> Optional[str]:
    hit = match_consented_face(signature, faces, threshold=threshold)
    return hit.get("display_name") if hit else None


def match_consented_face(
    signature: np.ndarray,
    faces: List[dict],
    threshold: float = MATCH_THRESHOLD,
) -> Optional[dict]:
    """Best-of-all-pose-templates per user; supports many simultaneous faces."""
    best = None
    best_score = threshold
    for face in faces:
        score = best_match_score(signature, face)
        if score >= best_score:
            best_score = score
            best = {**face, "match_score": score}
    return best


def post_face_presence(api_url: str, camera_id: str, presence: List[dict], worker_token: str = "") -> None:
    """Отчёт секунд присутствия в кадре (face-worker → API)."""
    if not api_url or not camera_id or not presence:
        return
    try:
        import urllib.request

        payload = json.dumps({"camera_id": camera_id, "presence": presence}).encode()
        req = urllib.request.Request(
            f"{api_url.rstrip('/')}/api/v1/face-presence",
            data=payload,
            headers={
                "Content-Type": "application/json",
                **({"X-Cmir-Worker": worker_token} if worker_token else {}),
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            resp.read()
    except Exception as e:
        print(f"Warning: face-presence report failed: {e}")


def fetch_consented_faces_from_api(api_url: str) -> List[dict]:
    try:
        import os
        import urllib.request

        url = f"{api_url.rstrip('/')}/api/v1/consented-faces"
        token = os.environ.get("CMIR_WORKER_TOKEN", "").strip()
        headers = {"X-Cmir-Worker": token} if token else {}
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        return list(data.get("data", {}).get("faces", []))
    except Exception as e:
        print(f"Warning: could not fetch consented faces: {e}")
        return []


def fetch_embeddings_from_api(api_url: str, poi_id: str) -> List[np.ndarray]:
    try:
        import os
        import urllib.request

        url = f"{api_url.rstrip('/')}/api/v1/pois/{poi_id}/embeddings"
        token = os.environ.get("CMIR_WORKER_TOKEN", "").strip()
        headers = {"X-Cmir-Worker": token} if token else {}
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        out: List[np.ndarray] = []
        for item in data.get("data", {}).get("embeddings", []):
            vec = np.array(item, dtype=np.float32)
            if vec.size == PATCH_SIZE * PATCH_SIZE:
                out.append(vec)
        return out
    except Exception as e:
        print(f"Warning: could not fetch embeddings: {e}")
        return []
```

## `apps/face-worker/cmir_face/eye_mask.py`

```python
"""Одна чёрная плашка на лицо (полицейская хроника) — keypoints MediaPipe."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple
import math

Box = Tuple[int, int, int, int]


def _clamp_box(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(12, bw), max(10, bh)
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


def eye_rects_from_detection(det, frame_w: int, frame_h: int) -> List[Box]:
    """Два чёрных прямоугольника на глаза."""
    loc = det.location_data
    kps = loc.relative_keypoints
    w, h = frame_w, frame_h
    rb = loc.relative_bounding_box
    rects: List[Box] = []

    if len(kps) >= 2:
        eyes = [(kps[0].x * w, kps[0].y * h), (kps[1].x * w, kps[1].y * h)]
        rx, ry = eyes[0]
        lx, ly = eyes[1]
        eye_dist = math.hypot(lx - rx, ly - ry)
        ew = max(14, int(eye_dist * 0.42))
        eh = max(10, int(ew * 0.55))
        for ex, ey in eyes:
            rects.append(_clamp_box(int(ex - ew / 2), int(ey - eh / 2), ew, eh, w, h))
        return rects

    bx, by = int(rb.xmin * w), int(rb.ymin * h)
    bw, bh = int(rb.width * w), int(rb.height * h)
    ew, eh = max(14, bw // 5), max(10, bh // 8)
    rects.append(_clamp_box(bx + bw // 4 - ew // 2, by + bh // 3, ew, eh, w, h))
    rects.append(_clamp_box(bx + 3 * bw // 4 - ew // 2, by + bh // 3, ew, eh, w, h))
    return rects


def eye_rects_from_detections(detections, frame_w: int, frame_h: int) -> List[Box]:
    out: List[Box] = []
    for det in detections:
        out.extend(eye_rects_from_detection(det, frame_w, frame_h))
    return out


def draw_eye_rects(frame, rects: List[Box]) -> None:
    import cv2

    for x, y, bw, bh in rects:
        cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 0, 0), thickness=-1)


def draw_mask_image(frame, bar: Box, image_bgra) -> None:
    """Наложить картинку маски вместо чёрного прямоугольника."""
    import cv2
    import numpy as np

    x, y, bw, bh = bar
    if image_bgra is None or bw < 4 or bh < 4:
        cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 0, 0), thickness=-1)
        return
    resized = cv2.resize(image_bgra, (bw, bh), interpolation=cv2.INTER_AREA)
    if resized.shape[2] == 4:
        alpha = resized[:, :, 3:4] / 255.0
        roi = frame[y : y + bh, x : x + bw]
        if roi.shape[0] == bh and roi.shape[1] == bw:
            blended = (alpha * resized[:, :, :3] + (1 - alpha) * roi).astype(np.uint8)
            frame[y : y + bh, x : x + bw] = blended
    else:
        frame[y : y + bh, x : x + bw] = resized[:, :, :3]


def face_bar_from_detection(det, frame_w: int, frame_h: int) -> Box | None:
    """
    Горизонтальная плашка по центру лица: закрывает глаза и верхнюю часть лица.
    Ширина ~1.25× расстояние между глазами, высота ~0.55× ширины.
    """
    loc = det.location_data
    kps = loc.relative_keypoints
    w, h = frame_w, frame_h
    rb = loc.relative_bounding_box

    if len(kps) >= 2:
        rx, ry = kps[0].x * w, kps[0].y * h
        lx, ly = kps[1].x * w, kps[1].y * h
        eye_dist = math.hypot(lx - rx, ly - ry)
        cx = (rx + lx) / 2
        cy = (ry + ly) / 2
    else:
        bx, by = int(rb.xmin * w), int(rb.ymin * h)
        bw, bh = int(rb.width * w), int(rb.height * h)
        eye_dist = bw * 0.55
        cx = bx + bw / 2
        cy = by + bh * 0.42

    if eye_dist < 10:
        bw = max(int(rb.width * w), 48)
        eye_dist = bw * 0.55
        cx = int(rb.xmin * w) + bw / 2
        cy = int(rb.ymin * h) + int(rb.height * h) * 0.42

    bar_w = max(36, int(eye_dist * 1.28))
    bar_h = max(22, int(bar_w * 0.52))
    # чуть выше центра глаз — типичная «хроника»
    cy = cy - bar_h * 0.08

    return _clamp_box(int(cx - bar_w / 2), int(cy - bar_h / 2), bar_w, bar_h, w, h)


def face_bars_from_detections(detections, frame_w: int, frame_h: int) -> List[Box]:
    out: List[Box] = []
    for det in detections:
        bar = face_bar_from_detection(det, frame_w, frame_h)
        if bar:
            out.append(bar)
    return out


def draw_face_bar(frame, bar: Box) -> None:
    import cv2

    x, y, bw, bh = bar
    cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 0, 0), thickness=-1)


def bbox_from_detection(det, frame_w: int, frame_h: int) -> Box:
    rb = det.location_data.relative_bounding_box
    w, h = frame_w, frame_h
    x = int(rb.xmin * w)
    y = int(rb.ymin * h)
    bw = int(rb.width * w)
    bh = int(rb.height * h)
    return _clamp_box(x, y, bw, bh, w, h)


@dataclass
class _BarTrack:
    box: Box
    missed: int = 0
    smooth: Box = field(default_factory=lambda: (0, 0, 0, 0))

    def __post_init__(self) -> None:
        self.smooth = self.box

    @property
    def center(self) -> Tuple[float, float]:
        x, y, bw, bh = self.smooth
        return x + bw / 2, y + bh / 2


class FaceBarTracker:
    """Сглаживание одной плашки на лицо."""

    def __init__(self, pos_smooth: float = 0.55, size_smooth: float = 0.35, max_missed: int = 15) -> None:
        self.pos_smooth = pos_smooth
        self.size_smooth = size_smooth
        self.max_missed = max_missed
        self._tracks: List[_BarTrack] = []
        self._fw = 0
        self._fh = 0

    def _smooth_box(self, old: Box, new: Box) -> Box:
        ox, oy, ow, oh = old
        nx, ny, nw, nh = new
        ap, az = self.pos_smooth, self.size_smooth
        cx = int(ap * (nx + nw / 2) + (1 - ap) * (ox + ow / 2))
        cy = int(ap * (ny + nh / 2) + (1 - ap) * (oy + oh / 2))
        nw2 = int(az * nw + (1 - az) * ow)
        nh2 = int(az * nh + (1 - az) * oh)
        return _clamp_box(cx - nw2 // 2, cy - nh2 // 2, nw2, nh2, self._fw, self._fh)

    def update(self, bars: List[Box], frame_w: int, frame_h: int) -> List[Box]:
        self._fw, self._fh = frame_w, frame_h
        used = [False] * len(bars)

        for track in self._tracks:
            tcx, tcy = track.center
            best_i, best_d = -1, 1e9
            for i, bar in enumerate(bars):
                if used[i]:
                    continue
                bx, by, bw, bh = bar
                cx, cy = bx + bw / 2, by + bh / 2
                d = math.hypot(cx - tcx, cy - tcy)
                if d < best_d:
                    best_d, best_i = d, i

            max_d = max(frame_w, frame_h) * 0.14
            if best_i >= 0 and best_d < max_d:
                used[best_i] = True
                track.box = bars[best_i]
                track.smooth = self._smooth_box(track.smooth, track.box)
                track.missed = 0
            else:
                track.missed += 1

        for i, bar in enumerate(bars):
            if not used[i]:
                t = _BarTrack(box=bar)
                t.smooth = bar
                self._tracks.append(t)

        self._tracks = [t for t in self._tracks if t.missed <= self.max_missed]
        return [t.smooth for t in self._tracks]
```

## `apps/face-worker/cmir_face/face_box.py`

```python
"""Face bounding boxes from MediaPipe detections — include hair, stable sizing."""
from __future__ import annotations

from typing import List, Tuple

Box = Tuple[int, int, int, int]


def _clamp(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(20, bw), max(20, bh)
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


def box_from_detection(det, frame_w: int, frame_h: int) -> Box:
    """
    Union of MediaPipe relative bbox + keypoints (eyes/ears/mouth).
    Extra margin on top for hair; wider than chin-only box.
    """
    loc = det.location_data
    rb = loc.relative_bounding_box
    w, h = frame_w, frame_h

    # keypoints in normalized coords
    xs, ys = [], []
    for kp in loc.relative_keypoints:
        xs.append(kp.x * w)
        ys.append(kp.y * h)

    kx1, kx2 = min(xs), max(xs)
    ky1, ky2 = min(ys), max(ys)
    kw, kh = kx2 - kx1, ky2 - ky1

    bx = int(rb.xmin * w)
    by = int(rb.ymin * h)
    bw = int(rb.width * w)
    bh = int(rb.height * h)

    # union
    x1 = min(bx, int(kx1))
    y1 = min(by, int(ky1))
    x2 = max(bx + bw, int(kx2))
    y2 = max(by + bh, int(ky2))
    uw, uh = x2 - x1, y2 - y1

    # prefer keypoint span for width; height extends up for hair
    face_w = max(uw, kw * 1.15)
    face_h = max(uh, kh * 1.35)
    cx = (kx1 + kx2) / 2 if kw > 0 else x1 + uw / 2
    cy = (ky1 + ky2) / 2 if kh > 0 else y1 + uh / 2

    # asym padding: больше сверху (волосы), чуть по бокам
    top_pad = face_h * 0.72
    bottom_pad = face_h * 0.38
    side_pad = face_w * 0.42

    x = int(cx - face_w / 2 - side_pad)
    y = int(cy - face_h / 2 - top_pad)
    bw = int(face_w + 2 * side_pad)
    bh = int(face_h + top_pad + bottom_pad)
    return _clamp(x, y, bw, bh, w, h)


def detections_to_boxes(detections, frame_w: int, frame_h: int) -> List[Box]:
    return [box_from_detection(d, frame_w, frame_h) for d in detections]
```

## `apps/face-worker/cmir_face/privacy_gate.py`

```python
"""Задержанный выход: кадр анализируется и маскируется до попадания в поток."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional, Tuple

import numpy as np

Box = Tuple[int, int, int, int]


@dataclass
class TrackedFace:
    box: Box
    ttl: int = 8


@dataclass
class PrivacyGate:
    """Держит кадры в буфере, на выход — детекция + маска (fail-safe)."""

    delay_frames: int = 24
    face_ttl: int = 10
    expand: float = 1.15
    _raw: Deque[np.ndarray] = field(default_factory=deque)
    _tracks: List[TrackedFace] = field(default_factory=list)

    def ingest(self, frame: np.ndarray) -> List[np.ndarray]:
        """Принять кадр; вернуть кадры, готовые к публикации."""
        self._raw.append(frame.copy())
        out: List[np.ndarray] = []
        while len(self._raw) > self.delay_frames:
            out.append(self._raw.popleft())
        return out

    def expand_box(self, x: int, y: int, bw: int, bh: int, w: int, h: int) -> Box:
        cx, cy = x + bw / 2, y + bh / 2
        bw2 = int(bw * self.expand)
        bh2 = int(bh * self.expand)
        nx = int(cx - bw2 / 2)
        ny = int(cy - bh2 / 2)
        nx = max(0, min(nx, w - 1))
        ny = max(0, min(ny, h - 1))
        return nx, ny, min(bw2, w - nx), min(bh2, h - ny)

    def update_tracks(self, boxes: List[Box]) -> List[Box]:
        if boxes:
            self._tracks = [TrackedFace(box=b, ttl=self.face_ttl) for b in boxes]
        else:
            for t in self._tracks:
                t.ttl -= 1
            self._tracks = [t for t in self._tracks if t.ttl > 0]
        return [t.box for t in self._tracks]

    def flush(self) -> List[np.ndarray]:
        out = list(self._raw)
        self._raw.clear()
        return out
```

## `apps/face-worker/cmir_face/rtmp_writer.py`

```python
"""Publish processed BGR frames to RTMP (MediaMTX)."""
from __future__ import annotations

import shutil
import subprocess
from typing import Optional

import numpy as np


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg"


class FfmpegRtmpWriter:
    def __init__(self, url: str, width: int, height: int, fps: float = 30.0) -> None:
        self.url = url
        self.width = width
        self.height = height
        self.fps = fps if 5 <= fps <= 60 else 30.0
        self._cmd = [
            _ffmpeg(),
            "-nostdin",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(self.fps),
            "-i",
            "pipe:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-pix_fmt",
            "yuv420p",
            "-g",
            str(int(self.fps)),
            "-f",
            "flv",
            url,
        ]
        self._proc: Optional[subprocess.Popen] = subprocess.Popen(
            self._cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def write(self, frame: np.ndarray) -> bool:
        if self._proc is None or self._proc.stdin is None:
            return False
        if self._proc.poll() is not None:
            return False
        if frame.shape[0] != self.height or frame.shape[1] != self.width:
            return False
        try:
            self._proc.stdin.write(frame.tobytes())
            return True
        except (BrokenPipeError, ValueError):
            return False

    def close(self) -> None:
        if self._proc is None:
            return
        if self._proc.stdin:
            try:
                self._proc.stdin.close()
            except Exception:
                pass
        try:
            self._proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        self._proc = None
```

## `apps/face-worker/cmir_face/rtsp_capture.py`

```python
"""RTSP capture via ffmpeg (OpenCV often fails on macOS)."""
from __future__ import annotations

import shutil
import subprocess
from typing import Optional, Tuple

import numpy as np


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg"


def _ffprobe() -> str:
    return shutil.which("ffprobe") or "/usr/local/bin/ffprobe"


def probe_stream(url: str) -> Tuple[int, int, float]:
    cmd = [
        _ffprobe(),
        "-rtsp_transport",
        "tcp",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate",
        "-of",
        "csv=p=0",
        url,
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    parts = out.split(",")
    w, h = int(parts[0]), int(parts[1])
    fps = 25.0
    if len(parts) > 2 and parts[2]:
        num, _, den = parts[2].partition("/")
        try:
            fps = float(num) / float(den or "1")
        except ValueError:
            fps = 25.0
    if fps > 60 or fps < 5:
        fps = 30.0
    return w, h, fps


class FfmpegRtspCapture:
    def __init__(self, url: str) -> None:
        self.url = url
        self.width, self.height, self.fps = probe_stream(url)
        self._cmd = [
            _ffmpeg(),
            "-nostdin",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-i",
            url,
            "-an",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "pipe:1",
        ]
        self._proc = subprocess.Popen(
            self._cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self._frame_bytes = self.width * self.height * 3

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self._proc.stdout is None:
            return False, None
        raw = self._proc.stdout.read(self._frame_bytes)
        if len(raw) < self._frame_bytes:
            return False, None
        frame = np.frombuffer(raw, dtype=np.uint8).reshape(self.height, self.width, 3).copy()
        return True, frame

    def release(self) -> None:
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._proc.kill()
```

## `apps/face-worker/cmir_face/tracker.py`

```python
"""Stable face tracking: IoU + center distance, separate position/size smoothing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple
import math

Box = Tuple[int, int, int, int]


def _iou(a: Box, b: Box) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter <= 0:
        return 0.0
    return inter / (aw * ah + bw * bh - inter)


def _center(b: Box) -> Tuple[float, float]:
    x, y, w, h = b
    return x + w / 2, y + h / 2


def _center_dist(a: Box, b: Box) -> float:
    ax, ay = _center(a)
    bx, by = _center(b)
    return math.hypot(ax - bx, ay - by)


def _clamp_box(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(20, bw), max(20, bh)
    x, y = max(0, min(x, fw - 1)), max(0, min(y, fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


@dataclass
class _Track:
    box: Box
    missed: int = 0
    age: int = 0
    smooth: Box = field(default_factory=lambda: (0, 0, 0, 0))

    def __post_init__(self) -> None:
        self.smooth = self.box


class FaceTracker:
    def __init__(
        self,
        pos_smooth: float = 0.42,
        size_smooth: float = 0.28,
        iou_match: float = 0.08,
        center_match_ratio: float = 0.55,
        max_missed: int = 18,
    ) -> None:
        self.pos_smooth = pos_smooth
        self.size_smooth = size_smooth
        self.iou_match = iou_match
        self.center_match_ratio = center_match_ratio
        self.max_missed = max_missed
        self._tracks: List[_Track] = []
        self._fw = 0
        self._fh = 0

    def _match_score(self, track: _Track, det: Box) -> float:
        iou = _iou(track.smooth, det)
        if iou >= self.iou_match:
            return iou + 0.5
        tw = track.smooth[2]
        dist = _center_dist(track.smooth, det)
        if tw > 0 and dist < tw * self.center_match_ratio:
            return 0.4 + iou
        return iou

    def _smooth_box(self, old: Box, new: Box) -> Box:
        ox, oy, ow, oh = old
        nx, ny, nw, nh = new
        ap, az = self.pos_smooth, self.size_smooth
        cx = int(ap * (nx + nw / 2) + (1 - ap) * (ox + ow / 2))
        cy = int(ap * (ny + nh / 2) + (1 - ap) * (oy + oh / 2))
        nw2 = int(az * nw + (1 - az) * ow)
        nh2 = int(az * nh + (1 - az) * oh)
        return _clamp_box(cx - nw2 // 2, cy - nh2 // 2, nw2, nh2, self._fw, self._fh)

    def update(self, detections: List[Box], frame_w: int, frame_h: int) -> List[Box]:
        self._fw, self._fh = frame_w, frame_h
        dets = [_clamp_box(*d, frame_w, frame_h) for d in detections]
        used = [False] * len(dets)

        for track in self._tracks:
            best_i, best_s = -1, 0.0
            for i, det in enumerate(dets):
                if used[i]:
                    continue
                s = self._match_score(track, det)
                if s > best_s:
                    best_s, best_i = s, i
            if best_i >= 0 and best_s >= 0.35:
                used[best_i] = True
                track.box = dets[best_i]
                track.smooth = self._smooth_box(track.smooth, track.box)
                track.missed = 0
                track.age += 1
            else:
                track.missed += 1

        for i, det in enumerate(dets):
            if not used[i]:
                t = _Track(box=det)
                t.smooth = det
                self._tracks.append(t)

        self._tracks = [t for t in self._tracks if t.missed <= self.max_missed]
        return [t.smooth for t in self._tracks]
```

## `apps/face-worker/cmir_face/worker.py`

```python
"""
Phase 0–1: video → face detect → eye black bars (or emoji) unless consented.

Usage:
  python -m cmir_face.worker --input demo.mp4 --output out.mp4
  python -m cmir_face.worker --input demo.mp4 --output out.mp4 \\
    --api-url http://localhost:8090 --poi-id <uuid>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from cmir_face.avatar_sprite import DEFAULT_OVERLAY_SCALE, EMOJI_IDS, get_sprite, overlay_sprite
from cmir_face.embeddings import (
    fetch_consented_faces_from_api,
    fetch_embeddings_from_api,
    load_embeddings_json,
    match_consented_face,
    patch_from_bbox,
    post_face_presence,
)
from cmir_face.eye_mask import (
    FaceBarTracker,
    bbox_from_detection,
    draw_eye_rects,
    draw_face_bar,
    draw_mask_image,
    eye_rects_from_detections,
    face_bars_from_detections,
)
from cmir_face.face_box import detections_to_boxes
from cmir_face.privacy_gate import PrivacyGate
from cmir_face.rtmp_writer import FfmpegRtmpWriter
from cmir_face.rtsp_capture import FfmpegRtspCapture
from cmir_face.tracker import FaceTracker


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cmir face worker POC")
    p.add_argument("--input", required=True, help="Input video path")
    p.add_argument(
        "--output",
        required=True,
        help="Output MP4 path or RTMP URL (rtmp://127.0.0.1:1935/gopro_avatar)",
    )
    p.add_argument("--consent-embeddings", default="", help="JSON file with embeddings")
    p.add_argument("--api-url", default="", help="Cmir API base URL")
    p.add_argument("--poi-id", default="", help="POI UUID for consent lookup")
    p.add_argument("--camera-id", default="", help="Camera UUID for face presence / airtime")
    p.add_argument(
        "--demo-fallback",
        action="store_true",
        help="If MediaPipe finds no face, use moving demo bbox (Phase 0 synthetic video)",
    )
    p.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (0=all)")
    p.add_argument("--consent-threshold", type=float, default=0.0, help="Match threshold override")
    p.add_argument(
        "--mask",
        default="eye-rect",
        choices=("eye-rect", "face-bar", "emoji"),
        help="Privacy mask: eye rectangles (default), face bar, or emoji sprite",
    )
    p.add_argument(
        "--emoji",
        default="stylized",
        choices=list(EMOJI_IDS),
        help="Emoji style when --mask emoji",
    )
    p.add_argument(
        "--track-smooth",
        type=float,
        default=0.55,
        help="Smoothing for eye bars / face box (higher = stickier)",
    )
    p.add_argument(
        "--overlay-scale",
        type=float,
        default=DEFAULT_OVERLAY_SCALE,
        help="Emoji size when --mask emoji",
    )
    p.add_argument("--mask-image", default="", help="PNG/JPG overlay instead of black mask")
    p.add_argument(
        "--output-delay-ms",
        type=int,
        default=300,
        help="Задержка выходного буфера (мс): кадр анализируется до публикации",
    )
    return p.parse_args()


def demo_bbox(frame_idx: int, total: int, w: int, h: int) -> tuple[int, int, int, int]:
    t = frame_idx / max(total - 1, 1)
    cx = int(w * (0.25 + 0.5 * t))
    cy = h // 2
    return cx - 55, cy - 70, 110, 140


def run(
    input_path: str,
    output_path: str,
    consent_path: str,
    api_url: str,
    poi_id: str,
    camera_id: str = "",
    demo_fallback: bool = False,
    max_frames: int = 0,
    consent_threshold: float = 0.0,
    mask_mode: str = "face-bar",
    emoji_id: str = "stylized",
    track_smooth: float = 0.55,
    overlay_scale: float = DEFAULT_OVERLAY_SCALE,
    mask_image_path: str = "",
    output_delay_ms: int = 900,
) -> int:
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        print("Install: pip install -r requirements.txt", file=sys.stderr)
        return 1

    consented_faces: list[dict] = []
    if consent_path:
        consented_faces = [{"embedding": e, "display_name": ""} for e in load_embeddings_json(consent_path)]
    elif api_url:
        consented_faces = fetch_consented_faces_from_api(api_url)

    def reload_consented() -> None:
        nonlocal consented_faces
        if api_url:
            fresh = fetch_consented_faces_from_api(api_url)
            if fresh:
                consented_faces = fresh

    is_rtsp = input_path.lower().startswith(("rtsp://", "rtsps://", "http://", "https://"))
    src = Path(input_path)
    if not is_rtsp and not src.is_file():
        print(f"Input not found: {src}", file=sys.stderr)
        return 1

    cap = None
    rtsp_cap: FfmpegRtspCapture | None = None
    if is_rtsp:
        print(f"Live input: {input_path} (max_frames={max_frames or 'unlimited'})")
        try:
            rtsp_cap = FfmpegRtspCapture(input_path)
            w, h, fps = rtsp_cap.width, rtsp_cap.height, rtsp_cap.fps
            print(f"RTSP via ffmpeg: {w}x{h} @ {fps:.1f} fps")
        except Exception as e:
            print(f"ffmpeg RTSP failed ({e}), trying OpenCV…", file=sys.stderr)
            rtsp_cap = None

    if rtsp_cap is None:
        if is_rtsp:
            import os

            os.environ.setdefault(
                "OPENCV_FFMPEG_CAPTURE_OPTIONS",
                "rtsp_transport;tcp|stimeout;5000000",
            )
            cap = cv2.VideoCapture(input_path, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                cap = cv2.VideoCapture(input_path)
        else:
            cap = cv2.VideoCapture(str(src))
        if not cap.isOpened():
            print(f"Cannot open: {input_path}", file=sys.stderr)
            return 1
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    else:
        cap = None

    match_threshold = consent_threshold if consent_threshold > 0 else 0.85

    mp_face = mp.solutions.face_detection
    # model 1 = full range (лучше для GoPro / средних дистанций)
    min_conf = 0.35
    detector = mp_face.FaceDetection(model_selection=1, min_detection_confidence=min_conf)

    use_emoji = mask_mode == "emoji"
    use_eye_rect = mask_mode == "eye-rect"
    face_tracker = FaceTracker(pos_smooth=track_smooth, size_smooth=max(0.22, track_smooth - 0.12))
    bar_tracker = FaceBarTracker(pos_smooth=track_smooth, size_smooth=max(0.25, track_smooth - 0.15))
    sprite = get_sprite(emoji_id, size=384) if use_emoji else None
    mask_img = None
    if mask_image_path:
        mask_img = cv2.imread(mask_image_path, cv2.IMREAD_UNCHANGED)
        if mask_img is not None:
            print(f"Custom mask image: {mask_image_path}")
    print(
        f"Mask: {mask_mode} | pos_smooth={track_smooth} | output_delay={output_delay_ms}ms"
        + (f" | emoji={emoji_id}" if use_emoji else "")
    )

    delay_frames = max(1, int(fps * output_delay_ms / 1000.0))
    privacy_gate = PrivacyGate(delay_frames=delay_frames, face_ttl=12, expand=1.2)
    fast_bar_tracker = FaceBarTracker(pos_smooth=0.35, size_smooth=0.3)
    presence_acc: dict[str, float] = {}
    frame_dt = 1.0 / max(fps, 1.0)

    def flush_presence() -> None:
        nonlocal presence_acc
        if not api_url or not camera_id or not presence_acc:
            presence_acc = {}
            return
        items = [
            {"user_id": uid, "camera_id": camera_id, "seconds": round(sec, 3)}
            for uid, sec in presence_acc.items()
            if sec > 0
        ]
        presence_acc = {}
        import os

        post_face_presence(api_url, camera_id, items, os.environ.get("CMIR_WORKER_TOKEN", ""))

    def draw_name_under_chin(out, fx: int, fy: int, fbw: int, fbh: int, name: str) -> None:
        import cv2

        if not name:
            return
        chin_y = fy + int(fbh * 0.92)
        cx = fx + fbw // 2
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.5, fbw / 240.0)
        thickness = max(1, int(scale * 2))
        (tw, th), baseline = cv2.getTextSize(name, font, scale, thickness)
        tx = max(0, min(cx - tw // 2, out.shape[1] - tw - 1))
        ty = min(out.shape[0] - 4, chin_y + th + 6)
        pad = 4
        cv2.rectangle(
            out,
            (tx - pad, ty - th - pad),
            (tx + tw + pad, ty + baseline + pad),
            (0, 0, 0),
            -1,
        )
        cv2.putText(out, name, (tx, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    def _draw_privacy_at_detection(out, det, fw: int, fh: int) -> None:
        fx, fy, fbw, fbh = bbox_from_detection(det, fw, fh)
        expanded = privacy_gate.expand_box(fx, fy, fbw, fbh, fw, fh)
        sig = patch_from_bbox(out, fx, fy, fbw, fbh)
        hit = match_consented_face(sig, consented_faces, threshold=match_threshold)
        matched_name = (hit or {}).get("display_name") or ""
        if hit and hit.get("user_id"):
            presence_acc[hit["user_id"]] = presence_acc.get(hit["user_id"], 0.0) + frame_dt
        if matched_name:
            nonlocal real_count
            real_count += 1
            draw_name_under_chin(out, fx, fy, fbw, fbh, matched_name)
            return
        nonlocal avatar_count
        avatar_count += 1
        if mask_img is not None:
            draw_mask_image(out, expanded, mask_img)
        elif use_eye_rect:
            draw_eye_rects(out, eye_rects_from_detections([det], fw, fh))
        elif use_emoji and sprite is not None:
            overlay_sprite(out, sprite, expanded, overlay_scale)
        else:
            draw_face_bar(out, expanded)

    def _draw_privacy_at_box(out, box: tuple[int, int, int, int]) -> None:
        nonlocal avatar_count
        avatar_count += 1
        if mask_img is not None:
            draw_mask_image(out, box, mask_img)
        elif use_eye_rect:
            draw_face_bar(out, box)
        elif use_emoji and sprite is not None:
            overlay_sprite(out, sprite, box, overlay_scale)
        else:
            draw_face_bar(out, box)

    def _center_near(cx: float, cy: float, centers: list[tuple[float, float]], fw: int) -> bool:
        thresh = fw * 0.12
        return any((cx - mx) ** 2 + (cy - my) ** 2 < thresh ** 2 for mx, my in centers)

    def apply_privacy_mask(frame: np.ndarray) -> np.ndarray:
        nonlocal avatar_count, real_count
        import cv2

        out = frame.copy()
        fh, fw = out.shape[:2]
        rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)
        dets = results.detections or []

        det_boxes = []
        for det in dets:
            fx, fy, fbw, fbh = bbox_from_detection(det, fw, fh)
            det_boxes.append(privacy_gate.expand_box(fx, fy, fbw, fbh, fw, fh))

        tracked_boxes = privacy_gate.update_tracks(det_boxes)
        masked_centers: list[tuple[float, float]] = []

        for det in dets:
            fx, fy, fbw, fbh = bbox_from_detection(det, fw, fh)
            _draw_privacy_at_detection(out, det, fw, fh)
            masked_centers.append((fx + fbw / 2, fy + fbh / 2))

        for box in tracked_boxes:
            bx, by, bw, bh = box
            cx, cy = bx + bw / 2, by + bh / 2
            if _center_near(cx, cy, masked_centers, fw):
                continue
            _draw_privacy_at_box(out, box)
            masked_centers.append((cx, cy))

        return out

    def write_frame(frame: np.ndarray) -> bool:
        if rtmp_writer is not None:
            return rtmp_writer.write(frame)
        if writer is not None:
            writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            return True
        return False

    frame_idx = 0
    avatar_count = 0
    real_count = 0
    if cap is not None:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    else:
        total_frames = max(max_frames, 1) if max_frames > 0 else 1

    is_rtmp_out = output_path.lower().startswith("rtmp://")
    writer = None
    rtmp_writer: FfmpegRtmpWriter | None = None
    if is_rtmp_out:
        rtmp_writer = FfmpegRtmpWriter(output_path, w, h, fps=fps)
        print(f"RTMP publish: {output_path}")
    else:
        try:
            import imageio

            writer = imageio.get_writer(output_path, fps=fps, codec="libx264")
        except Exception as e:
            print(f"Warning: streaming writer failed ({e})", file=sys.stderr)
            writer = None

    while True:
        if rtsp_cap is not None:
            ok, frame = rtsp_cap.read()
        else:
            ok, frame = cap.read()
        if not ok or frame is None:
            break

        for ready in privacy_gate.ingest(frame):
            masked = apply_privacy_mask(ready)
            if not write_frame(masked):
                print("RTMP writer stopped", file=sys.stderr)
                ok = False
                break

        if not ok:
            break

        frame_idx += 1
        if frame_idx % 150 == 0:
            reload_consented()
        if frame_idx % 30 == 0 and frame_idx > 0:
            flush_presence()
        if frame_idx % 90 == 0 and frame_idx > 0:
            print(f"  … {frame_idx} frames", flush=True)
        if max_frames > 0 and frame_idx >= max_frames:
            break

    flush_presence()
    for tail in privacy_gate.flush():
        masked = apply_privacy_mask(tail)
        write_frame(masked)

    if rtsp_cap is not None:
        rtsp_cap.release()
    elif cap is not None:
        cap.release()
    if rtmp_writer is not None:
        rtmp_writer.close()
    elif writer is not None:
        writer.close()
        if not Path(output_path).is_file():
            print(f"Failed to write video: {output_path}", file=sys.stderr)
            return 1
    else:
        print("No output writer", file=sys.stderr)
        return 1
    print(f"Processed {frame_idx} frames -> {output_path}")
    label = "masked" if not use_emoji else "avatars"
    print(f"Consented templates: {len(consented_faces)} | {label}: {avatar_count} | real: {real_count}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(
        run(
            args.input,
            args.output,
            args.consent_embeddings,
            args.api_url,
            args.poi_id,
            camera_id=getattr(args, "camera_id", "") or "",
            demo_fallback=args.demo_fallback,
            max_frames=args.max_frames,
            consent_threshold=args.consent_threshold,
            mask_mode=args.mask,
            emoji_id=args.emoji,
            track_smooth=args.track_smooth,
            overlay_scale=args.overlay_scale,
            mask_image_path=args.mask_image,
            output_delay_ms=args.output_delay_ms,
        )
    )


if __name__ == "__main__":
    main()
```

## `apps/face-worker/requirements.txt`

```text
# Cmir face-worker — Phase 0 POC
opencv-python-headless>=4.9.0
numpy>=1.26.0
mediapipe>=0.10.9
imageio>=2.34.0
imageio-ffmpeg>=0.5.0
Pillow>=10.0.0
```

## `apps/ingest/docker-compose.yml`

```yaml
# Cmir ingest — MediaMTX for lab / GoPro RTMP
# Usage: cd apps/ingest && docker compose up -d
services:
  mediamtx:
    image: bluenviron/mediamtx:latest
    container_name: cmir-mediamtx
    ports:
      - "1935:1935"   # RTMP ingest (GoPro Live / FFmpeg)
      - "8554:8554"   # RTSP read
      - "8888:8888"   # HLS
      - "9997:9997"   # API
    volumes:
      - ./mediamtx.yml:/mediamtx.yml:ro
    command: /mediamtx.yml
    restart: unless-stopped
```

## `apps/ingest/mediamtx.yml`

```yaml
# Cmir — MediaMTX (Phase 1)
# https://github.com/bluenviron/mediamtx

logLevel: info
api: yes
apiAddress: :9997

rtmp: yes
rtmpAddress: :1935

rtsp: yes
rtspAddress: :8554

hls: yes
hlsAddress: :8888
hlsAlwaysRemux: yes

paths:
  # Demo publishers (Phase 0)
  demo_general_a:
    source: publisher
  demo_general_b:
    source: publisher
  demo_consent:
    source: publisher

  # GoPro HERO13 / FFmpeg → RTMP publish to rtmp://HOST:1935/gopro_main
  gopro_main:
    source: publisher
    # Readers: rtsp://HOST:8554/gopro_main
    # HLS:     http://HOST:8888/gopro_main/index.m3u8

  gopro_consent:
    source: publisher

  # Face-worker → RTMP (live с аватарами)
  gopro_avatar:
    source: publisher
    # HLS: http://HOST:8888/gopro_avatar/index.m3u8

  # Динамические потоки мест (poi_*, poi_*_avatar) из local_relay
  "~^poi_":
    source: publisher
    overridePublisher: true

  all_others:
    source: publisher
    overridePublisher: true
```

## `apps/web/admin.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cmir — администрирование</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="css/app.css" />
  <script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.7"></script>
</head>
<body class="admin-page">
  <nav class="topnav">
    <h1>Cmir Admin <span class="env-badge" id="envBadge">test</span></h1>
    <span id="adminUserLabel" class="msg" style="margin:0 1rem"></span>
    <button type="button" class="tab-btn secondary" id="btnBack">← К сайту</button>
    <button type="button" class="tab-btn secondary" id="btnLogoutAdmin">Выйти</button>
  </nav>

  <div class="admin-tabs">
    <button type="button" class="tab-btn active" data-admin-tab="places">Места</button>
    <button type="button" class="tab-btn" data-admin-tab="users">Пользователи</button>
    <button type="button" class="tab-btn" data-admin-tab="quality">Качество сети</button>
    <button type="button" class="tab-btn" data-admin-tab="stats">Статистика</button>
  </div>

  <div id="panelPlaces" class="admin-tab-panel active">
    <div class="admin-layout">
      <div class="admin-map-wrap">
        <p class="map-hint" id="mapPickHint">Кликните на дом на карте, чтобы добавить место</p>
        <div id="adminMap" class="admin-map"></div>
      </div>
      <aside class="admin-side">
        <div class="admin-section">
          <h3>Место на карте</h3>
          <button type="button" class="primary" id="btnAddPoi" style="width:100%;margin-bottom:0.75rem">Добавить место</button>
          <label class="hint" for="poiSelect">Выберите место для редактирования</label>
          <select id="poiSelect"><option value="">— нет мест —</option></select>
          <input id="poiName" placeholder="Наименование" />
          <input id="poiAddress" placeholder="Адрес" />
          <button type="button" class="secondary" id="btnGeocode" style="width:100%;margin-bottom:0.5rem">Найти по адресу</button>
          <textarea id="poiComment" placeholder="Комментарий"></textarea>
          <input id="poiLat" placeholder="Широта" />
          <input id="poiLng" placeholder="Долгота" />
          <div class="row-btns">
            <button type="button" class="secondary" id="btnSavePoi">Сохранить место</button>
            <button type="button" class="secondary" id="btnDeletePoi" style="color:#ff8a80">Удалить</button>
          </div>
        </div>

        <div class="admin-section" id="camerasSection" style="display:none">
          <h3>Камеры места</h3>
          <p class="hint">До 5 USB-камер. Типы: общий план, согласие, перфоманс (интервью/стол)</p>
          <div id="cameraSlots"></div>
          <button type="button" class="secondary" id="btnAddCameraSlot" style="width:100%">+ Добавить камеру</button>
          <button type="button" class="primary" id="btnSaveCameras" style="width:100%;margin-top:0.5rem">Сохранить камеры</button>
        </div>

        <div class="admin-section preview-inactive" id="maskSection">
          <h3>Превью новой маски</h3>
          <p class="hint" id="maskCameraHint">Доступно при включённой рабочей камере</p>
          <div class="stream-sample">
            <video id="adminCameraPreview" muted playsinline></video>
            <canvas id="maskOverlayCanvas" class="mask-overlay-canvas"></canvas>
          </div>
          <input type="file" id="maskFile" accept="image/png,image/jpeg,image/webp" disabled />
          <div class="row-btns">
            <button type="button" class="primary" id="btnApplyMask" disabled>Применить к месту</button>
            <button type="button" class="secondary" id="btnRemoveMask" disabled>Убрать</button>
          </div>
        </div>
        <pre class="log" id="adminLog"></pre>
      </aside>
    </div>
  </div>

  <div id="panelUsers" class="admin-tab-panel admin-tab-panel--scroll">
    <div style="max-width:520px;margin:1rem auto;padding:0 1rem">
      <div class="admin-section">
        <h3>Пользователи</h3>
        <table class="users">
          <thead><tr><th>Email</th><th>Роль</th><th>Кошелёк UT</th><th>Блок</th></tr></thead>
          <tbody id="usersBody"></tbody>
        </table>
        <hr style="border-color:#2a3548;margin:0.75rem 0" />
        <input id="newUserEmail" placeholder="Email нового" />
        <input id="newUserName" placeholder="Имя" />
        <input id="newUserPass" type="password" placeholder="Пароль (8+)" />
        <select id="newUserRole"><option value="user">user</option><option value="admin">admin</option></select>
        <button type="button" class="secondary" id="btnAddUser" style="width:100%">Добавить</button>
        <hr style="border-color:#2a3548;margin:0.75rem 0" />
        <input id="editUserEmail" placeholder="Email" />
        <input id="editUserName" placeholder="Имя" />
        <input id="editUserPass" type="password" placeholder="Новый пароль" />
        <select id="editUserRole"><option value="user">user</option><option value="admin">admin</option></select>
        <input id="blockHours" type="number" value="24" />
        <div class="row-btns">
          <button type="button" class="secondary" id="btnSaveUser">Сохранить</button>
          <button type="button" class="secondary" id="btnBlockUser">Заблокировать</button>
          <button type="button" class="secondary" id="btnUnblockUser">Разблок.</button>
          <button type="button" class="secondary" id="btnDeleteUser" style="color:#ff8a80">Удалить</button>
        </div>
      </div>
    </div>
  </div>

  <div id="panelQuality" class="admin-tab-panel admin-tab-panel--scroll">
    <div class="admin-layout-quality">
      <div class="admin-section">
        <h3>Качество сигнала сети камер</h3>
        <button type="button" class="primary" id="btnCheckQuality">Проверить все камеры</button>
        <p class="quality-score" id="qualityScore">—</p>
        <p class="hint" id="qualityGrade"></p>
        <div id="qualityList"></div>
      </div>
    </div>
  </div>

  <div id="panelStats" class="admin-tab-panel admin-tab-panel--scroll">
    <div style="max-width:960px;margin:1rem auto;padding:0 1rem">
      <div class="admin-section">
        <h3>Аналитика системы</h3>
        <button type="button" class="primary" id="btnRefreshStats">Обновить отчёт</button>
        <div id="statsCards" class="stats-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0.75rem;margin-top:1rem"></div>
        <h4 style="margin-top:1.5rem">Камеры по типам</h4>
        <div id="statsCameras"></div>
        <h4 style="margin-top:1.5rem">Топ мест по согласиям</h4>
        <div id="statsTopPois"></div>
        <h4 style="margin-top:1.5rem">Качество сети (сводка)</h4>
        <p id="statsQuality"></p>
      </div>
    </div>
  </div>

  <div class="modal-backdrop" id="addPoiModal">
    <div class="modal" role="dialog">
      <h2 id="addPoiModalTitle">Новое место на карте</h2>
      <p class="hint" id="addPoiMapInfo" style="display:none"></p>
      <form id="formAddPoi">
        <input id="dlgPoiName" placeholder="Наименование" required />
        <input id="dlgPoiAddress" placeholder="Адрес" />
        <textarea id="dlgPoiComment" placeholder="Комментарий"></textarea>
        <input type="hidden" id="dlgPoiLat" />
        <input type="hidden" id="dlgPoiLng" />
        <div class="modal-actions">
          <button type="button" class="secondary" id="btnCancelAddPoi">Отмена</button>
          <button type="submit" class="primary">Добавить</button>
        </div>
      </form>
    </div>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script type="module">
    import { initAdmin } from "./js/admin.js";
    initAdmin().catch((e) => {
      console.error(e);
      alert("Ошибка загрузки админки: " + e.message);
    });
  </script>
</body>
</html>
```

## `apps/web/css/app.css`

```css
:root {
  --bg: #0a0e14;
  --panel: rgba(18, 24, 36, 0.88);
  --border: #2a3548;
  --text: #e8edf5;
  --muted: #8a96a8;
  --accent: #4d9fff;
  --accent2: #2d6a9f;
  --danger: #e74c3c;
  --nav-h: 52px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

a { color: var(--accent); text-decoration: none; }

/* --- User nav --- */
.topnav {
  height: var(--nav-h);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 1rem;
  background: #121a28;
  border-bottom: 1px solid var(--border);
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 1000;
}

.topnav h1 { font-size: 1.1rem; margin-right: auto; letter-spacing: 0.04em; }

.tab-btn {
  background: transparent;
  border: 1px solid transparent;
  color: var(--muted);
  padding: 0.45rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.tab-btn.active {
  color: var(--text);
  background: var(--accent2);
  border-color: #3d7ab8;
}

.tab-btn.admin-link {
  margin-left: 0.5rem;
  border-color: var(--border);
  color: var(--accent);
}

/* --- Views --- */
.view { display: none; min-height: calc(100vh - var(--nav-h)); }
.view.active { display: block; }

/* --- Map fullscreen --- */
#mapView {
  position: fixed;
  top: var(--nav-h);
  left: 0;
  right: 0;
  bottom: 0;
  padding-top: 0;
  min-height: 0;
}
#map { width: 100%; height: 100%; min-height: 240px; z-index: 1; }

.map-status {
  position: fixed;
  top: calc(var(--nav-h) + 0.75rem);
  left: 50%;
  transform: translateX(-50%);
  z-index: 1200;
  max-width: min(520px, calc(100% - 2rem));
  padding: 0.65rem 1rem;
  border-radius: 10px;
  background: rgba(20, 35, 56, 0.92);
  border: 1px solid var(--border);
  font-size: 0.85rem;
  text-align: center;
  pointer-events: none;
}
.map-status--err {
  background: rgba(42, 18, 18, 0.94);
  border-color: #8b3a3a;
  color: #ffb4b4;
}

#poiPanel {
  position: fixed;
  top: var(--nav-h);
  right: 0;
  width: 25%;
  min-width: 280px;
  max-width: 420px;
  height: calc(100vh - var(--nav-h));
  background: var(--panel);
  backdrop-filter: blur(10px);
  border-left: 1px solid var(--border);
  padding: 1rem;
  display: none;
  flex-direction: column;
  z-index: 900;
  overflow-y: auto;
}

#poiPanel.open { display: flex; }

#poiPanel h2 { font-size: 1rem; margin-bottom: 0.35rem; }
#poiPanel .addr { font-size: 0.8rem; color: var(--muted); margin-bottom: 0.75rem; }
#poiPanel .comment { font-size: 0.85rem; margin-bottom: 0.75rem; line-height: 1.4; }

.preview-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.preview-wrap video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

video.live-source-hidden {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  opacity: 0 !important;
  pointer-events: none;
  z-index: -1;
}

.privacy-composite .mask-overlay-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  background: #000;
}

.preview-wrap .mask-overlay-canvas,
.video-box .mask-overlay-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.panel-actions { display: flex; flex-direction: column; gap: 0.5rem; margin-top: auto; }

button.primary {
  background: var(--accent);
  color: #0a0e14;
  border: none;
  padding: 0.65rem 1rem;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}

button.secondary {
  background: #2a3548;
  color: var(--text);
  border: 1px solid var(--border);
  padding: 0.55rem 1rem;
  border-radius: 8px;
  cursor: pointer;
}

button.close-panel {
  align-self: flex-end;
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: 1.25rem;
  margin-bottom: 0.25rem;
}

/* --- Account --- */
#accountView {
  padding-top: var(--nav-h);
  max-width: 420px;
  margin: 0 auto;
  padding: calc(var(--nav-h) + 1rem) 1rem 2rem;
}

.auth-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.auth-tabs button {
  flex: 1;
  padding: 0.6rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #141c2a;
  color: var(--muted);
  cursor: pointer;
  font-weight: 600;
}

.auth-tabs button.active {
  background: var(--accent2);
  color: #fff;
  border-color: #3d7ab8;
}

form input {
  width: 100%;
  padding: 0.65rem;
  margin-bottom: 0.65rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #0f1419;
  color: var(--text);
}

.msg { font-size: 0.85rem; margin-top: 0.75rem; color: var(--muted); white-space: pre-wrap; }
.msg.error { color: #ff8a80; }
.msg.ok { color: #81c784; }

.user-card {
  background: #141c2a;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem;
}

.user-card p { margin-bottom: 0.5rem; font-size: 0.9rem; }
.profile-form label { display: block; font-size: 0.85rem; margin: 0.65rem 0 0.25rem; opacity: 0.9; }
.profile-form input,
.profile-form select { width: 100%; max-width: 360px; }

/* --- Admin --- */
.admin-page {
  padding-top: var(--nav-h);
  min-height: 100vh;
}

.admin-tabs {
  display: flex;
  gap: 0.35rem;
  padding: 0 1rem;
  background: #121a28;
  border-bottom: 1px solid var(--border);
  height: 48px;
  align-items: center;
  position: sticky;
  top: var(--nav-h);
  z-index: 950;
}

.admin-tabs .tab-btn {
  margin: 0;
  font-size: 0.9rem;
}

.admin-tab-panel {
  display: none;
  height: calc(100vh - var(--nav-h) - 48px);
  overflow: hidden;
}

.admin-tab-panel.active {
  display: block;
}

.admin-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  height: 100%;
  min-height: 0;
}

.admin-map-wrap {
  position: relative;
  height: 100%;
  min-height: 0;
}

.admin-map {
  height: 100%;
  min-height: 320px;
  width: 100%;
  background: #1a2332;
  z-index: 0;
}

.admin-map-wrap .map-hint {
  position: absolute;
  top: 0.75rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 500;
  background: rgba(18, 26, 40, 0.92);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.45rem 0.85rem;
  font-size: 0.8rem;
  color: var(--muted);
  pointer-events: none;
  white-space: nowrap;
}

.admin-map .leaflet-container {
  height: 100% !important;
  width: 100% !important;
  background: #1a2332;
}

.admin-side.is-readonly {
  opacity: 0.55;
}

.admin-side.is-readonly input:not([type="file"]),
.admin-side.is-readonly textarea,
.admin-side.is-readonly button:not(#btnAddPoi) {
  pointer-events: none;
}

.admin-tab-panel--scroll {
  height: calc(100vh - var(--nav-h) - 48px);
  overflow-y: auto;
  padding: 1rem 2rem;
  max-width: 560px;
  margin: 0 auto;
}

.admin-layout-quality {
  padding: 1rem 2rem;
  max-width: 900px;
  margin: 0 auto;
}

.admin-side {
  border-left: 1px solid var(--border);
  background: #121a28;
  overflow-y: auto;
  padding: 1rem;
}

.admin-section { margin-bottom: 1.5rem; }
.admin-section h3 {
  font-size: 0.9rem;
  color: var(--accent);
  margin-bottom: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.admin-side input, .admin-side select, .admin-side textarea {
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: #0f1419;
  color: var(--text);
  font-size: 0.85rem;
}

.admin-side textarea { min-height: 60px; resize: vertical; }

.row-btns { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.35rem; }

table.users {
  width: 100%;
  font-size: 0.75rem;
  border-collapse: collapse;
}

table.users th, table.users td {
  border-bottom: 1px solid var(--border);
  padding: 0.35rem 0.25rem;
  text-align: left;
}

table.users tr { cursor: pointer; }
table.users tr.selected { background: #1e2d44; }

.mask-preview {
  width: 100%;
  max-height: 120px;
  object-fit: contain;
  background: #000;
  border-radius: 8px;
  margin: 0.5rem 0;
}

.stream-sample {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #111;
  border-radius: 8px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.stream-sample video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.mask-overlay-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.admin-section.preview-inactive .stream-sample {
  opacity: 0.55;
}

.admin-section.preview-inactive input,
.admin-section.preview-inactive button {
  opacity: 1;
  pointer-events: auto;
}

.admin-section .hint {
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 0.5rem;
}

/* --- Modal --- */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-backdrop.open { display: flex; }

.modal {
  background: #141c2a;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.25rem;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
}

.modal h2 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
  color: var(--accent);
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

.log { font-size: 0.75rem; color: var(--muted); white-space: pre-wrap; max-height: 100px; overflow-y: auto; }

.quality-score {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--accent);
  margin: 0.5rem 0;
}

.camera-slot {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.65rem;
  margin-bottom: 0.5rem;
  background: #0f1419;
}

.camera-slot label {
  font-size: 0.8rem;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.35rem;
}

.camera-slot .slot-remove {
  margin-top: 0.5rem;
  width: 100%;
  font-size: 0.8rem;
  color: #ff8a80;
  background: transparent;
  border: 1px solid #5a3030;
  border-radius: 6px;
  padding: 0.35rem;
  cursor: pointer;
}

.env-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  background: #2a3548;
  color: var(--muted);
  margin-left: 0.5rem;
}
```

## `apps/web/index.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cmir — карта мест</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="css/app.css" />
  <script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.7"></script>
</head>
<body>
  <nav class="topnav">
    <h1>Cmir</h1>
    <button type="button" class="tab-btn active" data-view="map" id="tabMap">Карта</button>
    <button type="button" class="tab-btn" data-view="account" id="tabAccount">Аккаунт</button>
    <a href="admin.html" class="tab-btn admin-link" id="adminLink" style="display:none">Админ-панель</a>
    <a href="kiosk/index.html" class="tab-btn admin-link" id="kioskLink">Киоск согласия</a>
    <a href="performance.html" class="tab-btn admin-link" id="performanceLink">Перфоманс</a>
  </nav>

  <!-- Пользовательский контур: карта -->
  <section id="mapView" class="view active">
    <div id="map"></div>
    <div id="mapStatus" class="map-status" style="display:none" role="status"></div>
    <aside id="poiPanel">
      <button type="button" class="close-panel" id="closePanel" aria-label="Закрыть">×</button>
      <h2 id="panelTitle">Место</h2>
      <p class="addr" id="panelAddr"></p>
      <p class="comment" id="panelComment"></p>
      <div class="preview-wrap privacy-composite">
        <video id="previewVideo" class="live-source-hidden" muted playsinline autoplay></video>
        <canvas id="previewMaskCanvas" class="mask-overlay-canvas"></canvas>
      </div>
      <p class="addr" id="panelPreviewStatus"></p>
      <p class="addr">Превью: 10 с записи с эфира (зациклено, после старта потока)</p>
      <div class="panel-actions">
        <button type="button" class="primary" id="btnFullscreen">Открыть трансляцию на весь экран</button>
      </div>
    </aside>
  </section>

  <!-- Пользовательский контур: аккаунт -->
  <section id="accountView" class="view">
    <div id="authGuest">
      <div class="auth-tabs">
        <button type="button" class="active" data-auth="login">Вход</button>
        <button type="button" data-auth="register">Регистрация</button>
      </div>
      <form id="formLogin">
        <input name="email" type="text" placeholder="Email или телефон" required autocomplete="username" />
        <input name="password" type="password" placeholder="Пароль" required autocomplete="current-password" />
        <button type="submit" class="primary" style="width:100%">Войти</button>
      </form>
      <form id="formRegister" style="display:none">
        <input name="name" placeholder="Имя" />
        <input name="email" type="email" placeholder="Email" required />
        <input name="password" type="password" placeholder="Пароль (мин. 8)" required minlength="8" />
        <button type="submit" class="primary" style="width:100%">Зарегистрироваться</button>
      </form>
      <p class="hint">После киоска согласия вход — по телефону и выданному паролю.</p>
      <p class="msg" id="authMsg"></p>
    </div>
    <div id="authUser" class="user-card" style="display:none">
      <p id="authStatus"></p>
      <div id="consentsSection" class="profile-form">
        <h3 style="margin-top:0.5rem;font-size:1rem">Согласия на камерах</h3>
        <p class="hint">Отзыв согласия снова включает маску на вашем лице.</p>
        <div id="consentsList"></div>
      </div>
      <div id="airtimeSection" class="profile-form">
        <h3 style="margin-top:1rem;font-size:1rem">Время в кадре (UT)</h3>
        <p class="hint">Секунды на камерах за текущие периоды — доля от рекламы.</p>
        <div id="airtimeList"></div>
      </div>
      <form id="formProfile" class="profile-form">
        <p class="hint" id="profileFio"></p>
        <label for="profilePhone">Телефон</label>
        <input id="profilePhone" type="tel" autocomplete="tel" />
        <label for="profileEmail">Email</label>
        <input id="profileEmail" type="email" autocomplete="email" />
        <label for="profileMenu">Любимый пункт меню</label>
        <select id="profileMenu"><option value="">—</option></select>
        <button type="submit" class="primary" style="width:100%;margin-top:0.75rem">Сохранить профиль</button>
        <p class="msg" id="profileMsg"></p>
      </form>
      <div class="profile-form" id="platformsSection">
        <h3 style="margin-top:1rem;font-size:1rem">Платформы</h3>
        <p class="hint">Привяжите никнеймы YouTube, Twitch, Instagram, TikTok</p>
        <div id="platformLinks"></div>
        <label>Добавить / изменить</label>
        <select id="platformSelect">
          <option value="youtube">YouTube</option>
          <option value="twitch">Twitch</option>
          <option value="instagram">Instagram</option>
          <option value="tiktok">TikTok</option>
        </select>
        <input id="platformUsername" placeholder="Никнейм на платформе" style="margin-top:0.5rem" />
        <button type="button" class="secondary" id="btnLinkPlatform" style="width:100%;margin-top:0.5rem">Сохранить никнейм</button>
        <button type="button" class="secondary" id="btnOAuthPlatform" style="width:100%;margin-top:0.35rem">OAuth (полный доступ)</button>
      </div>
      <button type="button" class="secondary" id="btnLogout" style="margin-top:0.75rem">Выйти</button>
    </div>
  </section>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script type="module">
    import { initUser } from "./js/user.js";
    if (location.hash === "#account") {
      document.querySelector('.tab-btn[data-view="account"]').click();
    }
    initUser().catch((e) => {
      console.error(e);
      alert("Ошибка загрузки: " + e.message);
    });
  </script>
</body>
</html>
```

## `apps/web/js/admin.js`

```javascript
import { API, api, geocodeAddress, reverseGeocode, getToken, setToken, authHeaders } from "./api.js";
import { AdminMaskPreview } from "./mask-preview.js";

let map, markers = [], pois = [], selectedPoiId = null, selectedUserId = null;
let pendingMaskFile = null, adminHls = null, localPreviewStream = null;
let localDevices = [], cameraSlots = [], pickMarker = null, markerClickAt = 0;
let addPoiFromMap = false, maskPreview = null;

function log(msg) {
  const el = document.getElementById("adminLog");
  if (el) el.textContent = new Date().toLocaleTimeString() + " " + msg + "\n" + el.textContent;
}

function bindClick(id, handler) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Элемент #${id} не найден в admin.html`);
  el.onclick = handler;
}

function bindChange(id, handler) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Элемент #${id} не найден в admin.html`);
  el.onchange = handler;
}

function bindSubmit(id, handler) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Элемент #${id} не найден в admin.html`);
  el.onsubmit = handler;
}

function openModal(id) { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

async function guardAdmin() {
  const token = getToken();
  if (!token) { location.href = "index.html#account"; return false; }
  try {
    const me = await api("GET", "/api/v1/auth/me");
    if (me.data.role !== "admin") { alert("Нужны права администратора"); location.href = "index.html"; return false; }
    document.getElementById("adminUserLabel").textContent = me.data.email;
    return true;
  } catch {
    setToken(""); location.href = "index.html#account"; return false;
  }
}

function showAdminTab(name) {
  const panels = { places: "panelPlaces", users: "panelUsers", quality: "panelQuality", stats: "panelStats" };
  document.querySelectorAll("[data-admin-tab]").forEach((b) => {
    b.classList.toggle("active", b.dataset.adminTab === name);
  });
  document.querySelectorAll(".admin-tab-panel").forEach((p) => p.classList.remove("active"));
  document.getElementById(panels[name])?.classList.add("active");
  if (name === "places" && map) {
    setTimeout(() => map.invalidateSize(), 50);
    setTimeout(() => map.invalidateSize(), 300);
  }
  if (name === "stats") loadAdminStats().catch((e) => alert(e.message));
}

function requireSelectedPoi(actionLabel) {
  if (selectedPoiId) return true;
  alert(`Сначала выберите место в списке — без этого ${actionLabel} невозможно.`);
  return false;
}

function setPoiFormEditable(on) {
  document.querySelector(".admin-side")?.classList.toggle("is-readonly", !on);
  document.getElementById("btnGeocode").disabled = !on;
  document.getElementById("btnSavePoi").disabled = !on;
  document.getElementById("btnDeletePoi").disabled = !on;
}

function resolveDeviceId(cam) {
  if (!cam) return "";
  if (cam.device_id) return cam.device_id;
  if (cam.stream_url?.startsWith("local://")) return cam.stream_url.slice(8);
  return "";
}

function maskPreviewUrl() {
  if (pendingMaskFile) return URL.createObjectURL(pendingMaskFile);
  const poi = pois.find((p) => p.id === selectedPoiId);
  if (poi?.mask_image_url) return API + poi.mask_image_url + "?t=" + Date.now();
  return "";
}

function updateMaskPreview(url) {
  if (!maskPreview) return;
  const resolved = url !== undefined ? url : maskPreviewUrl();
  maskPreview.setMaskUrl(resolved);
  if (localPreviewStream || adminHls) maskPreview.start();
}

function initMap() {
  map = L.map("adminMap").setView([41.7151, 44.8271], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OSM" }).addTo(map);
  map.on("click", async (e) => {
    if (Date.now() - markerClickAt < 250) return;
    const { lat, lng } = e.latlng;
    try {
      const rev = await reverseGeocode(lat, lng);
      openAddPoiModal({
        fromMap: true,
        lat: rev.lat,
        lon: rev.lon,
        address: rev.display,
      });
      if (pickMarker) map.removeLayer(pickMarker);
      pickMarker = L.marker([rev.lat, rev.lon], {
        icon: L.divIcon({
          className: "",
          html: '<div style="background:#4d9fff;color:#fff;padding:4px 8px;border-radius:6px;font-size:11px">Новое место</div>',
          iconAnchor: [40, 10],
        }),
      }).addTo(map);
    } catch (err) {
      alert("Не удалось определить адрес по точке на карте: " + err.message);
    }
  });
}

function openAddPoiModal({ fromMap = false, lat = "", lon = "", address = "" } = {}) {
  addPoiFromMap = fromMap;
  document.getElementById("formAddPoi").reset();
  document.getElementById("dlgPoiLat").value = lat;
  document.getElementById("dlgPoiLng").value = lon;
  const addrEl = document.getElementById("dlgPoiAddress");
  const infoEl = document.getElementById("addPoiMapInfo");
  const titleEl = document.getElementById("addPoiModalTitle");
  if (fromMap) {
    titleEl.textContent = "Новое место с карты";
    addrEl.value = address;
    addrEl.readOnly = true;
    addrEl.required = false;
    infoEl.style.display = "block";
    infoEl.textContent = `Координаты: ${Number(lat).toFixed(5)}, ${Number(lon).toFixed(5)} · адрес с карты`;
  } else {
    titleEl.textContent = "Новое место по адресу";
    addrEl.readOnly = false;
    addrEl.required = true;
    infoEl.style.display = "none";
    infoEl.textContent = "";
  }
  openModal("addPoiModal");
}

function refreshPoiMarkers() {
  if (!map) return;
  markers.forEach((m) => map.removeLayer(m));
  markers = [];
  pois.forEach((poi) => {
    const m = L.marker([poi.latitude, poi.longitude], {
      icon: L.divIcon({
        className: "",
        html: `<div style="background:${poi.id === selectedPoiId ? "#4d9fff" : "#2d6a9f"};color:#fff;padding:4px 8px;border-radius:6px;font-size:11px">${poi.name}</div>`,
        iconAnchor: [20, 10],
      }),
    }).addTo(map).on("click", () => {
      markerClickAt = Date.now();
      selectPoi(poi.id);
    });
    markers.push(m);
  });
}

async function loadPois() {
  const res = await fetch(`${API}/api/v1/pois`);
  pois = (await res.json()).data || [];
  refreshPoiMarkers();
  const sel = document.getElementById("poiSelect");
  sel.innerHTML = '<option value="">— выберите место —</option>' +
    pois.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");
  if (selectedPoiId && pois.some((p) => p.id === selectedPoiId)) sel.value = selectedPoiId;
}

async function loadLocalDevices() {
  try {
    await navigator.mediaDevices.getUserMedia({ video: true }).then((s) => s.getTracks().forEach((t) => t.stop()));
  } catch (_) {}
  const all = await navigator.mediaDevices.enumerateDevices();
  localDevices = all.filter((d) => d.kind === "videoinput");
}

function stopCameraStreams() {
  maskPreview?.stop();
  if (adminHls) { adminHls.destroy(); adminHls = null; }
  if (localPreviewStream) { localPreviewStream.getTracks().forEach((t) => t.stop()); localPreviewStream = null; }
  const video = document.getElementById("adminCameraPreview");
  video.removeAttribute("src");
  video.srcObject = null;
}

function setMaskSectionEnabled(previewOn, hint = "") {
  const section = document.getElementById("maskSection");
  section.classList.toggle("preview-inactive", !previewOn);
  document.getElementById("maskCameraHint").textContent = previewOn
    ? "Рабочая камера активна — загрузите маску для превью"
    : hint || "Включите рабочую камеру у выбранного места";
  refreshMaskButtons();
}

function refreshMaskButtons() {
  const hasPoi = !!selectedPoiId;
  document.getElementById("maskFile").disabled = !hasPoi;
  document.getElementById("btnApplyMask").disabled = !hasPoi || !pendingMaskFile;
  document.getElementById("btnRemoveMask").disabled = !hasPoi;
}

function slotToPreviewCam(slot) {
  if (!slot) return null;
  return {
    id: slot.id,
    is_active: slot.is_active,
    is_preview: slot.is_preview,
    source_type: slot.device_id ? "local_usb" : (slot.source_type || "rtsp"),
    device_id: slot.device_id,
    stream_url: slot.device_id ? `local://${slot.device_id}` : (slot.stream_url || ""),
  };
}

function getPreviewSlotCamera() {
  const slot = cameraSlots.find((s) => s.is_preview && s.is_active);
  return slotToPreviewCam(slot);
}

async function refreshLocalPreview() {
  if (!selectedPoiId) return;
  updateMaskPreview();
  const cam = getPreviewSlotCamera();
  if (!cam) {
    stopCameraStreams();
    setMaskSectionEnabled(false, "Выберите рабочую включённую камеру");
    return;
  }
  const deviceId = resolveDeviceId(cam);
  if (!deviceId && (cam.source_type === "local_usb" || !cam.id)) {
    stopCameraStreams();
    setMaskSectionEnabled(false, "Выберите USB-камеру в списке");
    return;
  }
  await startCameraPreview({ ...cam, device_id: deviceId });
}

function showMaskOverlay(url) {
  updateMaskPreview(url);
}

async function startCameraPreview(cam) {
  stopCameraStreams();
  updateMaskPreview();
  if (!cam?.is_active) {
    setMaskSectionEnabled(false, "Отметьте камеру как включённую и рабочую");
    return;
  }
  const video = document.getElementById("adminCameraPreview");
  const deviceId = resolveDeviceId(cam);
  if (cam.source_type === "local_usb" || cam.stream_url?.startsWith("local://") || deviceId) {
    if (!deviceId) {
      setMaskSectionEnabled(false, "Выберите USB-камеру в списке");
      return;
    }
    try {
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } } });
      } catch (_) {
        stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId } });
      }
      localPreviewStream = stream;
      video.srcObject = stream;
      await video.play();
      if (!maskPreview?.ready) await maskPreview?.init();
      updateMaskPreview();
      maskPreview?.start();
      setMaskSectionEnabled(true);
    } catch (e) {
      setMaskSectionEnabled(false, "USB-камера недоступна: " + e.message);
    }
    return;
  }
  if (!cam.id) {
    setMaskSectionEnabled(false, "Сохраните камеры, чтобы открыть сетевой поток");
    return;
  }
  try {
    const pb = await api("GET", `/api/v1/cameras/${cam.id}/playback`);
    const url = pb.data.masked_hls_url || pb.data.hls_url;
    if (!url) throw new Error("нет HLS");
    if (window.Hls && Hls.isSupported()) {
      adminHls = new Hls({ lowLatencyMode: true });
      adminHls.loadSource(url);
      adminHls.attachMedia(video);
      adminHls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().then(async () => {
          if (!maskPreview?.ready) await maskPreview?.init();
          updateMaskPreview();
          maskPreview?.start();
          setMaskSectionEnabled(true);
        });
      });
    } else {
      video.src = url;
      await video.play();
      if (!maskPreview?.ready) await maskPreview?.init();
      updateMaskPreview();
      maskPreview?.start();
      setMaskSectionEnabled(true);
    }
  } catch (e) {
    setMaskSectionEnabled(false, "Поток недоступен");
  }
}

function buildCameraSlotsFromPoi(poi) {
  const cams = (poi?.cameras || []).slice().sort((a, b) => (a.slot_index ?? 0) - (b.slot_index ?? 0));
  if (!cams.length) {
    cameraSlots = [{ slot_index: 0, device_id: "", is_active: true, is_preview: true, name: "Камера 1", role: "general" }];
  } else {
    cameraSlots = cams.map((c, i) => ({
      id: c.id,
      slot_index: c.slot_index ?? i,
      device_id: resolveDeviceId(c),
      device_label: c.device_label || "",
      is_active: c.is_active,
      is_preview: c.is_preview,
      name: c.name,
      role: c.role || "general",
      source_type: c.source_type || (resolveDeviceId(c) ? "local_usb" : "rtsp"),
      stream_url: c.stream_url,
    }));
  }
  renderCameraSlots();
}

const CAMERA_ROLE_LABELS = {
  general: "Общий план",
  consent: "Согласие",
  performance: "Перфоманс",
};

function buildDeviceOptions(selectedId) {
  let opts = '<option value="">— выберите USB-камеру —</option>';
  const seen = new Set();
  for (const d of localDevices) {
    seen.add(d.deviceId);
    const sel = d.deviceId === selectedId ? " selected" : "";
    opts += `<option value="${d.deviceId}"${sel}>${d.label || "Камера"}</option>`;
  }
  if (selectedId && !seen.has(selectedId)) {
    opts += `<option value="${selectedId}" selected>Сохранённая (${selectedId.slice(0, 10)}…)</option>`;
  }
  return opts;
}

function renderCameraSlots() {
  const wrap = document.getElementById("cameraSlots");
  if (!wrap) return;
  wrap.innerHTML = cameraSlots.map((slot, i) => {
    const opts = buildDeviceOptions(slot.device_id || "");
    const role = slot.role || "general";
    const roleOpts = Object.entries(CAMERA_ROLE_LABELS).map(([v, label]) =>
      `<option value="${v}"${v === role ? " selected" : ""}>${label}</option>`,
    ).join("");
    const previewRow = role === "general"
      ? `<label><input type="radio" name="previewCam" class="slot-preview" value="${i}" ${slot.is_preview ? "checked" : ""} /> Рабочая (превью с маской)</label>`
      : "";
    return `
    <div class="camera-slot" data-slot="${i}">
      <strong>Камера ${i + 1}</strong>
      <label>Тип камеры
        <select class="slot-role">${roleOpts}</select>
      </label>
      <select class="slot-device">${opts}</select>
      <label><input type="checkbox" class="slot-active" ${slot.is_active ? "checked" : ""} /> Камера включена</label>
      ${previewRow}
      <button type="button" class="slot-remove" data-slot="${i}">Отвязать камеру</button>
    </div>`;
  }).join("");
  wrap.querySelectorAll(".camera-slot").forEach((el, i) => {
    const devSel = el.querySelector(".slot-device");
    if (devSel) {
      devSel.value = cameraSlots[i].device_id || "";
      devSel.onchange = (e) => {
        cameraSlots[i].device_id = e.target.value;
        cameraSlots[i].device_label = localDevices.find((d) => d.deviceId === e.target.value)?.label || "";
        cameraSlots[i].source_type = e.target.value ? "local_usb" : "rtsp";
        if (cameraSlots[i].is_preview) refreshLocalPreview();
      };
    }
    const roleSel = el.querySelector(".slot-role");
    if (roleSel) {
      roleSel.value = cameraSlots[i].role || "general";
      roleSel.onchange = (e) => {
        cameraSlots[i].role = e.target.value;
        if (e.target.value !== "general") cameraSlots[i].is_preview = false;
        renderCameraSlots();
      };
    }
    const activeCb = el.querySelector(".slot-active");
    if (activeCb) {
      activeCb.onchange = (e) => {
        cameraSlots[i].is_active = e.target.checked;
        if (cameraSlots[i].is_preview) refreshLocalPreview();
      };
    }
    const prev = el.querySelector(".slot-preview");
    if (prev) {
      prev.onchange = () => {
        cameraSlots.forEach((s, j) => { s.is_preview = j === i; });
        renderCameraSlots();
        refreshLocalPreview();
      };
    }
    const removeBtn = el.querySelector(".slot-remove");
    if (removeBtn) removeBtn.onclick = () => removeCameraSlot(i);
  });
}

async function removeCameraSlot(i) {
  if (!requireSelectedPoi("отвязку камеры")) return;
  const label = cameraSlots[i]?.name || `Камера ${i + 1}`;
  if (!confirm(`Отвязать «${label}» от этого места?`)) return;
  const wasPreview = cameraSlots[i]?.is_preview;
  cameraSlots.splice(i, 1);
  if (cameraSlots.length) {
    if (wasPreview || !cameraSlots.some((s) => s.is_preview)) cameraSlots[0].is_preview = true;
    renderCameraSlots();
    try {
      await saveCamerasAndPreview();
      log("Камера отвязана");
    } catch (e) { alert(e.message); }
  } else {
    try {
      await api("POST", `/api/v1/pois/${selectedPoiId}/cameras/sync`, { cameras: [] });
      await loadPois();
      buildCameraSlotsFromPoi(pois.find((p) => p.id === selectedPoiId));
      stopCameraStreams();
      setMaskSectionEnabled(false, "Нет камер — добавьте или выберите USB");
      log("Все камеры отвязаны");
    } catch (e) { alert(e.message); }
  }
}

function collectCameraPayload() {
  return cameraSlots.map((s, i) => {
    const deviceId = s.device_id || "";
    const dev = localDevices.find((d) => d.deviceId === deviceId);
    const role = s.role || "general";
    return {
      slot_index: i,
      device_id: deviceId,
      device_label: s.device_label || dev?.label || "",
      name: s.name || `Камера ${i + 1}`,
      role,
      source_type: deviceId ? "local_usb" : (s.source_type || "rtsp"),
      stream_url: deviceId ? `local://${deviceId}` : (s.stream_url || ""),
      is_active: s.is_active,
      is_preview: role === "general" ? s.is_preview : false,
    };
  });
}

async function saveCamerasAndPreview() {
  if (!selectedPoiId) return;
  const payload = collectCameraPayload();
  const preview = payload.find((c) => c.is_preview && c.is_active && c.role === "general" && (c.device_id || c.stream_url));
  if (!preview) {
    setMaskSectionEnabled(false, "Выберите рабочую камеру «общий план» с USB-устройством");
    throw new Error("Выберите рабочую камеру «общий план» с USB-устройством");
  }
  await api("POST", `/api/v1/pois/${selectedPoiId}/cameras/sync`, { cameras: payload });
  await loadPois();
  const poi = pois.find((p) => p.id === selectedPoiId);
  buildCameraSlotsFromPoi(poi);
  await refreshLocalPreview();
}

async function selectPoi(id) {
  stopCameraStreams();
  if (!id) {
    selectedPoiId = null;
    document.getElementById("camerasSection").style.display = "none";
    document.getElementById("maskSection").style.display = "none";
    setPoiFormEditable(false);
    maskPreview?.setMaskUrl("");
    maskPreview?.stop();
    refreshPoiMarkers();
    return;
  }
  selectedPoiId = id;
  const poi = pois.find((p) => p.id === id);
  if (!poi) return;
  setPoiFormEditable(true);
  document.getElementById("poiSelect").value = id;
  document.getElementById("poiName").value = poi.name;
  document.getElementById("poiAddress").value = poi.address || "";
  document.getElementById("poiComment").value = poi.comment || "";
  document.getElementById("poiLat").value = poi.latitude;
  document.getElementById("poiLng").value = poi.longitude;
  document.getElementById("camerasSection").style.display = "block";
  document.getElementById("maskSection").style.display = "block";
  pendingMaskFile = null;
  document.getElementById("maskFile").value = "";
  refreshMaskButtons();
  updateMaskPreview(poi.mask_image_url ? API + poi.mask_image_url + "?t=" + Date.now() : "");
  await loadLocalDevices();
  buildCameraSlotsFromPoi(poi);
  refreshPoiMarkers();
  map.setView([poi.latitude, poi.longitude], 15);
  await refreshLocalPreview();
}

async function loadUsers() {
  const res = await api("GET", "/api/v1/admin/users");
  const tbody = document.getElementById("usersBody");
  tbody.innerHTML = res.data.map((u) => {
    const ut = u.wallet ? u.wallet.balance_ut : "—";
    return `<tr data-id="${u.id}" class="${u.id === selectedUserId ? "selected" : ""}">
      <td>${u.email}</td><td>${u.role}</td><td>${ut}</td><td>${u.blocked_until ? "🔒" : "—"}</td></tr>`;
  }).join("");
  tbody.querySelectorAll("tr").forEach((tr) => {
    tr.onclick = () => {
      selectedUserId = tr.dataset.id;
      const u = res.data.find((x) => x.id === selectedUserId);
      document.getElementById("editUserEmail").value = u.email;
      document.getElementById("editUserName").value = u.display_name;
      document.getElementById("editUserRole").value = u.role;
      loadUsers();
    };
  });
}

async function checkNetworkQuality() {
  const data = (await api("GET", "/api/v1/admin/network-quality")).data;
  document.getElementById("qualityScore").textContent = data.aggregate_score + " / 100";
  document.getElementById("qualityGrade").textContent = `Оценка сети: ${data.grade} · камер: ${data.camera_count}`;
  document.getElementById("qualityList").innerHTML = (data.cameras || []).map((c) =>
    `<p class="hint">${c.name} (${CAMERA_ROLE_LABELS[c.role] || c.role}) @ ${c.poi_id?.slice(0, 8)}… — ${c.quality_score} (${c.status})</p>`
  ).join("") || "<p class='hint'>Нет активных камер</p>";
}

function statCard(title, value, sub = "") {
  return `<div class="admin-section" style="padding:0.75rem;text-align:center">
    <div style="font-size:1.6rem;font-weight:700">${value}</div>
    <div style="opacity:0.85">${title}</div>
    ${sub ? `<div class="hint" style="margin-top:0.25rem">${sub}</div>` : ""}
  </div>`;
}

async function loadAdminStats() {
  const s = (await api("GET", "/api/v1/admin/stats")).data;
  const byRole = s.cameras_by_role || {};
  document.getElementById("statsCards").innerHTML = [
    statCard("Пользователи", s.users_total),
    statCard("Профили", s.profiles_total),
    statCard("Кошельки", s.wallets_total, `ST: ${s.balance_st_total} · UT: ${s.balance_ut_total}`),
    statCard("Места (POI)", s.pois_total),
    statCard("Согласия", s.consents_active),
    statCard("Просмотр", `${Math.round(s.view_seconds_total)} с`),
    statCard("Перфоманс-стримы", s.performance_streams_total),
    statCard("Привязки подписи", s.signature_bindings_active),
  ].join("");
  document.getElementById("statsCameras").innerHTML = Object.entries(CAMERA_ROLE_LABELS).map(([role, label]) =>
    `<p class="hint">${label}: <strong>${byRole[role] || 0}</strong></p>`,
  ).join("");
  const tops = s.top_pois_consent || [];
  document.getElementById("statsTopPois").innerHTML = tops.length
    ? tops.map((p, i) => `<p class="hint">${i + 1}. ${p.name} — ${p.stats?.consent_rate_percent ?? "—"}%</p>`).join("")
    : "<p class='hint'>Нет данных</p>";
  const q = s.network_quality || {};
  document.getElementById("statsQuality").textContent =
    `Сводная оценка: ${q.aggregate_score ?? "—"} / 100 (${q.grade || "—"}), камер в мониторинге: ${q.camera_count ?? 0}`;
}

function bindEvents() {
  document.querySelectorAll("[data-admin-tab]").forEach((btn) => {
    btn.onclick = () => showAdminTab(btn.dataset.adminTab);
  });
  bindClick("btnBack", () => (location.href = "index.html"));
  bindClick("btnLogoutAdmin", async () => {
    try { await api("POST", "/api/v1/auth/logout", {}); } catch (_) {}
    setToken(""); location.href = "index.html";
  });
  bindChange("poiSelect", (e) => { selectPoi(e.target.value || null); });
  bindClick("btnAddPoi", () => openAddPoiModal({ fromMap: false }));
  bindClick("btnCancelAddPoi", () => {
    closeModal("addPoiModal");
    addPoiFromMap = false;
  });
  bindClick("addPoiModal", (e) => {
    if (e.target.id === "addPoiModal") {
      closeModal("addPoiModal");
      addPoiFromMap = false;
    }
  });
  bindSubmit("formAddPoi", async (e) => {
    e.preventDefault();
    const name = document.getElementById("dlgPoiName").value.trim();
    const comment = document.getElementById("dlgPoiComment").value.trim();
    if (!name) return alert("Укажите наименование");
    try {
      let lat, lon, address;
      if (addPoiFromMap) {
        lat = parseFloat(document.getElementById("dlgPoiLat").value);
        lon = parseFloat(document.getElementById("dlgPoiLng").value);
        address = document.getElementById("dlgPoiAddress").value.trim();
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) throw new Error("Некорректные координаты");
      } else {
        address = document.getElementById("dlgPoiAddress").value.trim();
        if (!address) return alert("Введите адрес");
        const g = await geocodeAddress(address);
        lat = g.lat;
        lon = g.lon;
        address = g.display || address;
      }
      const r = await api("POST", "/api/v1/pois", {
        name, address, comment, description: comment, poi_type: "live_cam",
        latitude: lat, longitude: lon, city: "", country: "",
      });
      closeModal("addPoiModal");
      addPoiFromMap = false;
      if (pickMarker) { map.removeLayer(pickMarker); pickMarker = null; }
      log("Место создано: " + name);
      await loadPois();
      selectPoi(r.data.id);
    } catch (err) { alert(err.message); }
  });
  bindClick("btnGeocode", async () => {
    if (!requireSelectedPoi("поиск по адресу")) return;
    const addr = document.getElementById("poiAddress").value.trim();
    if (!addr) return alert("Введите адрес");
    try {
      const g = await geocodeAddress(addr);
      document.getElementById("poiLat").value = g.lat;
      document.getElementById("poiLng").value = g.lon;
      if (g.display) document.getElementById("poiAddress").value = g.display;
      map.setView([g.lat, g.lon], 16);
      log("Координаты обновлены по адресу");
    } catch (e) { alert(e.message); }
  });
  bindClick("btnSavePoi", async () => {
    if (!requireSelectedPoi("сохранение")) return;
    try {
      await api("PATCH", `/api/v1/pois/${selectedPoiId}`, {
        name: document.getElementById("poiName").value,
        address: document.getElementById("poiAddress").value,
        comment: document.getElementById("poiComment").value,
        latitude: parseFloat(document.getElementById("poiLat").value),
        longitude: parseFloat(document.getElementById("poiLng").value),
      });
      log("Место сохранено");
      await loadPois();
    } catch (e) { alert(e.message); }
  });
  bindClick("btnDeletePoi", async () => {
    if (!requireSelectedPoi("удаление")) return;
    if (!confirm("Удалить место?")) return;
    await api("DELETE", `/api/v1/pois/${selectedPoiId}`);
    selectedPoiId = null;
    await loadPois();
    document.getElementById("camerasSection").style.display = "none";
    document.getElementById("maskSection").style.display = "none";
    setPoiFormEditable(false);
    stopCameraStreams();
  });
  bindClick("btnAddCameraSlot", () => {
    if (!requireSelectedPoi("добавление камеры")) return;
    if (cameraSlots.length >= 5) return alert("Максимум 5 камер");
    cameraSlots.push({
      slot_index: cameraSlots.length,
      device_id: "",
      is_active: false,
      is_preview: false,
      role: "general",
      name: `Камера ${cameraSlots.length + 1}`,
    });
    renderCameraSlots();
  });
  bindClick("btnSaveCameras", async () => {
    if (!requireSelectedPoi("сохранение камер")) return;
    try {
      await saveCamerasAndPreview();
      log("Камеры сохранены");
    } catch (e) { alert(e.message); }
  });
  bindChange("maskFile", (e) => {
    const f = e.target.files[0];
    if (!f) return;
    pendingMaskFile = f;
    updateMaskPreview(URL.createObjectURL(f));
    refreshMaskButtons();
    if (localPreviewStream || adminHls) maskPreview?.start();
  });
  bindClick("btnApplyMask", async () => {
    if (!requireSelectedPoi("применение маски")) return;
    if (!pendingMaskFile) return alert("Сначала выберите файл маски");
    try {
      const fd = new FormData();
      fd.append("image", pendingMaskFile, pendingMaskFile.name || "mask.png");
      const res = await fetch(`${API}/api/v1/pois/${selectedPoiId}/mask-image`, {
        method: "POST",
        headers: authHeaders(),
        body: fd,
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || json.success === false) throw new Error(json.error || "Не удалось применить маску");
      pendingMaskFile = null;
      document.getElementById("maskFile").value = "";
      refreshMaskButtons();
      await loadPois();
      await selectPoi(selectedPoiId);
      log("Маска применена к месту");
    } catch (e) {
      alert(e.message);
    }
  });
  bindClick("btnRemoveMask", async () => {
    if (!requireSelectedPoi("удаление маски")) return;
    try {
      await api("DELETE", `/api/v1/pois/${selectedPoiId}/mask-image`);
      pendingMaskFile = null;
      document.getElementById("maskFile").value = "";
      refreshMaskButtons();
      await loadPois();
      await selectPoi(selectedPoiId);
      log("Маска убрана — чёрная плашка");
    } catch (e) {
      alert(e.message);
    }
  });
  bindClick("btnCheckQuality", checkNetworkQuality);
  bindClick("btnRefreshStats", () => loadAdminStats().catch((e) => alert(e.message)));
  bindClick("btnAddUser", async () => {
    try {
      await api("POST", "/api/v1/admin/users", {
        email: document.getElementById("newUserEmail").value,
        password: document.getElementById("newUserPass").value,
        display_name: document.getElementById("newUserName").value,
        role: document.getElementById("newUserRole").value,
      });
      loadUsers();
    } catch (e) { alert(e.message); }
  });
  bindClick("btnSaveUser", async () => {
    if (!selectedUserId) return;
    const body = { email: document.getElementById("editUserEmail").value, display_name: document.getElementById("editUserName").value, role: document.getElementById("editUserRole").value };
    const pw = document.getElementById("editUserPass").value;
    if (pw) body.password = pw;
    await api("PATCH", `/api/v1/admin/users/${selectedUserId}`, body);
    loadUsers();
  });
  bindClick("btnBlockUser", async () => {
    if (!selectedUserId) return;
    await api("POST", `/api/v1/admin/users/${selectedUserId}/block`, { hours: parseFloat(document.getElementById("blockHours").value) || 24 });
    loadUsers();
  });
  bindClick("btnUnblockUser", async () => {
    if (!selectedUserId) return;
    await api("POST", `/api/v1/admin/users/${selectedUserId}/unblock`, {});
    loadUsers();
  });
  bindClick("btnDeleteUser", async () => {
    if (!selectedUserId || !confirm("Удалить?")) return;
    await api("DELETE", `/api/v1/admin/users/${selectedUserId}`);
    selectedUserId = null;
    loadUsers();
  });
}

export async function initAdmin() {
  if (!(await guardAdmin())) return;
  bindEvents();
  const video = document.getElementById("adminCameraPreview");
  const canvas = document.getElementById("maskOverlayCanvas");
  if (!video || !canvas) throw new Error("Превью камеры (#adminCameraPreview / #maskOverlayCanvas) не найдено");
  maskPreview = new AdminMaskPreview(video, canvas);
  maskPreview.init().catch((e) => console.warn("mask preview init", e));
  setPoiFormEditable(false);
  initMap();
  const h = await fetch(`${API}/health`).then((r) => r.json());
  document.getElementById("envBadge").textContent = h.environment || "test";
  await loadLocalDevices();
  await loadPois();
  try { await loadUsers(); } catch (_) {}
  setMaskSectionEnabled(false);
  setTimeout(() => map?.invalidateSize(), 100);
  setTimeout(() => map?.invalidateSize(), 500);
  if (!pois.length) log("Нет мест — кликните на карту или «Добавить место»");
  else if (pois.length === 1) await selectPoi(pois[0].id);
}
```

## `apps/web/js/api.js`

```javascript
export const API = localStorage.getItem("cmir_api") || "http://localhost:8090";

export function getToken() {
  return localStorage.getItem("cmir_token") || "";
}

export function setToken(t) {
  if (t) localStorage.setItem("cmir_token", t);
  else {
    localStorage.removeItem("cmir_token");
    localStorage.removeItem("cmir_user");
  }
}

export function authHeaders(extra = {}) {
  const h = { ...extra };
  const t = getToken();
  if (t) h.Authorization = "Bearer " + t;
  return h;
}

export async function api(method, path, body, isForm = false) {
  const opts = { method, headers: authHeaders() };
  if (body !== undefined) {
    if (isForm) {
      opts.body = body;
    } else {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(API + path, opts);
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || res.statusText);
  return json;
}

export async function geocodeAddress(address) {
  const q = encodeURIComponent(address);
  const res = await fetch(`${API}/api/v1/geocode?q=${q}`);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Адрес не найден");
  return {
    lat: json.data.lat,
    lon: json.data.lon,
    display: json.data.display_name,
  };
}

export async function reverseGeocode(lat, lon) {
  const res = await fetch(`${API}/api/v1/reverse-geocode?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Не удалось определить адрес");
  return {
    lat: json.data.lat,
    lon: json.data.lon,
    display: json.data.display_name,
    street: json.data.street || "",
    building: json.data.building || "",
  };
}
```

## `apps/web/js/face-enroll.js`

```javascript
/**
 * Guided multi-pose face enrollment for Cmir consent kiosk.
 * Poses: center → left → right → up → down (MediaPipe Face Landmarker yaw/pitch).
 */
export const ENROLL_POSES = [
  { id: "center", title: "Смотрите прямо в камеру", yaw: [ -12, 12], pitch: [-12, 12] },
  { id: "left", title: "Поверните голову влево", yaw: [ 18, 55], pitch: [-18, 18] },
  { id: "right", title: "Поверните голову вправо", yaw: [-55,-18], pitch: [-18, 18] },
  { id: "up", title: "Поднимите подбородок вверх", yaw: [-18, 18], pitch: [-45,-14] },
  { id: "down", title: "Опустите подбородок вниз", yaw: [-18, 18], pitch: [ 14, 45] },
];

export function poseInRange(yaw, pitch, step) {
  const [y0, y1] = step.yaw;
  const [p0, p1] = step.pitch;
  return yaw >= y0 && yaw <= y1 && pitch >= p0 && pitch <= p1;
}

/** Approximate yaw/pitch (degrees) from Face Landmarker facialTransformationMatrix. */
export function yawPitchFromMatrix(matrixData) {
  if (!matrixData || matrixData.length < 16) return { yaw: 0, pitch: 0, roll: 0 };
  // column-major 4x4
  const r00 = matrixData[0];
  const r10 = matrixData[1];
  const r20 = matrixData[2];
  const r21 = matrixData[6];
  const r22 = matrixData[10];
  const pitch = Math.atan2(-r21, r22) * (180 / Math.PI);
  const yaw = Math.atan2(r20, Math.sqrt(r00 * r00 + r10 * r10)) * (180 / Math.PI);
  const roll = Math.atan2(r10, r00) * (180 / Math.PI);
  return { yaw, pitch, roll };
}

/** Fallback yaw/pitch from face bbox position in frame (no landmarker). */
export function yawPitchFromBbox(bbox, videoW, videoH) {
  if (!bbox || !videoW || !videoH) return { yaw: 0, pitch: 0 };
  const norm = bbox.originX <= 1;
  const cx = (norm ? bbox.originX + bbox.width / 2 : bbox.originX + bbox.width / 2) / (norm ? 1 : videoW);
  const cy = (norm ? bbox.originY + bbox.height / 2 : bbox.originY + bbox.height / 2) / (norm ? 1 : videoH);
  const yaw = (0.5 - cx) * 80;
  const pitch = (cy - 0.5) * 70;
  return { yaw, pitch };
}

export class PoseEnrollment {
  constructor({ onStatus, captureSignature, getPose }) {
    this.onStatus = onStatus || (() => {});
    this.captureSignature = captureSignature;
    this.getPose = getPose;
    this.templates = [];
    this.stepIndex = 0;
    this.stableFrames = 0;
    this.running = false;
  }

  get current() {
    return ENROLL_POSES[this.stepIndex] || null;
  }

  get done() {
    return this.templates.length >= ENROLL_POSES.length;
  }

  reset() {
    this.templates = [];
    this.stepIndex = 0;
    this.stableFrames = 0;
    this.running = false;
  }

  async run() {
    this.reset();
    this.running = true;
    while (this.running && this.stepIndex < ENROLL_POSES.length) {
      const step = this.current;
      this.onStatus(`Шаг ${this.stepIndex + 1}/${ENROLL_POSES.length}: ${step.title}`);
      this.stableFrames = 0;
      // wait until pose held ~0.7s
      // eslint-disable-next-line no-await-in-loop
      await this._waitPose(step);
      if (!this.running) break;
      const sig = this.captureSignature();
      if (!sig) {
        this.onStatus("Лицо не видно — повторите позу");
        // eslint-disable-next-line no-await-in-loop
        await sleep(600);
        continue;
      }
      const pose = this.getPose() || { yaw: 0, pitch: 0 };
      this.templates.push({
        pose: step.id,
        embedding: sig,
        yaw: pose.yaw,
        pitch: pose.pitch,
      });
      this.stepIndex += 1;
      this.onStatus(`✓ ${step.title}`);
      // eslint-disable-next-line no-await-in-loop
      await sleep(350);
    }
    this.running = false;
    return this.templates;
  }

  stop() {
    this.running = false;
  }

  async _waitPose(step) {
    const need = 8;
    const started = Date.now();
    const timeoutMs = 9000;
    while (this.running && this.stableFrames < need) {
      const pose = this.getPose();
      const timedOut = Date.now() - started > timeoutMs;
      if ((pose && poseInRange(pose.yaw, pose.pitch, step)) || timedOut) {
        this.stableFrames += 1;
        this.onStatus(
          timedOut
            ? `Шаг ${this.stepIndex + 1}/${ENROLL_POSES.length}: держите лицо в кадре… ${this.stableFrames}/${need}`
            : `Шаг ${this.stepIndex + 1}/${ENROLL_POSES.length}: ${step.title}… ${this.stableFrames}/${need}`,
        );
      } else {
        this.stableFrames = Math.max(0, this.stableFrames - 2);
        this.onStatus(`Шаг ${this.stepIndex + 1}/${ENROLL_POSES.length}: ${step.title}`);
      }
      // eslint-disable-next-line no-await-in-loop
      await sleep(70);
    }
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
```

## `apps/web/js/live-camera.js`

```javascript
/**
 * Мгновенный локальный поток USB + маски/подписи как в админ-превью.
 */
import {
  coverTransform,
  drawNameUnderChin,
  drawOrientedOverlay,
  poseFromDetection,
  smoothPose,
} from "./mask-preview.js";

const PATCH = 32;
const MATCH_THRESHOLD = 0.82;
const MATCH_HOLD_THRESHOLD = 0.75; // hysteresis while already matched
const DETECT_INTERVAL_MS = 33;
const MIN_MASK_CONFIRM_FRAMES = 2;
const SIG_BLEND = 0.35;
const CONSENT_HOLD_FRAMES = 20;
const FACE_MATCH_INTERVAL_MS = 400;

function deviceIdFromCamera(cam) {
  if (cam?.device_id) return cam.device_id;
  const url = cam?.stream_url || "";
  if (url.startsWith("local://")) return url.slice(8);
  return "";
}

function cosine(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}

function authHeaders(extra = {}) {
  const h = { ...extra };
  const t = localStorage.getItem("cmir_token") || "";
  if (t) h.Authorization = "Bearer " + t;
  return h;
}

function currentUserId() {
  try {
    const raw = localStorage.getItem("cmir_user");
    if (!raw) return "";
    return JSON.parse(raw)?.id || "";
  } catch (_) {
    return "";
  }
}

/** Фильтр ложных срабатываний (руки и т.п.) — только похожие на лицо bbox. */
export function isLikelyFaceDetection(d, vw, vh) {
  const bb = d.boundingBox;
  if (!bb || !vw || !vh) return false;
  const norm = bb.originX <= 1 && bb.originY <= 1 && bb.width <= 1;
  const x = norm ? bb.originX * vw : bb.originX;
  const y = norm ? bb.originY * vh : bb.originY;
  const w = norm ? bb.width * vw : bb.width;
  const h = norm ? bb.height * vh : bb.height;
  if (w < 56 || h < 56) return false;
  if (w > vw * 0.42 || h > vh * 0.48) return false;
  const ar = w / h;
  if (ar < 0.68 || ar > 1.32) return false;
  const area = (w * h) / (vw * vh);
  if (area < 0.005 || area > 0.28) return false;

  const kps = d.keypoints;
  if (!kps || kps.length < 3) return false;
  const rx = kps[0].x <= 1 ? kps[0].x * vw : kps[0].x;
  const ry = kps[0].y <= 1 ? kps[0].y * vh : kps[0].y;
  const lx = kps[1].x <= 1 ? kps[1].x * vw : kps[1].x;
  const ly = kps[1].y <= 1 ? kps[1].y * vh : kps[1].y;
  const ny = kps[2].y <= 1 ? kps[2].y * vh : kps[2].y;
  const eyeDist = Math.hypot(lx - rx, ly - ry);
  if (eyeDist < 30 || eyeDist > Math.min(vw, vh) * 0.34) return false;
  const eyeMidY = (ry + ly) / 2;
  if (ny < eyeMidY - 6) return false;
  if (ny > eyeMidY + h * 0.55) return false;
  const cx = (rx + lx) / 2;
  const bbCx = x + w / 2;
  if (Math.abs(cx - bbCx) > w * 0.28) return false;
  if (eyeMidY < y + h * 0.12 || eyeMidY > y + h * 0.58) return false;
  return true;
}

function blendSignature(prev, next) {
  if (!next) return prev;
  if (!prev) return next;
  return prev.map((v, i) => v * (1 - SIG_BLEND) + next[i] * SIG_BLEND);
}

export function signatureFromVideo(video, bbox) {
  const vw = video.videoWidth;
  const vh = video.videoHeight;
  if (!vw || !vh || !bbox) return null;
  const norm = bbox.originX <= 1 && bbox.originY <= 1;
  let x = norm ? bbox.originX * vw : bbox.originX;
  let y = norm ? bbox.originY * vh : bbox.originY;
  let w = norm ? bbox.width * vw : bbox.width;
  let h = norm ? bbox.height * vh : bbox.height;
  x = Math.max(0, x);
  y = Math.max(0, y);
  w = Math.min(w, vw - x);
  h = Math.min(h, vh - y);
  if (w < 8 || h < 8) return null;
  const canvas = document.createElement("canvas");
  canvas.width = PATCH;
  canvas.height = PATCH;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, x, y, w, h, 0, 0, PATCH, PATCH);
  const img = ctx.getImageData(0, 0, PATCH, PATCH);
  const gray = new Float32Array(PATCH * PATCH);
  let minV = 1;
  let maxV = 0;
  for (let i = 0; i < PATCH * PATCH; i++) {
    const o = i * 4;
    const v = (img.data[o] + img.data[o + 1] + img.data[o + 2]) / (3 * 255);
    gray[i] = v;
    if (v < minV) minV = v;
    if (v > maxV) maxV = v;
  }
  const span = Math.max(1e-6, maxV - minV);
  for (let i = 0; i < gray.length; i++) gray[i] = (gray[i] - minV) / span;
  let normV = 0;
  for (let i = 0; i < gray.length; i++) normV += gray[i] * gray[i];
  normV = Math.sqrt(normV) || 1;
  return Array.from(gray, (v) => v / normV);
}

let devicesCache = null;
let devicesCacheAt = 0;

export async function ensureCameraPermission() {
  if (!navigator.mediaDevices?.getUserMedia) return false;
  try {
    const s = await navigator.mediaDevices.getUserMedia({ video: true });
    s.getTracks().forEach((t) => t.stop());
    return true;
  } catch (_) {
    return false;
  }
}

async function enumerateVideoDevices() {
  const now = Date.now();
  if (devicesCache && now - devicesCacheAt < 5000) return devicesCache;
  await ensureCameraPermission();
  if (!navigator.mediaDevices?.enumerateDevices) return [];
  const all = await navigator.mediaDevices.enumerateDevices();
  devicesCache = all.filter((d) => d.kind === "videoinput");
  devicesCacheAt = now;
  return devicesCache;
}

function matchDeviceId(savedId, devices) {
  if (!savedId) return "";
  if (devices.some((d) => d.deviceId === savedId)) return savedId;
  return savedId;
}

/** Синхронный fallback (без enumerateDevices). */
export function resolveUsbDeviceId(cam) {
  return deviceIdFromCamera(cam);
}

function deviceScore(label) {
  const l = (label || "").toLowerCase();
  if (/gopro/.test(l)) return 100;
  if (/obs|virtual|continuity|iphone|blackhole|capture screen/.test(l)) return -1;
  if (/facetime|built-in|встроенн/.test(l)) return 50;
  if (/webcam|usb|camera|камер/.test(l)) return 40;
  return 10;
}

/** GoPro если есть, иначе обычная веб-камера (не virtual/Continuity). */
export function pickPreferredVideoDevice(devices) {
  if (!devices?.length) return null;
  const ranked = devices
    .map((d) => ({ d, s: deviceScore(d.label) }))
    .filter((x) => x.s >= 0)
    .sort((a, b) => b.s - a.s || 0);
  return ranked[0]?.d || devices[0] || null;
}

/**
 * Разрешает USB deviceId: запрашивает доступ к камере, сверяет с сохранённым id,
 * при необходимости берёт другую активную камеру того же POI или единственную USB.
 * Если GoPro нет — заглушка: встроенная / USB веб-камера.
 */
export async function resolveUsbDeviceIdAsync(cam, fallbackCams = []) {
  const candidates = [cam, ...fallbackCams].filter(Boolean);
  const devices = await enumerateVideoDevices();

  for (const c of candidates) {
    const id = deviceIdFromCamera(c);
    if (!id) continue;
    const matched = matchDeviceId(id, devices);
    if (matched && devices.some((d) => d.deviceId === matched)) return matched;
  }

  for (const c of candidates) {
    const label = (c.device_label || c.name || "").trim().toLowerCase();
    if (!label) continue;
    const byLabel = devices.find((d) => (d.label || "").toLowerCase().includes(label));
    if (byLabel?.deviceId) return byLabel.deviceId;
  }

  // Явный GoPro в конфиге, но устройства нет → stub webcam
  const wantsGopro = candidates.some((c) =>
    /gopro/i.test(`${c.device_label || ""} ${c.name || ""}`),
  );
  if (wantsGopro) {
    const stub = pickPreferredVideoDevice(devices.filter((d) => !/gopro/i.test(d.label || "")));
    if (stub?.deviceId) return stub.deviceId;
  }

  const saved = deviceIdFromCamera(cam);
  if (saved && devices.some((d) => d.deviceId === saved)) return saved;

  const wantsUsb = candidates.some((c) => c.is_active && (c.source_type === "local_usb" || deviceIdFromCamera(c)));
  if (wantsUsb && devices.length) {
    const pref = pickPreferredVideoDevice(devices);
    return pref?.deviceId || "";
  }

  return "";
}

export class LiveCameraView {
  constructor(videoEl, canvasEl) {
    this.video = videoEl;
    this.canvas = canvasEl;
    if (!canvasEl) throw new Error("Canvas для маски не найден");
    this.ctx = canvasEl.getContext("2d");
    this.detector = null;
    this.maskImg = null;
    this.stream = null;
    this.running = false;
    this.raf = 0;
    this.lastTs = 0;
    this.faceSmooth = new Map();
    this.matchCache = new Map(); // trackKey → { user_id, display_name, at, pending }
    this.apiBase = "";
    this.ready = false;
    this.compositeMode = true;
    this.onRecognized = null;
    this.cameraId = "";
    this.presenceAcc = new Map();
    this.presenceTimer = null;
    this.lastFaceBbox = null;
    this.privacyReady = false;
    this.firstDetectDone = false;
  }

  async init() {
    if (this.ready) return;
    const { FaceDetector, FilesetResolver } = await import(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14"
    );
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm",
    );
    this.detector = await FaceDetector.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
      },
      runningMode: "VIDEO",
      minDetectionConfidence: 0.58,
    });
    this.ready = true;
  }

  /** Server-side match — gallery never downloaded to the browser. */
  requestFaceMatch(trackKey, sig, priorUserId) {
    if (!this.apiBase || !sig) return;
    const cached = this.matchCache.get(trackKey);
    const now = performance.now();
    if (cached?.pending) return;
    if (cached && now - cached.at < FACE_MATCH_INTERVAL_MS) return;
    this.matchCache.set(trackKey, {
      ...(cached || {}),
      pending: true,
      at: now,
    });
    fetch(`${this.apiBase}/api/v1/face-match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        embedding: sig,
        prior_user_id: priorUserId || "",
      }),
    })
      .then((r) => r.json())
      .then((json) => {
        const data = json.data || {};
        this.matchCache.set(trackKey, {
          user_id: data.matched ? data.user_id : null,
          display_name: data.matched ? data.display_name || "" : null,
          at: performance.now(),
          pending: false,
        });
      })
      .catch(() => {
        const prev = this.matchCache.get(trackKey) || {};
        this.matchCache.set(trackKey, { ...prev, pending: false, at: performance.now() });
      });
  }

  cachedMatch(trackKey) {
    const c = this.matchCache.get(trackKey);
    if (!c?.user_id) return null;
    return { user_id: c.user_id, display_name: c.display_name || "" };
  }

  setMaskImageUrl(url) {
    this.maskImg = null;
    if (!url) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => { this.maskImg = img; };
    img.src = url;
  }

  async start({
    deviceId,
    maskImageUrl = "",
    apiBase = "",
    cameraId = "",
    compositeMode = true,
  } = {}) {
    this.stop({ keepReady: true });
    this.apiBase = apiBase;
    this.cameraId = cameraId;
    this.compositeMode = compositeMode !== false;
    this.privacyReady = false;
    this.firstDetectDone = false;
    this.setMaskImageUrl(maskImageUrl);
    this.video.classList.toggle("live-source-hidden", this.compositeMode);
    this.canvas.parentElement?.classList.add("privacy-composite");
    if (this.compositeMode) this.canvas.style.opacity = "0";

    await this.init();

    let stream;
    if (deviceId) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { deviceId: { exact: deviceId } },
        });
      } catch (_) {
        stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId } });
      }
    } else {
      await ensureCameraPermission();
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
    }
    this.stream = stream;
    this.video.srcObject = stream;
    await this.video.play();
    this.running = true;
    this.lastTs = 0;
    const tick = (ts) => {
      if (!this.running) return;
      this.raf = requestAnimationFrame(tick);
      this.drawFrame(ts);
    };
    this.raf = requestAnimationFrame(tick);
    this.presenceTimer = setInterval(() => this.flushPresence(), 5000);
  }

  getLastFaceSignature() {
    if (!this.lastFaceBbox) return null;
    return signatureFromVideo(this.video, this.lastFaceBbox);
  }

  flushPresence() {
    // Browser may only report self (JWT); worker reports all matched faces.
    if (!this.apiBase || !this.cameraId || !this.presenceAcc.size) return Promise.resolve();
    const token = localStorage.getItem("cmir_token") || "";
    const selfId = currentUserId();
    if (!token || !selfId) {
      this.presenceAcc.clear();
      return Promise.resolve();
    }
    const seconds = this.presenceAcc.get(selfId) || 0;
    this.presenceAcc.clear();
    if (seconds <= 0) return Promise.resolve();
    return fetch(`${this.apiBase}/api/v1/face-presence`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        camera_id: this.cameraId,
        presence: [{ user_id: selfId, camera_id: this.cameraId, seconds: Math.round(seconds * 1000) / 1000 }],
      }),
      keepalive: true,
    }).catch(() => {});
  }

  stop({ keepReady = false } = {}) {
    this.flushPresence();
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
    if (this.presenceTimer) {
      clearInterval(this.presenceTimer);
      this.presenceTimer = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
    this.video.srcObject = null;
    this.video.classList.remove("live-source-hidden");
    this.canvas.parentElement?.classList.remove("privacy-composite");
    this.faceSmooth.clear();
    this.matchCache.clear();
    this.presenceAcc.clear();
    this.lastFaceBbox = null;
    this.privacyReady = false;
    this.firstDetectDone = false;
    this.ctx?.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (!keepReady) {
      this.ready = false;
      if (this.detector) {
        try {
          this.detector.close();
        } catch (_) {}
        this.detector = null;
      }
    }
  }

  resizeCanvas() {
    const wrap = this.canvas.parentElement;
    if (!wrap) return;
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w;
      this.canvas.height = h;
    }
  }

  drawFrame(ts) {
    const video = this.video;
    if (!video.videoWidth) return;
    this.resizeCanvas();
    const cw = this.canvas.width;
    const ch = this.canvas.height;
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const { scale, ox, oy } = coverTransform(vw, vh, cw, ch);

    this.ctx.fillStyle = "#000";
    this.ctx.fillRect(0, 0, cw, ch);

    if (!this.detector) return;

    if (ts - this.lastTs >= DETECT_INTERVAL_MS) {
      const elapsedSec = this.lastTs
        ? Math.min(0.25, Math.max(DETECT_INTERVAL_MS / 1000, (ts - this.lastTs) / 1000))
        : DETECT_INTERVAL_MS / 1000;
      this.lastTs = ts;
      const dets = (this.detector.detectForVideo(video, performance.now()).detections || [])
        .filter((d) => isLikelyFaceDetection(d, vw, vh));
      const usedKeys = new Set();
      let primaryBbox = null;

      for (const d of dets) {
        const coverHead = !!this.maskImg;
        const raw = poseFromDetection(d.keypoints, vw, vh, d.boundingBox, coverHead);
        if (!raw) continue;
        const key = matchFaceTrack(this.faceSmooth, raw);
        const prev = this.faceSmooth.get(key);
        const smooth = smoothPose(prev?.smooth, raw);
        const sigRaw = signatureFromVideo(video, d.boundingBox);
        const sig = blendSignature(prev?.sig, sigRaw);
        const priorId = prev?.userId || "";
        this.requestFaceMatch(key, sig, priorId);
        let face = this.cachedMatch(key);
        let hold = prev?.hold || 0;
        if (face?.user_id) {
          hold = CONSENT_HOLD_FRAMES;
        } else if (hold > 0 && priorId) {
          // hysteresis: keep registered identity briefly on angled frames
          face = { user_id: priorId, display_name: prev?.name || "" };
          hold -= 1;
        } else {
          hold = 0;
        }
        const name = face?.display_name || null;
        const userId = face?.user_id || null;
        const hadName = prev?.name;
        const confirm = (prev?.confirm || 0) + 1;
        this.faceSmooth.set(key, { smooth, name, userId, sig, confirm, missed: 0, hold });
        usedKeys.add(key);
        if (!primaryBbox) primaryBbox = d.boundingBox;
        if (userId) {
          this.presenceAcc.set(userId, (this.presenceAcc.get(userId) || 0) + elapsedSec);
        }
        if (name && !hadName && this.onRecognized) {
          this.onRecognized({ name, userId, key });
        }
      }

      if (primaryBbox) this.lastFaceBbox = primaryBbox;

      for (const [key, state] of this.faceSmooth) {
        if (usedKeys.has(key)) continue;
        state.missed = (state.missed || 0) + 1;
        state.confirm = 0;
        if (state.missed > 8) this.faceSmooth.delete(key);
      }
      this.firstDetectDone = true;
    }

    if (this.compositeMode && !this.firstDetectDone) return;

    if (this.compositeMode) {
      this.ctx.drawImage(video, ox, oy, vw * scale, vh * scale);
    }

    for (const state of this.faceSmooth.values()) {
      if (!state.smooth) continue;
      if (state.name) {
        drawNameUnderChin(this.ctx, state.smooth, state.name, scale, ox, oy);
      } else if ((state.confirm || 0) >= MIN_MASK_CONFIRM_FRAMES) {
        drawOrientedOverlay(this.ctx, state.smooth, this.maskImg, scale, ox, oy);
      }
    }

    if (this.compositeMode && !this.privacyReady) {
      this.privacyReady = true;
      this.canvas.style.opacity = "1";
    }
  }
}

function matchFaceTrack(faceSmooth, raw) {
  let bestKey = null;
  let bestDist = 96;
  for (const [key, state] of faceSmooth) {
    const p = state.smooth;
    if (!p) continue;
    const d = Math.hypot(p.cx - raw.cx, p.cy - raw.cy);
    if (d < bestDist) {
      bestDist = d;
      bestKey = key;
    }
  }
  if (bestKey) return bestKey;
  return `f_${Math.round(raw.cx)}_${Math.round(raw.cy)}_${Date.now() % 100000}`;
}

export async function startUsbCameraView(video, canvas, cam, poi, apiBase, fallbackCams = []) {
  const deviceId = await resolveUsbDeviceIdAsync(cam, fallbackCams);
  if (!deviceId) throw new Error("USB-камера не настроена");
  const view = new LiveCameraView(video, canvas);
  const maskUrl = poi?.mask_image_url ? `${apiBase}${poi.mask_image_url}` : "";
  await view.start({ deviceId, maskImageUrl: maskUrl, apiBase, cameraId: cam?.id || "" });
  return view;
}

function wantsLocalUsb(cam) {
  return !!(
    cam?.source_type === "local_usb"
    || cam?.device_id
    || (cam?.stream_url || "").startsWith("local://")
  );
}

/**
 * USB (getUserMedia) с маской, при ошибке — защищённый HLS.
 * Возвращает { mode: 'usb'|'hls', view, hls }.
 */
export async function startMaskedPageCamera({
  video,
  canvas,
  cam,
  poi,
  fallbackCams = [],
  apiBase,
  clientId,
  onStatus,
  usbOnly = false,
}) {
  if (!cam) throw new Error("Камера не настроена");
  const deviceId = await resolveUsbDeviceIdAsync(cam, fallbackCams);
  const tryUsb = wantsLocalUsb(cam) || !!deviceId;

  if (tryUsb && video && canvas) {
    let lastErr = null;
    for (let i = 0; i < 3; i++) {
      try {
        onStatus?.(i ? `Камера занята, повтор ${i + 1}/3…` : "Подключение USB-камеры…");
        // снять ffmpeg с этого POI, чтобы освободить FaceTime
        if (poi?.id) {
          await fetch(`${apiBase}/api/v1/pois/${poi.id}/stream/acquire`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              client_id: clientId || "browser",
              browser_usb: true,
              wait_hls: false,
            }),
          }).catch(() => {});
        }
        const view = new LiveCameraView(video, canvas);
        const maskUrl = poi?.mask_image_url ? `${apiBase}${poi.mask_image_url}` : "";
        await view.start({ deviceId, maskImageUrl: maskUrl, apiBase, cameraId: cam?.id || "" });
        return { mode: "usb", view, hls: null };
      } catch (e) {
        lastErr = e;
        await new Promise((r) => setTimeout(r, 500));
      }
    }
    if (usbOnly || wantsLocalUsb(cam)) {
      throw lastErr || new Error("USB-камера недоступна");
    }
    onStatus?.(`USB: ${lastErr?.message || "ошибка"}. Пробуем сетевой поток…`);
  }

  if (poi?.id) {
    await fetch(`${apiBase}/api/v1/pois/${poi.id}/stream/acquire`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: clientId || "browser", wait_hls: false }),
    }).catch(() => {});
  }
  onStatus?.("Подключение защищённого потока…");
  const { waitMaskedPlayback, playHlsOnVideo } = await import("./stream-player.js");
  const { url } = await waitMaskedPlayback(cam.id, clientId, { maxWaitMs: 20000, pollMs: 800 });
  const hls = await playHlsOnVideo(video, url, {});
  return { mode: "hls", view: null, hls };
}
```

## `apps/web/js/mask-preview.js`

```javascript
/** Превью маски: поворот по голове, плашка 2× шире, картинка — на всю голову */

const BAR_WIDTH_FACTOR = 1.28 * 2;
const POS_SMOOTH = 0.28;
const SIZE_SMOOTH = 0.22;
const ANGLE_SMOOTH = 0.35;

function kpCoord(v, dim) {
  return v <= 1 ? v * dim : v;
}

function bboxPixels(bbox, vw, vh) {
  if (!bbox) return null;
  const norm = bbox.originX <= 1 && bbox.originY <= 1 && bbox.width <= 1;
  return {
    x: norm ? bbox.originX * vw : bbox.originX,
    y: norm ? bbox.originY * vh : bbox.originY,
    w: norm ? bbox.width * vw : bbox.width,
    h: norm ? bbox.height * vh : bbox.height,
  };
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function lerpAngle(a, b, t) {
  let d = b - a;
  while (d > Math.PI) d -= 2 * Math.PI;
  while (d < -Math.PI) d += 2 * Math.PI;
  return a + d * t;
}

export function drawNameUnderChin(ctx, pose, name, scale, ox, oy) {
  const cx = ox + pose.cx * scale;
  const chinY = oy + (pose.cy + pose.h * 0.62) * scale;
  const fontSize = Math.max(12, pose.w * scale * 0.16);
  ctx.save();
  ctx.font = `600 ${fontSize}px system-ui, sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  const tw = ctx.measureText(name).width;
  const th = fontSize * 1.15;
  ctx.fillStyle = "rgba(0,0,0,0.85)";
  ctx.fillRect(cx - tw / 2 - 6, chinY, tw + 12, th + 8);
  ctx.fillStyle = "#fff";
  ctx.fillText(name, cx, chinY + 4);
  ctx.restore();
}

export function smoothPose(oldP, newP) {
  if (!oldP) return { ...newP };
  return {
    cx: lerp(oldP.cx, newP.cx, POS_SMOOTH),
    cy: lerp(oldP.cy, newP.cy, POS_SMOOTH),
    w: lerp(oldP.w, newP.w, SIZE_SMOOTH),
    h: lerp(oldP.h, newP.h, SIZE_SMOOTH),
    roll: lerpAngle(oldP.roll, newP.roll, ANGLE_SMOOTH),
    pitch: lerpAngle(oldP.pitch, newP.pitch, ANGLE_SMOOTH),
    yaw: lerpAngle(oldP.yaw, newP.yaw, ANGLE_SMOOTH),
    mode: newP.mode,
  };
}

export function poseFromDetection(kps, vw, vh, bbox, coverHead) {
  if (!kps || kps.length < 2) {
    const box = bboxPixels(bbox, vw, vh);
    if (!box) return null;
    const cx = box.x + box.w / 2;
    const cy = box.y + box.h * 0.42;
    const w = coverHead ? box.w * 1.35 : box.w * 1.1;
    const h = coverHead ? box.h * 1.4 : box.h * 0.45;
    return { cx, cy, w, h, roll: 0, pitch: 0, yaw: 0, mode: coverHead ? "head" : "bar" };
  }

  const rx = kpCoord(kps[0].x, vw);
  const ry = kpCoord(kps[0].y, vh);
  const lx = kpCoord(kps[1].x, vw);
  const ly = kpCoord(kps[1].y, vh);
  const nx = kps[2] ? kpCoord(kps[2].x, vw) : (rx + lx) / 2;
  const ny = kps[2] ? kpCoord(kps[2].y, vh) : (ry + ly) / 2;
  const mx = kps[3] ? kpCoord(kps[3].x, vw) : nx;
  const my = kps[3] ? kpCoord(kps[3].y, vh) : ny + 20;
  const rex = kps[4] ? kpCoord(kps[4].x, vw) : rx - 30;
  const rey = kps[4] ? kpCoord(kps[4].y, vh) : ry;
  const lex = kps[5] ? kpCoord(kps[5].x, vw) : lx + 30;
  const ley = kps[5] ? kpCoord(kps[5].y, vh) : ly;

  const eyeDist = Math.max(12, Math.hypot(lx - rx, ly - ry));
  const cx = (rx + lx) / 2;
  const cy = (ry + ly) / 2;

  const roll = Math.atan2(ly - ry, lx - rx);

  const ex = lx - rx;
  const ey = ly - ry;
  const elen = Math.hypot(ex, ey) || 1;
  const perpX = -ey / elen;
  const perpY = ex / elen;
  const noseOff = (nx - cx) * perpX + (ny - cy) * perpY;
  const yaw = Math.atan2(noseOff, eyeDist * 0.85);

  const earMidX = (rex + lex) / 2;
  const earMidY = (rey + ley) / 2;
  const earSpan = Math.hypot(lex - rex, ley - rey) || eyeDist * 1.6;
  const chinY = Math.max(my, ny + eyeDist * 0.35);
  const pitch = Math.atan2(chinY - cy - eyeDist * 0.55, earSpan * 0.5);

  if (coverHead) {
    const xs = [rx, lx, nx, mx, rex, lex];
    const ys = [ry, ly, ny, my, rey, ley];
    const box = bboxPixels(bbox, vw, vh);
    let minX = Math.min(...xs);
    let maxX = Math.max(...xs);
    let minY = Math.min(...ys);
    let maxY = Math.max(...ys);
    if (box) {
      minX = Math.min(minX, box.x);
      maxX = Math.max(maxX, box.x + box.w);
      minY = Math.min(minY, box.y);
      maxY = Math.max(maxY, box.y + box.h);
    }
    const padX = eyeDist * 0.55;
    const padTop = eyeDist * 0.75;
    const padBottom = eyeDist * 0.45;
    const w = (maxX - minX) + padX * 2;
    const h = (maxY - minY) + padTop + padBottom;
    return {
      cx: (minX + maxX) / 2,
      cy: (minY + maxY) / 2 + padBottom * 0.15,
      w: Math.max(w, eyeDist * 2.4),
      h: Math.max(h, eyeDist * 2.8),
      roll,
      pitch,
      yaw,
      mode: "head",
    };
  }

  const barW = Math.max(72, eyeDist * BAR_WIDTH_FACTOR);
  const barH = Math.max(22, barW * 0.52);
  return {
    cx,
    cy: cy - barH * 0.08,
    w: barW,
    h: barH,
    roll,
    pitch,
    yaw,
    mode: "bar",
  };
}

export function coverTransform(vw, vh, cw, ch) {
  const scale = Math.max(cw / vw, ch / vh);
  const dw = vw * scale;
  const dh = vh * scale;
  return { scale, ox: (cw - dw) / 2, oy: (ch - dh) / 2 };
}

export function drawDefaultPrivacyBar(ctx, pose, scale, ox, oy) {
  const cx = ox + pose.cx * scale;
  const cy = oy + pose.cy * scale;
  const w = pose.w * scale;
  const h = pose.h * scale;
  const skewX = Math.tan(pose.yaw) * 0.42;
  const skewY = Math.tan(pose.pitch) * 0.38;
  const scaleX = 1 + Math.sin(pose.yaw) * 0.22;
  const scaleY = 1 + Math.sin(pose.pitch) * 0.18;

  ctx.save();
  ctx.globalAlpha = 1;
  ctx.translate(cx, cy);
  ctx.rotate(pose.roll);
  ctx.transform(scaleX, skewY, skewX, scaleY, 0, 0);
  ctx.fillStyle = "#000";
  ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.strokeStyle = "rgba(255,255,255,0.35)";
  ctx.lineWidth = Math.max(1, w * 0.02);
  ctx.strokeRect(-w / 2, -h / 2, w, h);
  ctx.restore();
}

export function drawOrientedOverlay(ctx, pose, maskImg, scale, ox, oy) {
  if (!maskImg || pose.mode === "bar") {
    drawDefaultPrivacyBar(ctx, pose, scale, ox, oy);
    return;
  }

  const cx = ox + pose.cx * scale;
  const cy = oy + pose.cy * scale;
  const w = pose.w * scale;
  const h = pose.h * scale;

  const skewX = Math.tan(pose.yaw) * 0.42;
  const skewY = Math.tan(pose.pitch) * 0.38;
  const scaleX = 1 + Math.sin(pose.yaw) * 0.22;
  const scaleY = 1 + Math.sin(pose.pitch) * 0.18;

  ctx.save();
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = "source-over";
  ctx.translate(cx, cy);
  ctx.rotate(pose.roll);
  ctx.transform(scaleX, skewY, skewX, scaleY, 0, 0);

  ctx.fillStyle = "#000";
  ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.drawImage(maskImg, -w / 2, -h / 2, w, h);
  ctx.restore();
}

export class AdminMaskPreview {
  constructor(videoEl, canvasEl) {
    this.video = videoEl;
    this.canvas = canvasEl;
    this.ctx = canvasEl.getContext("2d");
    this.detector = null;
    this.maskImg = null;
    this.maskUrl = "";
    this.running = false;
    this.raf = 0;
    this.smooth = null;
    this.lastTs = 0;
    this.ready = false;
  }

  async init() {
    if (this.ready) return;
    const { FaceDetector, FilesetResolver } = await import(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14"
    );
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
    );
    this.detector = await FaceDetector.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
      },
      runningMode: "VIDEO",
    });
    this.ready = true;
  }

  setMaskUrl(url) {
    this.maskUrl = url || "";
    this.maskImg = null;
    this.smooth = null;
    if (!url) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      this.maskImg = img;
      this.smooth = null;
    };
    img.onerror = () => { this.maskImg = null; };
    img.src = url;
  }

  resizeCanvas() {
    const wrap = this.canvas.parentElement;
    if (!wrap) return;
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w;
      this.canvas.height = h;
    }
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.lastTs = 0;
    const tick = (ts) => {
      if (!this.running) return;
      this.raf = requestAnimationFrame(tick);
      this.drawFrame(ts);
    };
    this.raf = requestAnimationFrame(tick);
  }

  stop() {
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
    this.smooth = null;
    this.ctx?.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  drawFrame(ts) {
    const video = this.video;
    if (!video.videoWidth || !this.detector) return;
    this.resizeCanvas();
    const cw = this.canvas.width;
    const ch = this.canvas.height;
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const { scale, ox, oy } = coverTransform(vw, vh, cw, ch);

    this.ctx.clearRect(0, 0, cw, ch);

    if (ts - this.lastTs >= 33) {
      this.lastTs = ts;
      const dets = this.detector.detectForVideo(video, performance.now()).detections;
      if (dets.length) {
        const d = dets[0];
        const raw = poseFromDetection(d.keypoints, vw, vh, d.boundingBox, !!this.maskImg);
        if (raw) this.smooth = smoothPose(this.smooth, raw);
      }
    }

    if (!this.smooth) return;
    drawOrientedOverlay(this.ctx, this.smooth, this.maskImg, scale, ox, oy);
  }
}
```

## `apps/web/js/stream-player.js`

```javascript
/** Надёжное воспроизведение защищённого HLS через API Cmir. */
import { API } from "./api.js";

export function hlsConfig() {
  return {
    lowLatencyMode: false,
    manifestLoadingTimeOut: 30000,
    manifestLoadingMaxRetry: 10,
    levelLoadingTimeOut: 30000,
    fragLoadingTimeOut: 30000,
    maxBufferLength: 30,
    startFragPrefetch: true,
  };
}

export async function waitMaskedPlayback(cameraId, clientId, { maxWaitMs = 45000, pollMs = 800 } = {}) {
  const started = Date.now();
  while (Date.now() - started < maxWaitMs) {
    const res = await fetch(
      `${API}/api/v1/cameras/${cameraId}/playback?client_id=${encodeURIComponent(clientId)}`,
    );
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "playback failed");
    const d = json.data || {};
    const url = d.masked_hls_url || d.live_hls_url;
    if (d.masked_ready && url) return { url, data: d };
    await new Promise((r) => setTimeout(r, pollMs));
  }
  throw new Error("Защищённый поток не готов — проверьте камеру и face-worker");
}

export function playHlsOnVideo(video, url, { onReady, onError } = {}) {
  return new Promise((resolve, reject) => {
    if (!url) {
      reject(new Error("Нет URL потока"));
      return;
    }
    if (window.Hls && Hls.isSupported()) {
      const hls = new Hls(hlsConfig());
      let settled = false;
      const done = (ok, err) => {
        if (settled) return;
        settled = true;
        if (!ok) {
          hls.destroy();
          reject(err || new Error("HLS error"));
          return;
        }
        resolve(hls);
      };
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().then(() => {
          onReady?.();
          done(true);
        }).catch((e) => done(false, e));
      });
      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal && data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          hls.startLoad();
          return;
        }
        if (data.fatal) {
          onError?.(data);
          done(false, new Error(data.type || "fatal"));
        }
      });
      setTimeout(() => done(false, new Error("timeout")), 35000);
      return;
    }
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
      video.play().then(() => {
        onReady?.();
        resolve(null);
      }).catch(reject);
      return;
    }
    reject(new Error("HLS не поддерживается"));
  });
}

export async function acquirePoiStream(poiId, clientId, waitHls = true) {
  const res = await fetch(`${API}/api/v1/pois/${poiId}/stream/acquire`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: clientId, wait_hls: waitHls }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "acquire failed");
  return json.data;
}

export function releasePoiStream(poiId, clientId) {
  if (!poiId) return;
  navigator.sendBeacon(
    `${API}/api/v1/pois/${poiId}/stream/release`,
    new Blob([JSON.stringify({ client_id: clientId })], { type: "application/json" }),
  );
}
```

## `apps/web/js/user.js`

```javascript
import { API, api, getToken, setToken } from "./api.js";

let map, markers = [], pois = [], hlsPreview = null, selectedPoi = null;
let previewRetryTimer = null, previewAttempt = 0;
let activeStreamPoi = null;
let liveView = null;
let liveCameraMod = null;

async function ensureLiveCamera() {
  if (!liveCameraMod) {
    liveCameraMod = await import("./live-camera.js");
  }
  return liveCameraMod;
}

const els = {
  tabMap: () => document.getElementById("tabMap"),
  mapView: () => document.getElementById("mapView"),
  accountView: () => document.getElementById("accountView"),
  poiPanel: () => document.getElementById("poiPanel"),
  panelTitle: () => document.getElementById("panelTitle"),
  panelAddr: () => document.getElementById("panelAddr"),
  panelComment: () => document.getElementById("panelComment"),
  panelPreviewStatus: () => document.getElementById("panelPreviewStatus"),
  previewVideo: () => document.getElementById("previewVideo"),
  authGuest: () => document.getElementById("authGuest"),
  authUser: () => document.getElementById("authUser"),
  authStatus: () => document.getElementById("authStatus"),
  authMsg: () => document.getElementById("authMsg"),
  adminLink: () => document.getElementById("adminLink"),
};

function getClientId() {
  let id = sessionStorage.getItem("cmir_client_id");
  if (!id) {
    id = globalThis.crypto?.randomUUID?.() || `c-${Date.now()}`;
    sessionStorage.setItem("cmir_client_id", id);
  }
  return id;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function showView(name) {
  if (name !== "map" && selectedPoi) {
    closePoiPanel();
  }
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.querySelectorAll(".tab-btn[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === name);
  });
  const tabMap = els.tabMap();
  if (tabMap) tabMap.style.display = "";
  document.getElementById(name === "map" ? "mapView" : "accountView").classList.add("active");
  if (name === "map") {
    setTimeout(() => map?.invalidateSize(), 50);
    setTimeout(() => map?.invalidateSize(), 300);
  }
}

function initMap() {
  if (typeof L === "undefined") {
    throw new Error("Leaflet не загружен — проверьте интернет и обновите страницу");
  }
  const el = document.getElementById("map");
  if (!el) throw new Error("Элемент #map не найден");
  if (map) {
    map.remove();
    map = null;
  }
  map = L.map(el, { zoomControl: true }).setView([41.7151, 44.8271], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
  }).addTo(map);
}

function clearMarkers() {
  markers.forEach((m) => map.removeLayer(m));
  markers = [];
}

function showMapStatus(msg, isError = false) {
  const el = document.getElementById("mapStatus");
  if (!el) return;
  el.textContent = msg || "";
  el.classList.toggle("map-status--err", !!(msg && isError));
  el.style.display = msg ? "block" : "none";
}

async function loadPois() {
  if (!map) return;
  try {
    const res = await fetch(`${API}/api/v1/pois`);
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || res.statusText);
    pois = json.data || [];
    clearMarkers();
    pois.forEach((poi) => {
      const lat = Number(poi.latitude);
      const lon = Number(poi.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      const m = L.marker([lat, lon])
        .addTo(map)
        .bindTooltip(poi.name, { permanent: false })
        .on("click", () => openPoiPanel(poi));
      markers.push(m);
    });
    if (pois.length && !selectedPoi && markers.length) {
      const bounds = L.featureGroup(markers).getBounds();
      if (bounds.isValid()) map.fitBounds(bounds.pad(0.2));
    }
    if (selectedPoi) {
      const fresh = pois.find((p) => p.id === selectedPoi.id);
      if (fresh) selectedPoi = fresh;
    }
    if (!pois.length) {
      showMapStatus(
        "Нет мест на карте. Запустите lab: cd cmir && bash scripts/start-lab.sh",
        true,
      );
    } else {
      showMapStatus("");
    }
  } catch (e) {
    console.error("loadPois failed:", e);
    showMapStatus(
      `Сервер недоступен (${API}). Запустите: cd cmir && bash scripts/start-lab.sh`,
      true,
    );
  }
}

let viewTimer = null, viewCameraId = null;

function getPreviewCamera(poi) {
  const active = (poi?.cameras || []).filter((c) => c.is_active);
  const general = active.filter((c) => c.role === "general");
  return general.find((c) => c.is_preview) || general[0]
    || active.find((c) => c.is_preview) || active[0] || null;
}

function usbFallbackCams(poi, primary) {
  return (poi?.cameras || []).filter(
    (c) => c.is_active && c.id !== primary?.id && (c.source_type === "local_usb" || c.device_id || (c.stream_url || "").startsWith("local://")),
  );
}

function setPreviewStatus(msg) {
  const el = els.panelPreviewStatus();
  if (el) el.textContent = msg || "";
}

function stopViewTracking() {
  if (viewTimer) { clearInterval(viewTimer); viewTimer = null; }
  viewCameraId = null;
}

async function releaseStream(poiId, { force = false } = {}) {
  if (!poiId) return;
  try {
    await api("POST", `/api/v1/pois/${poiId}/stream/release`, {
      client_id: getClientId(),
      force,
    });
  } catch (_) {}
  if (activeStreamPoi === poiId) activeStreamPoi = null;
}

function stopPreview() {
  if (previewRetryTimer) { clearTimeout(previewRetryTimer); previewRetryTimer = null; }
  stopClipPoll();
  stopViewTracking();
  if (liveView) {
    liveView.stop();
    liveView = null;
  }
  if (hlsPreview) {
    hlsPreview.destroy();
    hlsPreview = null;
  }
  const v = els.previewVideo();
  const canvas = document.getElementById("previewMaskCanvas");
  if (canvas) {
    canvas.style.display = "";
    canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
  }
  if (v) {
    v.pause();
    v.removeAttribute("src");
    v.srcObject = null;
    v.loop = false;
    v.load();
  }
}

async function closePoiPanel() {
  const poiId = selectedPoi?.id || activeStreamPoi;
  els.poiPanel().classList.remove("open");
  stopPreview();
  setPreviewStatus("");
  selectedPoi = null;
  previewAttempt = 0;
  if (poiId) await releaseStream(poiId, { force: false });
}

function startViewTracking(cameraId) {
  stopViewTracking();
  if (!getToken() || !cameraId) return;
  viewCameraId = cameraId;
  viewTimer = setInterval(async () => {
    try {
      await api("POST", "/api/v1/views", { camera_id: viewCameraId, seconds: 30, ad_revenue: 0.02 });
    } catch (_) {}
  }, 30000);
}

function liveUrls(pb) {
  const d = pb.data || {};
  return [...new Set([d.masked_hls_url, d.live_hls_url].filter(Boolean))];
}

function hlsConfig() {
  return {
    lowLatencyMode: false,
    manifestLoadingTimeOut: 25000,
    manifestLoadingMaxRetry: 8,
    levelLoadingTimeOut: 25000,
    fragLoadingTimeOut: 25000,
    maxBufferLength: 30,
  };
}

function tryHlsUrl(video, url, camId, { trackViews = false } = {}) {
  return new Promise((resolve) => {
    if (!window.Hls || !Hls.isSupported()) {
      if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = url;
        video.loop = false;
        video.play().then(() => {
          if (trackViews) startViewTracking(camId);
          resolve(true);
        }).catch(() => resolve(false));
        return;
      }
      resolve(false);
      return;
    }
    const hls = new Hls(hlsConfig());
    let settled = false;
    const done = (ok) => {
      if (settled) return;
      settled = true;
      if (!ok) {
        hls.destroy();
        resolve(false);
        return;
      }
      if (hlsPreview && hlsPreview !== hls) hlsPreview.destroy();
      hlsPreview = hls;
      resolve(true);
    };
    hls.loadSource(url);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      video.loop = false;
      video.play().then(() => {
        if (trackViews) {
          setPreviewStatus("");
          startViewTracking(camId);
        }
        done(true);
      }).catch(() => done(false));
    });
    hls.on(Hls.Events.ERROR, (_, data) => {
      if (data.fatal && data.type === Hls.ErrorTypes.NETWORK_ERROR) {
        hls.startLoad();
        return;
      }
      if (data.fatal) done(false);
    });
    setTimeout(() => done(false), 18000);
  });
}

async function fetchPlayback(cam) {
  const cid = encodeURIComponent(getClientId());
  return api("GET", `/api/v1/cameras/${cam.id}/playback?client_id=${cid}`);
}

function resolveClipUrl(clipUrl) {
  if (!clipUrl) return "";
  if (clipUrl.startsWith("http")) return clipUrl;
  return `${API}${clipUrl}`;
}

function switchToPreviewClip(clipUrl) {
  if (hlsPreview) {
    hlsPreview.destroy();
    hlsPreview = null;
  }
  if (liveView) {
    liveView.stop();
    liveView = null;
  }
  const canvas = document.getElementById("previewMaskCanvas");
  if (canvas) {
    canvas.style.display = "none";
    canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
  }
  const video = els.previewVideo();
  video.classList.remove("live-source-hidden");
  video.loop = true;
  video.srcObject = null;
  video.src = `${resolveClipUrl(clipUrl)}?t=${Date.now()}`;
  video.play().catch(() => {});
  setPreviewStatus("Превью: 10 с записи с эфира (зациклено)");
}

let clipPollTimer = null;

function stopClipPoll() {
  if (clipPollTimer) {
    clearTimeout(clipPollTimer);
    clipPollTimer = null;
  }
}

function pollPreviewClipSwitch(poi) {
  stopClipPoll();
  const poll = async () => {
    if (!selectedPoi || selectedPoi.id !== poi.id) return;
    try {
      const st = await api("GET", `/api/v1/pois/${poi.id}/preview-clip`);
      const d = st.data || {};
      if (d.ready && d.clip_url) {
        switchToPreviewClip(d.clip_url);
        return;
      }
      if (d.error) {
        setPreviewStatus(`Превью: ${d.error}`);
      } else if (d.recording || (d.buffered_seconds || 0) < (d.target_seconds || 10)) {
        setPreviewStatus(`Запись превью… ${d.buffered_seconds || 0}/${d.target_seconds || 10} с`);
      }
    } catch (_) {}
    clipPollTimer = setTimeout(poll, 1000);
  };
  poll();
}

async function startPoiPreview(poi, fromRetry = false) {
  if (!fromRetry) previewAttempt = 0;
  const cam = getPreviewCamera(poi);
  const video = els.previewVideo();
  const canvas = document.getElementById("previewMaskCanvas");
  stopPreview();
  stopClipPoll();
  if (!cam) {
    setPreviewStatus("У места нет активной камеры. Настройте в админке и нажмите «Сохранить камеры».");
    return;
  }

  const mod = await ensureLiveCamera();
  const deviceId = await mod.resolveUsbDeviceIdAsync(cam, usbFallbackCams(poi, cam));
  const isLocal = cam.source_type === "local_usb" || !!deviceId
    || !!cam.device_id || (cam.stream_url || "").startsWith("local://");

  if (activeStreamPoi && activeStreamPoi !== poi.id) {
    await releaseStream(activeStreamPoi, { force: false });
  }
  activeStreamPoi = poi.id;

  // local_usb на iMac: только браузерный getUserMedia — без ffmpeg/acquire
  // (иначе 10 ретраев и камера остаётся включённой)
  if (isLocal && canvas) {
    try {
      setPreviewStatus("Подключение камеры…");
      // освобождаем device, если relay ещё держит ffmpeg
      await releaseStream(poi.id, { force: false });
      activeStreamPoi = poi.id;
      await new Promise((r) => setTimeout(r, 350));
      const { LiveCameraView } = mod;
      liveView = new LiveCameraView(video, canvas);
      canvas.style.display = "";
      const maskUrl = poi.mask_image_url ? `${API}${poi.mask_image_url}` : "";
      await liveView.start({
        deviceId,
        maskImageUrl: maskUrl,
        apiBase: API,
        cameraId: cam.id,
        compositeMode: true,
      });
      liveView.onRecognized = null;
      setPreviewStatus("Прямой эфир (веб-камера)");
      previewAttempt = 0;
      return;
    } catch (e) {
      liveView?.stop();
      liveView = null;
      previewAttempt += 1;
      if (previewAttempt < 3) {
        setPreviewStatus(`Камера занята, повтор ${previewAttempt}/3…`);
        previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 700);
        return;
      }
      setPreviewStatus(`Камера недоступна: ${e.message}. Закройте FaceTime/Zoom и откройте место снова.`);
      return;
    }
  }

  setPreviewStatus(previewAttempt ? `Подключение… попытка ${previewAttempt + 1}` : "Запуск камеры…");
  try {
    const pb = await fetchPlayback(cam);
    const isLocalNet = pb.data?.source_type === "local_usb";

    if (isLocalNet && !pb.data?.masked_ready) {
      setPreviewStatus("Подготовка защищённого потока…");
      previewAttempt += 1;
      if (previewAttempt >= 8) {
        setPreviewStatus("Защищённый поток не готов. Проверьте камеру и face-worker.");
        return;
      }
      previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 1000);
      return;
    }

    const urls = liveUrls(pb);
    if (!urls.length) {
      setPreviewStatus("Поток недоступен. Запустите start-lab.sh и сохраните камеры в админке.");
      previewAttempt += 1;
      if (previewAttempt < 6) {
        previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 1500);
      }
      return;
    }

    setPreviewStatus("Прямой эфир…");
    for (const url of urls) {
      const ok = await tryHlsUrl(video, url, cam.id, { trackViews: !isLocalNet });
      if (ok) {
        previewAttempt = 0;
        if (isLocalNet) pollPreviewClipSwitch(poi);
        else setPreviewStatus("");
        return;
      }
    }
    previewAttempt += 1;
    if (previewAttempt >= 5) {
      setPreviewStatus("Не удалось подключиться. Проверьте MediaMTX (docker) и USB-камеру в админке.");
      return;
    }
    previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 2000);
  } catch (e) {
    setPreviewStatus(e.message || "Ошибка загрузки потока");
  }
}

async function openPoiPanel(poi) {
  try {
    const res = await fetch(`${API}/api/v1/pois`);
    const list = (await res.json()).data || [];
    poi = list.find((p) => p.id === poi.id) || poi;
  } catch (_) {}
  selectedPoi = poi;
  els.poiPanel().classList.add("open");
  els.panelTitle().textContent = poi.name;
  els.panelAddr().textContent = poi.address || `${poi.city || ""} ${poi.country || ""}`.trim() || "—";
  els.panelComment().textContent = poi.comment || poi.description || "";
  await startPoiPreview(poi);
}

async function openFullscreenStream() {
  if (!selectedPoi) return;
  const cam = getPreviewCamera(selectedPoi);
  if (!cam) return alert("Нет активной камеры");
  try {
    const pb = await fetchPlayback(cam);
    const url = liveUrls(pb)[0];
    if (!url) return alert("Поток недоступен — подождите завершения подготовки превью");
    const u = new URL("stream.html", location.href);
    u.searchParams.set("poi", selectedPoi.id);
    u.searchParams.set("url", url);
    u.searchParams.set("name", selectedPoi.name);
    u.searchParams.set("client", getClientId());
    window.open(u.toString(), "_blank", "noopener,noreferrer,width=1280,height=720");
  } catch (e) {
    alert(e.message || "Ошибка открытия трансляции");
  }
}

async function loadProfileMenu(poiId) {
  const sel = document.getElementById("profileMenu");
  if (!poiId || !sel) return;
  try {
    const items = (await api("GET", `/api/v1/pois/${poiId}/menu-items`)).data || [];
    const cur = sel.value;
    sel.innerHTML = '<option value="">— выберите —</option>'
      + items.map((i) => `<option value="${i}">${i}</option>`).join("");
    if (cur) sel.value = cur;
  } catch (_) {}
}

async function loadPlatformLinks() {
  const box = document.getElementById("platformLinks");
  if (!box || !getToken()) return;
  try {
    const links = (await api("GET", "/api/v1/auth/platforms")).data || [];
    box.innerHTML = links.length
      ? links.map((l) => `<p class="hint">${l.platform}: <strong>${l.username || "—"}</strong></p>`).join("")
      : "<p class='hint'>Нет привязанных платформ</p>";
  } catch (_) {
    box.innerHTML = "";
  }
}

async function fillProfileForm(u) {
  const form = document.getElementById("formProfile");
  if (!form) return;
  const prof = u.profile || {};
  const fio = document.getElementById("profileFio");
  if (fio) fio.textContent = `ФИО: ${prof.full_name || u.display_name} (изменение недоступно)`;
  const phone = document.getElementById("profilePhone");
  const email = document.getElementById("profileEmail");
  const menu = document.getElementById("profileMenu");
  if (phone) phone.value = prof.phone || "";
  if (email) email.value = u.email || "";
  if (menu) menu.value = prof.favorite_menu_item || "";
  const poiId = u.consents?.[0]?.poi_id;
  await loadProfileMenu(poiId);
  if (menu && prof.favorite_menu_item) menu.value = prof.favorite_menu_item;
  await loadPlatformLinks();
  renderConsents(u);
  await loadAirtime();
}

async function loadAirtime() {
  const box = document.getElementById("airtimeList");
  if (!box || !getToken()) return;
  try {
    const rows = (await api("GET", "/api/v1/face-presence")).data || [];
    box.innerHTML = rows.length
      ? rows.map((r) => `
          <p class="hint">${r.camera_name || r.camera_id?.slice(0, 8) || "камера"} ·
            ${Number(r.seconds).toFixed(1)} с · период ${r.period_key}</p>
        `).join("")
      : "<p class='hint'>Пока нет зафиксированного присутствия в кадре.</p>";
  } catch (_) {
    box.innerHTML = "";
  }
}

function renderConsents(u) {
  const box = document.getElementById("consentsList");
  if (!box) return;
  const rows = u?.consents || [];
  if (!rows.length) {
    box.innerHTML = "<p class='hint'>Нет активных согласий — зарегистрируйтесь в киоске.</p>";
    return;
  }
  box.innerHTML = rows.map((c) => `
    <div class="stream-item" style="display:flex;justify-content:space-between;gap:0.5rem;align-items:center;padding:0.4rem 0;border-bottom:1px solid var(--border,#243552)">
      <span class="hint">POI ${String(c.poi_id).slice(0, 8)}… · ${c.consented_at || ""}</span>
      <button type="button" class="secondary" data-revoke-poi="${c.poi_id}" data-revoke-id="${c.id}" style="width:auto;padding:0.35rem 0.65rem;margin:0">Отозвать</button>
    </div>
  `).join("");
  box.querySelectorAll("[data-revoke-id]").forEach((btn) => {
    btn.onclick = async () => {
      if (!confirm("Отозвать согласие? На камерах снова появится маска.")) return;
      try {
        await api("DELETE", `/api/v1/pois/${btn.dataset.revokePoi}/consent/${btn.dataset.revokeId}`);
        await refreshAuth();
      } catch (err) {
        alert(err.message || "Не удалось отозвать");
      }
    };
  });
}

function userHasConsent(u) {
  return Array.isArray(u?.consents) && u.consents.length > 0;
}

function updateKioskLink(u) {
  const link = document.getElementById("kioskLink");
  if (!link) return;
  link.style.display = u && userHasConsent(u) ? "none" : "";
}

async function refreshAuth() {
  const token = getToken();
  const tabAccount = document.getElementById("tabAccount");
  if (!token) {
    els.authGuest().style.display = "block";
    els.authUser().style.display = "none";
    els.adminLink().style.display = "none";
    updateKioskLink(null);
    if (tabAccount) tabAccount.style.display = "";
    return;
  }
  try {
    const me = await api("GET", "/api/v1/auth/me");
    const u = me.data;
    if (u.role === "admin") {
      els.authGuest().style.display = "none";
      els.authUser().style.display = "none";
      els.adminLink().style.display = "inline-block";
      updateKioskLink(u);
      if (tabAccount) tabAccount.style.display = "none";
      showView("map");
      return;
    }
    els.authGuest().style.display = "none";
    els.authUser().style.display = "block";
    els.adminLink().style.display = "none";
    updateKioskLink(u);
    if (tabAccount) tabAccount.style.display = "";
    const w = u.wallet;
    els.authStatus().textContent = w
      ? `${u.display_name} (${u.email})\nКошелёк: ${w.address}\nST: ${w.balance_st} · UT: ${w.balance_ut}`
      : `${u.display_name} (${u.email})`;
    await fillProfileForm(u);
  } catch {
    setToken("");
    refreshAuth();
  }
}

function bindEvents() {
  document.querySelectorAll(".tab-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => showView(btn.dataset.view));
  });

  document.getElementById("closePanel").addEventListener("click", () => closePoiPanel());

  document.getElementById("btnFullscreen").addEventListener("click", openFullscreenStream);

  window.addEventListener("pagehide", () => {
    const poiId = activeStreamPoi || selectedPoi?.id;
    stopPreview();
    selectedPoi = null;
    if (!poiId) return;
    navigator.sendBeacon(
      `${API}/api/v1/pois/${poiId}/stream/release`,
      new Blob(
        [JSON.stringify({ client_id: getClientId(), force: false })],
        { type: "application/json" },
      ),
    );
    activeStreamPoi = null;
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      const poiId = activeStreamPoi || selectedPoi?.id;
      stopPreview();
      if (poiId) {
        navigator.sendBeacon(
          `${API}/api/v1/pois/${poiId}/stream/release`,
          new Blob(
            [JSON.stringify({ client_id: getClientId(), force: false })],
            { type: "application/json" },
          ),
        );
      }
      activeStreamPoi = null;
      return;
    }
    if (document.visibilityState === "visible" && selectedPoi && els.poiPanel()?.classList.contains("open")) {
      startPoiPreview(selectedPoi).catch(() => {});
    }
  });

  document.querySelectorAll(".auth-tabs button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".auth-tabs button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("formLogin").style.display = btn.dataset.auth === "login" ? "block" : "none";
      document.getElementById("formRegister").style.display = btn.dataset.auth === "register" ? "block" : "none";
    });
  });

  document.getElementById("formLogin").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const r = await api("POST", "/api/v1/auth/login", {
        email: fd.get("email"),
        password: fd.get("password"),
      });
      setToken(r.data.token);
      if (r.data.user) localStorage.setItem("cmir_user", JSON.stringify(r.data.user));
      els.authMsg().textContent = "Вход выполнен";
      els.authMsg().className = "msg ok";
      await refreshAuth();
      if (r.data.user?.role === "admin") {
        els.adminLink().style.display = "inline-block";
      }
    } catch (err) {
      els.authMsg().textContent = err.message;
      els.authMsg().className = "msg error";
    }
  });

  document.getElementById("formRegister").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("POST", "/api/v1/auth/register", {
        email: fd.get("email"),
        password: fd.get("password"),
        display_name: fd.get("name"),
      });
      els.authMsg().textContent = "Регистрация OK — войдите";
      els.authMsg().className = "msg ok";
    } catch (err) {
      els.authMsg().textContent = err.message;
      els.authMsg().className = "msg error";
    }
  });

  document.getElementById("btnLogout").addEventListener("click", async () => {
    try { await api("POST", "/api/v1/auth/logout", {}); } catch (_) {}
    setToken("");
    localStorage.removeItem("cmir_user");
    refreshAuth();
  });

  document.getElementById("formProfile")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("profileMsg");
    try {
      const body = {
        phone: document.getElementById("profilePhone").value.trim(),
        email: document.getElementById("profileEmail").value.trim(),
        favorite_menu_item: document.getElementById("profileMenu").value,
      };
      const r = await api("PATCH", "/api/v1/auth/profile", body);
      msg.textContent = "Профиль сохранён";
      msg.className = "msg ok";
      if (r.data?.user) await fillProfileForm({ ...r.data.user, profile: r.data.profile });
    } catch (err) {
      msg.textContent = err.message;
      msg.className = "msg error";
    }
  });

  document.getElementById("btnLinkPlatform")?.addEventListener("click", async () => {
    try {
      await api("POST", "/api/v1/auth/platforms/link", {
        platform: document.getElementById("platformSelect").value,
        username: document.getElementById("platformUsername").value.trim(),
      });
      await loadPlatformLinks();
      document.getElementById("profileMsg").textContent = "Платформа привязана";
      document.getElementById("profileMsg").className = "msg ok";
    } catch (err) {
      document.getElementById("profileMsg").textContent = err.message;
      document.getElementById("profileMsg").className = "msg error";
    }
  });

  document.getElementById("btnOAuthPlatform")?.addEventListener("click", async () => {
    try {
      const platform = document.getElementById("platformSelect").value;
      const r = await api("GET", `/api/v1/platforms/${platform}/authorize`);
      if (r.data?.authorize_url) location.href = r.data.authorize_url;
    } catch (err) {
      document.getElementById("profileMsg").textContent = err.message;
      document.getElementById("profileMsg").className = "msg error";
    }
  });
}

export async function initUser() {
  try {
    initMap();
    bindEvents();
    showView("map");
    await refreshAuth();
    await loadPois();
    setInterval(loadPois, 30000);
  } catch (e) {
    console.error("initUser failed:", e);
    const banner = document.createElement("p");
    banner.className = "msg error";
    banner.style.cssText = "position:fixed;bottom:1rem;left:1rem;right:1rem;z-index:9999;padding:1rem;background:#2a1212";
    banner.textContent = `Ошибка загрузки карты: ${e.message}`;
    document.body.appendChild(banner);
  }
}
```

## `apps/web/performance.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cmir — перфоманс</title>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.7/dist/hls.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #0a1628; color: #e8eef7; min-height: 100vh; }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 1.5rem; display: grid; gap: 1.25rem; grid-template-columns: 1fr 1fr; }
    @media (max-width: 860px) { .wrap { grid-template-columns: 1fr; } }
    .card { background: #132238; border-radius: 16px; padding: 1.25rem; border: 1px solid #243552; }
    h1 { font-size: 1.4rem; margin-bottom: 0.35rem; }
    .sub { opacity: 0.75; font-size: 0.9rem; margin-bottom: 1rem; }
    .video-box { position: relative; border-radius: 12px; overflow: hidden; background: #000; aspect-ratio: 16/10; }
    .video-box .mask-overlay-canvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
    video { width: 100%; height: 100%; object-fit: cover; }
    .video-label { position: absolute; bottom: 8px; left: 8px; background: rgba(0,0,0,0.55); padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; }
    label { display: block; font-size: 0.85rem; margin: 0.75rem 0 0.25rem; }
    input, select { width: 100%; padding: 0.65rem; border-radius: 10px; border: 1px solid #3a4d66; background: #0f1419; color: #fff; }
    .btn { width: 100%; margin-top: 0.75rem; padding: 0.75rem; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; }
    .btn-primary { background: linear-gradient(135deg, #6ecfff, #3498db); color: #031018; }
    .btn-secondary { background: #243552; color: #fff; }
    .btn-danger { background: #8b2e2e; color: #fff; }
    .btn:disabled { opacity: 0.45; cursor: not-allowed; }
    #status { margin-top: 0.75rem; font-size: 0.85rem; min-height: 1.2em; }
    #status.err { color: #ff8a8a; }
    #status.ok { color: #7dffb0; }
    .panel { display: none; }
    .panel.active { display: block; }
    .stream-list { margin-top: 0.75rem; font-size: 0.85rem; }
    .stream-item { padding: 0.5rem 0; border-bottom: 1px solid #243552; display: flex; justify-content: space-between; gap: 0.5rem; align-items: center; }
    a { color: #6ecfff; }
    .row-btns { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
    .row-btns .btn { width: auto; flex: 1; min-width: 120px; }
  </style>
</head>
<body>
  <p style="text-align:center;padding:1rem"><a href="index.html">← На главную</a> · <a href="index.html#account" id="accountLink">Личный кабинет</a></p>
  <div class="wrap">
    <section class="card">
      <h1>Камера перфоманс</h1>
      <p class="sub" id="poiName">Интервью / стол — регистрация и управление эфиром</p>
      <div class="video-box">
        <video id="live" autoplay playsinline muted></video>
        <canvas id="liveMaskCanvas" class="mask-overlay-canvas"></canvas>
        <span class="video-label" id="liveLabel">Подключение…</span>
      </div>
    </section>

    <section class="card">
      <div id="panelRegister" class="panel active">
        <h1>Регистрация</h1>
        <p class="sub">Заполните данные для согласия и доступа к управлению.</p>
        <label for="fullName">ФИО</label>
        <input id="fullName" autocomplete="name" />
        <label for="phone">Телефон</label>
        <input id="phone" type="tel" autocomplete="tel" />
        <label for="menuItem">Любимый пункт меню</label>
        <select id="menuItem"><option value="">Загрузка…</option></select>
        <button type="button" class="btn btn-primary" id="btnRegister" disabled>Зарегистрироваться</button>
      </div>

      <div id="panelControls" class="panel">
        <h1>Управление</h1>
        <p class="sub" id="userGreeting"></p>
        <p class="sub">Подпись привязана к вашему лицу (биометрии) и отображается на всех камерах, где вы появляетесь.</p>

        <label for="streamTitle">Название эфира</label>
        <input id="streamTitle" placeholder="Мой эфир" />
        <div class="row-btns">
          <button type="button" class="btn btn-primary" id="btnStart">Старт</button>
          <button type="button" class="btn btn-secondary" id="btnStop">Стоп и сохранить</button>
        </div>
        <div class="stream-list" id="streamList"></div>
      </div>
      <div id="status"></div>
    </section>
  </div>

  <script type="module">
    import { api, getToken, setToken, API } from "./js/api.js";
    import { startMaskedPageCamera } from "./js/live-camera.js";

    const qs = new URLSearchParams(location.search);
    let poiId = qs.get("poi") || "";
    let perfCamera = null;
    let currentPoi = null;
    let hls = null;
    let liveView = null;
    let me = null;

    const live = document.getElementById("live");
    const liveLabel = document.getElementById("liveLabel");
    const statusEl = document.getElementById("status");

    function getClientId() {
      let id = sessionStorage.getItem("cmir_perf_client");
      if (!id) {
        id = globalThis.crypto?.randomUUID?.() || `p-${Date.now()}`;
        sessionStorage.setItem("cmir_perf_client", id);
      }
      return id;
    }

    function setStatus(msg, ok) {
      statusEl.textContent = msg || "";
      statusEl.className = ok ? "ok" : msg ? "err" : "";
    }

    function stopHls() {
      if (hls) { hls.destroy(); hls = null; }
      live.removeAttribute("src");
    }

    function pickPerformanceCamera(poi) {
      const cams = (poi?.cameras || []).filter((c) => c.is_active);
      return cams.find((c) => c.role === "performance") || cams.find((c) => c.is_preview) || cams[0];
    }

    async function resolveContext() {
      const list = (await api("GET", "/api/v1/pois")).data || [];
      let poi = poiId ? list.find((p) => p.id === poiId) : null;
      if (!poi) {
        poi = list.find((p) => (p.cameras || []).some((c) => c.role === "performance" && c.is_active));
      }
      if (!poi) throw new Error("Нет места с камерой «перфоманс». Настройте в админке.");
      poiId = poi.id;
      currentPoi = poi;
      perfCamera = pickPerformanceCamera(poi);
      if (!perfCamera) throw new Error("Нет активной камеры перфоманс у этого места.");
      document.getElementById("poiName").textContent = `${poi.name} · камера: ${perfCamera.name}`;
    }

    async function startStream() {
      liveLabel.textContent = "Подключение…";
      if (liveView) { liveView.stop(); liveView = null; }
      stopHls();

      const fallbacks = (currentPoi?.cameras || []).filter(
        (c) => c.is_active && c.id !== perfCamera?.id,
      );
      try {
        const result = await startMaskedPageCamera({
          video: live,
          canvas: document.getElementById("liveMaskCanvas"),
          cam: perfCamera,
          poi: currentPoi,
          fallbackCams: fallbacks,
          apiBase: API,
          clientId: getClientId(),
          usbOnly: true,
          onStatus: (msg) => { if (msg) liveLabel.textContent = msg; },
        });
        liveView = result.view;
        hls = result.hls;
        liveLabel.textContent = "Прямой эфир (с маской)";
      } catch (e) {
        liveLabel.textContent = e.message || "Поток недоступен";
        setTimeout(() => startStream(), 3000);
      }
    }

    function stopAll() {
      if (liveView) { liveView.stop(); liveView = null; }
      stopHls();
      if (!poiId) return;
      navigator.sendBeacon(
        `${API}/api/v1/pois/${poiId}/stream/release`,
        new Blob(
          [JSON.stringify({ client_id: getClientId(), force: false })],
          { type: "application/json" },
        ),
      );
    }

    window.addEventListener("pagehide", stopAll);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") stopAll();
    });

    function showControls(user) {
      document.getElementById("panelRegister").classList.remove("active");
      document.getElementById("panelControls").classList.add("active");
      const label = user.profile?.full_name || user.display_name;
      document.getElementById("userGreeting").textContent =
        `${label} · кошелёк ${user.wallet?.address || "—"}`;
    }

    async function loadStreams() {
      if (!perfCamera || !getToken()) return;
      const rows = (await api("GET", `/api/v1/performance/streams?camera_id=${perfCamera.id}`)).data || [];
      const box = document.getElementById("streamList");
      box.innerHTML = rows.length ? rows.map((s) => `
        <div class="stream-item">
          <span>${s.title || "Эфир"} · <em>${s.status}</em>${s.clip_status === "ready" ? " · ✓" : ""}</span>
          <span>
            ${s.clip_status === "ready" && s.recording_id
    ? `<a href="${API}/api/v1/recordings/${s.recording_id}/clip.mp4" target="_blank">Клип</a> · `
    : ""}
            <button type="button" class="btn btn-danger" data-del="${s.id}" style="width:auto;padding:0.35rem 0.6rem;margin:0">Удалить</button>
          </span>
        </div>
      `).join("") : "<p class='sub'>Нет сохранённых эфиров</p>";
      box.querySelectorAll("[data-del]").forEach((btn) => {
        btn.onclick = async () => {
          if (!confirm("Удалить запись эфира?")) return;
          await api("DELETE", `/api/v1/performance/streams/${btn.dataset.del}`);
          await loadStreams();
        };
      });
    }

    async function refreshMe() {
      if (!getToken()) return null;
      me = (await api("GET", "/api/v1/auth/me")).data;
      showControls(me);
      await loadStreams();
      return me;
    }

    function updateRegisterBtn() {
      const ok = document.getElementById("fullName").value.trim()
        && document.getElementById("phone").value.trim()
        && document.getElementById("menuItem").value;
      document.getElementById("btnRegister").disabled = !ok;
    }

    document.getElementById("btnRegister").onclick = async () => {
      document.getElementById("btnRegister").disabled = true;
      setStatus("Регистрация…");
      try {
        if (live.readyState < 2 && !liveView) throw new Error("Дождитесь изображения с камеры");
        const embedding = liveView?.getLastFaceSignature();
        if (!embedding) throw new Error("Лицо не обнаружено — посмотрите в камеру");
        const res = await api("POST", `/api/v1/pois/${poiId}/kiosk-register`, {
          full_name: document.getElementById("fullName").value.trim(),
          phone: document.getElementById("phone").value.trim(),
          favorite_menu_item: document.getElementById("menuItem").value,
          face_embedding: embedding,
          acceptances: {
            terms_of_service: true,
            privacy_policy: true,
            personal_data_consent: true,
            biometric_data_consent: true,
            wallet_agreement: true,
          },
        });
        if (res.data?.auth?.token) setToken(res.data.auth.token);
        if (res.data?.user) localStorage.setItem("cmir_user", JSON.stringify(res.data.user));
        setStatus(res.message || "Готово", true);
        await refreshMe();
      } catch (e) {
        setStatus(e.message);
        document.getElementById("btnRegister").disabled = false;
      }
    };

    document.getElementById("btnStart").onclick = async () => {
      try {
        await api("POST", "/api/v1/performance/streams", {
          camera_id: perfCamera.id,
          title: document.getElementById("streamTitle").value.trim() || "Эфир",
        });
        setStatus("Эфир запущен", true);
        await loadStreams();
      } catch (e) { setStatus(e.message); }
    };

    document.getElementById("btnStop").onclick = async () => {
      try {
        const rows = (await api("GET", `/api/v1/performance/streams?camera_id=${perfCamera.id}`)).data || [];
        const liveRow = rows.find((r) => r.status === "live");
        if (!liveRow) return setStatus("Нет активного эфира");
        if (liveView) await liveView.flushPresence();
        const stopped = await api("POST", `/api/v1/performance/streams/${liveRow.id}/stop`, {});
        const rewards = stopped.data?.rewards?.participants || [];
        const totalUt = rewards.reduce((s, r) => s + Number(r.ut_earned || 0), 0);
        setStatus(
          `Эфир остановлен. UT (доля от 1 за полный стрим): ${rewards.length} уч., Σ ${totalUt.toFixed(4)} UT.`,
          true,
        );
        await loadStreams();
      } catch (e) { setStatus(e.message); }
    };

    ["fullName", "phone", "menuItem"].forEach((id) => {
      document.getElementById(id).addEventListener("input", updateRegisterBtn);
      document.getElementById(id).addEventListener("change", updateRegisterBtn);
    });

    try {
      await resolveContext();
      const items = (await api("GET", `/api/v1/pois/${poiId}/menu-items`)).data || [];
      document.getElementById("menuItem").innerHTML = '<option value="">— выберите —</option>'
        + items.map((i) => `<option value="${i}">${i}</option>`).join("");
      updateRegisterBtn();
      await startStream();
      if (await refreshMe()) {
        document.getElementById("panelRegister").classList.remove("active");
      }
    } catch (e) {
      setStatus(e.message);
      liveLabel.textContent = e.message;
    }
  </script>
</body>
</html>
```

## `apps/web/stream.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <title>Cmir — трансляция</title>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.7"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { width: 100%; height: 100%; background: #000; overflow: hidden; }
    video { width: 100vw; height: 100vh; object-fit: contain; background: #000; }
    .title {
      position: fixed; top: 12px; left: 16px; color: #fff;
      font: 600 1rem system-ui, sans-serif; text-shadow: 0 1px 4px #000;
      z-index: 2; max-width: 70%;
    }
    .status {
      position: fixed; bottom: 12px; left: 16px; color: #ccc;
      font: 0.85rem system-ui, sans-serif; text-shadow: 0 1px 4px #000;
      z-index: 2;
    }
  </style>
</head>
<body>
  <p class="title" id="title"></p>
  <p class="status" id="status">Подключение…</p>
  <video id="v" controls autoplay muted playsinline></video>
  <script type="module">
    const API = localStorage.getItem("cmir_api") || "http://localhost:8090";
    const p = new URLSearchParams(location.search);
    const url = p.get("url");
    const poiId = p.get("poi");
    const clientId = p.get("client") || sessionStorage.getItem("cmir_client_id") || "fullscreen";
    const name = p.get("name") || "Live";
    document.getElementById("title").textContent = name;
    const video = document.getElementById("v");
    const statusEl = document.getElementById("status");
    let hls = null;

    async function acquire() {
      if (!poiId) return;
      await fetch(`${API}/api/v1/pois/${poiId}/stream/acquire`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: clientId, wait_hls: true }),
      });
    }

    function release() {
      if (!poiId) return;
      navigator.sendBeacon(
        `${API}/api/v1/pois/${poiId}/stream/release`,
        new Blob([JSON.stringify({ client_id: clientId })], { type: "application/json" }),
      );
    }

    function playHls(streamUrl) {
      if (!streamUrl) {
        statusEl.textContent = "Нет URL потока";
        return;
      }
      if (window.Hls && Hls.isSupported()) {
        hls = new Hls({
          lowLatencyMode: false,
          manifestLoadingTimeOut: 25000,
          manifestLoadingMaxRetry: 8,
          levelLoadingTimeOut: 25000,
          fragLoadingTimeOut: 25000,
          maxBufferLength: 30,
        });
        hls.loadSource(streamUrl);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          statusEl.textContent = "Live (защищённый поток)";
          video.play().catch(() => {});
        });
        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal && data.type === Hls.ErrorTypes.NETWORK_ERROR) {
            hls.startLoad();
            return;
          }
          if (data.fatal) statusEl.textContent = "Ошибка потока: " + (data.type || "");
        });
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = streamUrl;
        video.play().catch(() => {});
        statusEl.textContent = "Live";
      } else {
        statusEl.textContent = "HLS не поддерживается в этом браузере";
      }
    }

    window.addEventListener("pagehide", release);

    if (!url) {
      statusEl.textContent = "Нет URL потока";
    } else {
      acquire()
        .then(() => playHls(url))
        .catch((e) => {
          statusEl.textContent = e.message || "Ошибка подключения";
          playHls(url);
        });
    }
  </script>
</body>
</html>
```
