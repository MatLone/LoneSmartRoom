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
import java.util.concurrent.atomic.AtomicBoolean
import java.security.SecureRandom

/** No pairing code, key or credential is exposed to the WebView. */
class AgentBridge(private val activity: Activity, private val deliver: (JSONObject) -> Unit,
                  private val deliverApps: (JSONObject) -> Unit) {
    private val executor = Executors.newSingleThreadExecutor()
    private val vault = AgentVault(activity)
    private val client = AgentClient()
    private val status = AgentStatus()
    @Volatile private var closed = false
    private val launchBusy = AtomicBoolean(false)
    private fun emitApps(value: JSONObject) {
        activity.runOnUiThread { if (!closed) deliverApps(value) }
    }
    private fun appFailure(message: String) {
        emitApps(JSONObject().put("state", "failed").put("message", message))
    }
    @JavascriptInterface fun refreshAppPermissions() {
        if (closed) return
        executor.execute {
            try {
                val config = vault.load() ?: throw IllegalStateException()
                val allowed = client.appPermissions(config)
                emitApps(JSONObject().put("kind", "permissions").put("allowed_apps", org.json.JSONArray(allowed.toList())))
            } catch (error: Exception) {
                emitApps(JSONObject().put("kind", "permissions").put("allowed_apps", org.json.JSONArray())
                    .put("message", "Permissão indisponível. Autorize Steam/CS2 localmente no Windows e confira o agente."))
            }
        }
    }
    private fun recordLaunch(config: JSONObject, result: JSONObject) {
        val pending = config.getJSONObject("pending_launch")
        pending.put("state", result.getString("state"))
        vault.save(config)
        emitApps(result)
    }
    private fun queryLaunch(config: JSONObject): JSONObject? {
        val pending = config.optJSONObject("pending_launch") ?: return null
        val result = try {
            client.launchResult(config, pending.getString("app"), pending.getString("request_id"))
        } catch (error: AgentRequestException) {
            if (error.statusCode != 404) throw error
            JSONObject().put("state", "failed").put("app", pending.getString("app"))
                .put("request_id", pending.getString("request_id"))
                .put("message", "Solicitação não encontrada no agente; nenhuma execução foi confirmada.")
        }
        recordLaunch(config, result)
        return result
    }
    @JavascriptInterface fun refreshLaunchResult() {
        if (closed || !launchBusy.compareAndSet(false, true)) return
        executor.execute {
            try { vault.load()?.let { queryLaunch(it) } }
            catch (error: Exception) { appFailure("Sem confirmação do resultado. Consulte novamente; não repita a abertura.") }
            finally { launchBusy.set(false) }
        }
    }
    @JavascriptInterface fun requestAppLaunch(app: String) {
        if (closed || app !in setOf("steam", "cs2") || !launchBusy.compareAndSet(false, true)) return
        executor.execute {
            try {
                val config = vault.load() ?: throw IllegalStateException()
                val pending = config.optJSONObject("pending_launch")
                if (pending != null && pending.optString("state") !in setOf("executed", "failed")) {
                    val result = queryLaunch(config)
                    if (result != null && result.getString("state") !in setOf("executed", "failed")) {
                        appFailure("Há uma solicitação em andamento. Consulte o resultado antes de abrir outro aplicativo.")
                        launchBusy.set(false)
                        return@execute
                    }
                }
                require(app in client.appPermissions(config))
                activity.runOnUiThread {
                    if (closed) { launchBusy.set(false); return@runOnUiThread }
                    val name = if (app == "steam") "Steam" else "Counter-Strike 2"
                    AlertDialog.Builder(ContextThemeWrapper(activity, android.R.style.Theme_DeviceDefault_Dialog_Alert))
                        .setTitle("Autorizar abertura de $name")
                        .setMessage("Abrir $name no Windows pareado?\n\n${config.getString("url")}\n\nO Windows também precisa autorizar este aplicativo para este dispositivo.")
                        .setNegativeButton("Cancelar") { _, _ -> launchBusy.set(false) }
                        .setOnCancelListener { launchBusy.set(false) }
                        .setPositiveButton("Autorizar abertura") { _, _ ->
                            executor.execute { submitLaunch(config, app) }
                        }.show()
                }
            } catch (error: Exception) {
                appFailure("Abertura bloqueada. Confira pareamento, rede e autorização específica no Windows.")
                launchBusy.set(false)
            }
        }
    }
    private fun submitLaunch(confirmedConfig: JSONObject, app: String) {
        try {
            val config = vault.load() ?: throw IllegalStateException()
            require(listOf("url", "sha256", "device_id").all { config.getString(it) == confirmedConfig.getString(it) })
            val id = ByteArray(16).also { SecureRandom().nextBytes(it) }.joinToString("") { "%02x".format(it.toInt() and 255) }
            config.put("pending_launch", JSONObject().put("request_id", id).put("app", app).put("state", "requested"))
            vault.save(config) // Save before POST: timeout must not generate a second launch.
            emitApps(JSONObject().put("state", "requested").put("request_id", id).put("app", app))
            val result = try { client.launch(config, app, id) }
            catch (error: AgentRequestException) {
                config.getJSONObject("pending_launch").put("state", "failed")
                vault.save(config)
                throw error
            }
            recordLaunch(config, result)
            repeat(4) {
                if (closed || config.getJSONObject("pending_launch").getString("state") in setOf("executed", "failed")) return
                Thread.sleep(500)
                queryLaunch(config)
            }
        } catch (error: Exception) {
            appFailure("Falha ou resultado ainda não confirmado. Consulte a solicitação; não reenvie automaticamente.")
        } finally { launchBusy.set(false) }
    }
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
