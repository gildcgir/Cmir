# Keep WebView / JS interfaces
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
