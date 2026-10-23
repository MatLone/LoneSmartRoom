package com.lonesmartroom.app

import android.app.Activity
import android.os.Build
import android.os.Bundle
import android.view.WindowInsets
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import org.json.JSONObject
import java.util.concurrent.Executors

/** Local WebView; isolated native bridges for WoL, secure status and confirmed apps. */
class MainActivity : Activity() {
    private lateinit var webView: WebView
    private val executor = Executors.newSingleThreadExecutor()
    private val assetsPrefix = "file:///android_asset/"
    private lateinit var agentBridge: AgentBridge

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        webView = WebView(this)
        webView.setBackgroundColor(android.graphics.Color.rgb(20, 23, 32))
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowContentAccess = false
        webView.settings.allowFileAccess = true // Necessário apenas para /android_asset/
        webView.settings.allowFileAccessFromFileURLs = false
        webView.settings.allowUniversalAccessFromFileURLs = false
        webView.settings.javaScriptCanOpenWindowsAutomatically = false
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url?.toString().orEmpty()
                return !url.startsWith(assetsPrefix)
            }
        }
        webView.addJavascriptInterface(WakeBridge(), "LoneAndroid")
        webView.addJavascriptInterface(AppInfoBridge(), "LoneAppInfo")
        agentBridge = AgentBridge(this, deliver = { result ->
            webView.evaluateJavascript("window.onLoneAgentStatus && window.onLoneAgentStatus(${result})", null)
        }, deliverApps = { result ->
            webView.evaluateJavascript("window.onLoneAppLaunch && window.onLoneAppLaunch(${result})", null)
        })
        webView.addJavascriptInterface(agentBridge, "LoneAgent")
        setContentView(webView)
        if (Build.VERSION.SDK_INT >= 35) {
            webView.setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(WindowInsets.Type.systemBars())
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
                insets
            }
        }
        webView.loadUrl(assetsPrefix + "index.html")
    }

    class AppInfoBridge {
        @JavascriptInterface fun getVersionName(): String = BuildConfig.VERSION_NAME
    }

    inner class WakeBridge {
        @JavascriptInterface
        fun sendWake(mac: String, broadcast: String, port: Int) {
            executor.execute {
                val result = try {
                    WakeOnLan.send(mac, broadcast, port)
                    JSONObject().put("ok", true).put("message", "Pacote enviado pela rede local")
                } catch (error: Exception) {
                    JSONObject().put("ok", false).put("message", error.message ?: "Falha no envio")
                }
                runOnUiThread {
                    // JSONObject serializa os textos, evitando injeção na expressão JS.
                    webView.evaluateJavascript("window.onLoneWakeResult(${result})", null)
                }
            }
        }
    }

    override fun onDestroy() {
        executor.shutdownNow()
        agentBridge.close()
        webView.removeJavascriptInterface("LoneAgent")
        webView.removeJavascriptInterface("LoneAppInfo")
        webView.removeJavascriptInterface("LoneAndroid")
        webView.destroy()
        super.onDestroy()
    }
}
