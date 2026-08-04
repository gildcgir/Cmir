# Cmir Android — публикация в Google Play

## Что это
Нативный Android shell (`com.cmir.app`) с WebView: карта, киоск согласия (камера), аккаунт.
UI/логика — из веб-контура Cmir; приложение даёт доступ к камере и deep links.

## Статус чеклиста (обновлено 2026-08-04)

| Пункт | Статус | Комментарий |
|-------|--------|-------------|
| Target API 35+ | ✅ | `compileSdk`/`targetSdk` = 35, `minSdk` 26 |
| Debug lab (USB + adb reverse) | ✅ | `com.cmir.app.debug`, auto-retry offline |
| Карта + POI + маски на фронтальной камере | ✅ | lab через reverse |
| Полноэкранная трансляция в WebView | ✅ | `stream.html` in-place / device+masks |
| Ссылки Privacy / Terms в UI | ✅ | `privacy.html`, `terms.html` (черновик) |
| Чат у POI + заявки мест (approve) | ✅ | web + API; Android через тот же WebView |
| Production `cmir_web_base` HTTPS | ⏳ | сейчас `https://app.cmir.live/` — нужен реальный деплой |
| Cleartext только для debug | ✅ | `usesCleartextTraffic=false`; localhost разрешён в `network_security_config` |
| Иконки Adaptive Icon | ✅ | vector adaptive (заменить на брендовый 1024 перед релизом) |
| Privacy Policy URL (публичный HTTPS) | ❌ | нужен хостинг финального текста |
| Data safety form (Play Console) | ❌ | заполняется в Console |
| Content rating (IARC) | ❌ | в Console |
| Camera permission rationale / disclosure | ✅ | in-app disclosure перед системным запросом CAMERA |
| Подпись AAB / Play App Signing | ❌ | upload key + `bundleRelease` |
| Crash-free на Pixel / Samsung | ⏳ | Pixel lab OK; нужен ещё mid-range прогон |
| Скриншоты листинга | ❌ | карта / киоск / эфир с маской |

## Перед загрузкой в Play Console
1. Замените `cmir_web_base` в `app/src/main/res/values/strings.xml` на production HTTPS URL (сайт должен отвечать).
2. Для release: `android:usesCleartextTraffic="false"` и только HTTPS в `network_security_config.xml`.
3. Добавьте реальные иконки: `mipmap-*/ic_launcher` (1024×1024 → Adaptive Icon).
4. Privacy Policy URL (обязательно для CAMERA / biometrics): опубликуйте страницу и укажите в Play Console.
5. Data safety form: biometrics face templates, account phone/email, camera — «collected / processed».
6. Content rating questionnaire (IARC).
7. Подпишите AAB: `./gradlew bundleRelease` с upload key в Play App Signing.

## Сборка
```bash
cd apps/android
./gradlew assembleDebug
./gradlew bundleRelease
```

Lab на Pixel:
```bash
bash scripts/android-lab-pixel.sh
# после переподключения USB:
adb reverse tcp:3000 tcp:3000 && adb reverse tcp:8090 tcp:8090
```

## Листинг (черновик)
- Title: Cmir
- Short: Карта live-мест с приватностью лиц
- Full: Смотрите трансляции заведений, регистрируйте согласие в киоске, кошелёк ST/UT.
- Category: Social / Entertainment
- Screenshots: phone 1080×1920 — карта, киоск, эфир с маской

## Следующий шаг
1. Задеплоить web на HTTPS (`app.cmir.live` или свой домен) и проверить release WebView.
2. Опубликовать финальные Privacy/Terms и указать URL в Play Console.
3. Собрать signed AAB (`bundleRelease`) + Play App Signing, Data safety, IARC.
4. Скриншоты листинга (карта / киоск / эфир с маской) и прогон на mid-range Samsung.
