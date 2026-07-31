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
