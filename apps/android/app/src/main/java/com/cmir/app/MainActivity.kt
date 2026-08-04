/**
 * Cmir Android — WebView shell for map / kiosk / account.
 * Package: com.cmir.app
 *
 * Debug lab: loads http://127.0.0.1:3000 via `adb reverse` — USB must stay connected.
 */
package com.cmir.app

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private var pendingPermissionRequest: PermissionRequest? = null
    private var loadFailed = false
    private var startUrl: String = ""
    private var mainFrameRetries = 0
    private var offlineAutoRetry = false
    private val mainHandler = Handler(Looper.getMainLooper())

    private val requestCamera = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        pendingPermissionRequest?.let { req ->
            if (granted) req.grant(req.resources) else req.deny()
            pendingPermissionRequest = null
        }
    }

    private val retryLabRunnable = object : Runnable {
        override fun run() {
            if (!::webView.isInitialized) return
            if (!packageName.endsWith(".debug")) return
            if (!loadFailed && webView.url?.startsWith("data:") != true) return
            Log.i(TAG, "auto-retry lab URL")
            loadLabUrl()
            mainHandler.postDelayed(this, RETRY_INTERVAL_MS)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.parseColor("#121A28")

        if (packageName.endsWith(".debug")) {
            WebView.setWebContentsDebuggingEnabled(true)
        }

        webView = WebView(this)
        setContentView(webView)

        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.mediaPlaybackRequiresUserGesture = false
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
        settings.userAgentString = settings.userAgentString + " CmirAndroid/1.0"
        settings.setSupportMultipleWindows(true)
        settings.javaScriptCanOpenWindowsAutomatically = true
        // Debug: avoid stale kiosk/map JS after lab edits
        settings.cacheMode = if (packageName.endsWith(".debug")) {
            WebSettings.LOAD_NO_CACHE
        } else {
            WebSettings.LOAD_DEFAULT
        }
        webView.setBackgroundColor(Color.parseColor("#0a0e14"))

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView?,
                request: WebResourceRequest?
            ): Boolean {
                val url = request?.url?.toString() ?: return false
                // Keep map / kiosk / account inside the same WebView
                if (url.startsWith("http://127.0.0.1")
                    || url.startsWith("http://localhost")
                    || url.contains("cmir.live")
                    || url.startsWith("file:")
                ) {
                    view?.loadUrl(url)
                    return true
                }
                return false
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                Log.i(TAG, "onPageFinished url=$url")
                if (url != null && !url.startsWith("data:")) {
                    loadFailed = false
                    mainFrameRetries = 0
                    stopOfflineAutoRetry()
                }
                if (packageName.endsWith(".debug")) {
                    view?.postDelayed({
                        view.evaluateJavascript(
                            "(function(){var imgs=[...document.querySelectorAll('.leaflet-tile-loaded')];var src=imgs[0]&&imgs[0].src||'';return JSON.stringify({boot:!!document.getElementById('bootStatus'),markers:document.querySelectorAll('.leaflet-marker-icon').length,tiles:imgs.length});})()"
                        ) { result -> Log.i(TAG, "pageState=$result") }
                    }, 2500)
                }
                super.onPageFinished(view, url)
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                if (request?.isForMainFrame == true) {
                    handleMainFrameError(
                        error?.errorCode,
                        error?.description?.toString(),
                        request.url?.toString()
                    )
                }
                super.onReceivedError(view, request, error)
            }

            @Deprecated("Deprecated in Java")
            override fun onReceivedError(
                view: WebView?,
                errorCode: Int,
                description: String?,
                failingUrl: String?
            ) {
                // API < 23 only; on newer devices the overload above is used.
                // Ignore subresource noise if URL is not our lab entry.
                if (isLabMainUrl(failingUrl)) {
                    handleMainFrameError(errorCode, description, failingUrl)
                }
                @Suppress("DEPRECATION")
                super.onReceivedError(view, errorCode, description, failingUrl)
            }
        }
        webView.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
                val msg = consoleMessage ?: return super.onConsoleMessage(consoleMessage)
                Log.i(
                    TAG,
                    "JS ${msg.messageLevel()} ${msg.sourceId()}:${msg.lineNumber()} ${msg.message()}"
                )
                return true
            }

            override fun onCreateWindow(
                view: WebView?,
                isDialog: Boolean,
                isUserGesture: Boolean,
                resultMsg: android.os.Message?
            ): Boolean {
                // window.open → same WebView (Play/lab WebView has no tab UI)
                val transport = resultMsg?.obj as? WebView.WebViewTransport ?: return false
                transport.webView = webView
                resultMsg.sendToTarget()
                return true
            }

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
                    maybeShowCameraDisclosureThenRequest()
                }
            }
        }

        // Allow JS window.open / target=_blank to reach onCreateWindow
        webView.settings.setSupportMultipleWindows(true)
        webView.settings.javaScriptCanOpenWindowsAutomatically = true

        startUrl = intent?.data?.toString() ?: getString(R.string.cmir_web_base)
        loadLabUrl()
    }

    override fun onResume() {
        super.onResume()
        if (packageName.endsWith(".debug") && ::webView.isInitialized) {
            // USB unplug clears adb reverse → offline page; retry when returning to app
            if (loadFailed || webView.url?.startsWith("data:") == true) {
                Log.i(TAG, "retrying lab URL after resume")
                mainFrameRetries = 0
                loadLabUrl()
                startOfflineAutoRetry()
            }
        }
    }

    override fun onPause() {
        stopOfflineAutoRetry()
        super.onPause()
    }

    private fun maybeShowCameraDisclosureThenRequest() {
        val prefs = getSharedPreferences(PREFS, MODE_PRIVATE)
        if (prefs.getBoolean(KEY_CAMERA_DISCLOSURE_SHOWN, false)) {
            requestCamera.launch(Manifest.permission.CAMERA)
            return
        }
        AlertDialog.Builder(this)
            .setTitle(R.string.camera_disclosure_title)
            .setMessage(R.string.camera_disclosure_message)
            .setPositiveButton(R.string.camera_disclosure_continue) { _, _ ->
                prefs.edit().putBoolean(KEY_CAMERA_DISCLOSURE_SHOWN, true).apply()
                requestCamera.launch(Manifest.permission.CAMERA)
            }
            .setNegativeButton(R.string.camera_disclosure_cancel) { _, _ ->
                pendingPermissionRequest?.deny()
                pendingPermissionRequest = null
            }
            .setCancelable(false)
            .show()
    }

    private fun loadLabUrl() {
        val url = startUrl.ifBlank { getString(R.string.cmir_web_base) }
        webView.loadUrl(url)
    }

    private fun isLabMainUrl(url: String?): Boolean {
        if (url.isNullOrBlank()) return false
        if (url.startsWith("data:")) return false
        val base = startUrl.ifBlank { getString(R.string.cmir_web_base) }
        return url == base || url.removeSuffix("/") == base.removeSuffix("/") ||
            url.startsWith("http://127.0.0.1:3000") || url.startsWith("http://localhost:3000")
    }

    private fun handleMainFrameError(code: Int?, description: String?, failingUrl: String?) {
        if (!packageName.endsWith(".debug")) return
        loadFailed = true
        Log.e(TAG, "main frame error $code $description url=$failingUrl (retry=$mainFrameRetries)")
        mainFrameRetries += 1
        if (mainFrameRetries <= MAX_QUICK_RETRIES) {
            mainHandler.postDelayed({ loadLabUrl() }, QUICK_RETRY_DELAY_MS * mainFrameRetries)
            return
        }
        showLabOfflinePage()
        startOfflineAutoRetry()
    }

    private fun startOfflineAutoRetry() {
        if (offlineAutoRetry) return
        offlineAutoRetry = true
        mainHandler.removeCallbacks(retryLabRunnable)
        mainHandler.postDelayed(retryLabRunnable, RETRY_INTERVAL_MS)
    }

    private fun stopOfflineAutoRetry() {
        offlineAutoRetry = false
        mainHandler.removeCallbacks(retryLabRunnable)
    }

    private fun showLabOfflinePage() {
        if (!packageName.endsWith(".debug")) return
        val html = """
            <!DOCTYPE html><html><head>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width,initial-scale=1"/>
            <style>
              body{font-family:system-ui,sans-serif;background:#0a0e14;color:#e8edf5;
                   padding:2rem 1.25rem;line-height:1.45}
              h1{font-size:1.25rem;margin:0 0 .75rem}
              code{background:#1a2332;padding:.1rem .35rem;border-radius:4px;font-size:.85rem}
              button{margin-top:1.25rem;width:100%;padding:.85rem;border:0;border-radius:10px;
                     background:#4d9fff;color:#0a0e14;font-weight:700;font-size:1rem}
              .hint{color:#8a96a8;font-size:.9rem;margin-top:1rem}
            </style></head><body>
            <h1>Нет связи с lab на Mac</h1>
            <p>USB подключён — но нужен ещё <b>adb reverse</b> (туннель к Mac).</p>
            <p>На Mac выполните:</p>
            <p>
              <code>adb reverse tcp:3000 tcp:3000</code><br/>
              <code>adb reverse tcp:8090 tcp:8090</code>
            </p>
            <p>или целиком: <code>bash scripts/android-lab-pixel.sh</code></p>
            <p class="hint">После переподключения кабеля reverse сбрасывается. Приложение само пробует снова каждые 2 с.</p>
            <button onclick="location.href='http://127.0.0.1:3000/'">Повторить</button>
            </body></html>
        """.trimIndent()
        webView.loadDataWithBaseURL(
            "http://127.0.0.1:3000/",
            html,
            "text/html",
            "UTF-8",
            null
        )
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (this::webView.isInitialized && webView.canGoBack()) {
            webView.goBack()
        } else {
            @Suppress("DEPRECATION")
            super.onBackPressed()
        }
    }

    companion object {
        private const val TAG = "CmirWeb"
        private const val PREFS = "cmir_prefs"
        private const val KEY_CAMERA_DISCLOSURE_SHOWN = "camera_disclosure_shown"
        private const val MAX_QUICK_RETRIES = 3
        private const val QUICK_RETRY_DELAY_MS = 700L
        private const val RETRY_INTERVAL_MS = 2000L
    }
}
