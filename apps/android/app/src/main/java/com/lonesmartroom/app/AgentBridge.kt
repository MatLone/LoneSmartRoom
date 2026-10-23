package com.lonesmartroom.app

import android.app.Activity
import android.app.AlertDialog
import android.text.InputType
import android.view.ContextThemeWrapper
import android.view.WindowManager
import android.webkit.JavascriptInterface
import android.widget.EditText
import org.json.JSONObject
import java.util.concurrent.Executors

/** No pairing code, key or credential is exposed to the WebView. */
class AgentBridge(private val activity: Activity, private val deliver: (JSONObject) -> Unit) {
    private val executor = Executors.newSingleThreadExecutor()
    private val vault = AgentVault(activity)
    private val client = AgentClient()
    private val status = AgentStatus()
    @Volatile private var closed = false
    private fun emit(reason: String) {
        val data = JSONObject().put("state", status.state).put("last_success", status.lastSuccess).put("message", reason)
        activity.runOnUiThread { if (!closed) deliver(data) }
    }
    @JavascriptInterface fun refreshStatus() {
        if (closed) return
        executor.execute {
            try {
                val config = vault.load()
                if (config == null) { status.forget(); emit("Pareie com o Windows para consultar o agente."); return@execute }
                status.restoreLastSuccess(config.optLong("last_success"))
                client.status(config)
                status.connected(System.currentTimeMillis())
                vault.save(config.put("last_success", status.lastSuccess))
                emit("Agente autenticado acessível; isso não confirma o estado de energia do PC.")
            } catch (error: Exception) {
                status.disconnected()
                emit("Sem comunicação autenticada. Verifique rede, certificado, horário e autorização; o PC pode estar ligado.")
            }
        }
    }
    @JavascriptInterface fun showPairing() {
        activity.runOnUiThread {
            if (closed) return@runOnUiThread
            val context = ContextThemeWrapper(activity, android.R.style.Theme_DeviceDefault_Dialog_Alert)
            val input = EditText(context).apply {
                hint = "LSR2.…"
                inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
                importantForAutofill = android.view.View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS
            }
            val dialog = AlertDialog.Builder(context).setTitle("Parear agente Windows")
                .setMessage("Cole o código obtido diretamente na tela confiável do Windows. Ele contém a identidade do certificado; nunca use um código recebido de terceiros.")
                .setView(input).setNegativeButton("Cancelar", null)
                .setPositiveButton("Parear") { _, _ ->
                    val text = input.text.toString().trim()
                    try {
                        val payload = client.pairingPayload(text)
                        AlertDialog.Builder(context).setTitle("Confirmar identidade do Windows")
                            .setMessage("Compare com a tela Windows antes de continuar.\n\n" + payload.getString("url") +
                                "\n\nSHA-256: " + payload.getString("sha256"))
                            .setNegativeButton("Cancelar", null)
                            .setPositiveButton("Identidade confere") { _, _ ->
                                executor.execute {
                                    try {
                                        // Recheck expiration after the user confirmation.
                                        val verified = client.pairingPayload(text)
                                        vault.save(client.pair(verified))
                                        status.forget()
                                        emit("Pareamento salvo com segurança. Consulte o status.")
                                    } catch (error: Exception) { emit("Pareamento recusado. Confira código, prazo, rede e identidade do Windows.") }
                                }
                            }.show()
                    } catch (error: Exception) { emit("Código inválido ou expirado; gere outro no Windows.") }
                }.create()
            dialog.window?.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
            dialog.show()
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(android.graphics.Color.rgb(240, 71, 89))
        }
    }
    fun close() { closed = true; executor.shutdownNow() }
}
