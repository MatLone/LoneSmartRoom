package com.lonesmartroom.app

import android.util.Base64
import org.json.JSONObject
import java.net.URL
import java.security.SecureRandom
import javax.net.ssl.HttpsURLConnection

class AgentRequestException(val statusCode: Int) : Exception("Agente recusou a requisição")

class AgentClient {
    companion object {
        private fun ipv4(value: String): Long {
            val octets = value.split('.')
            require(octets.size == 4 && octets.all { it.matches(Regex("0|[1-9][0-9]{0,2}")) && it.toInt() <= 255 })
            return octets.fold(0L) { acc, octet -> (acc shl 8) or octet.toLong() }
        }
        fun validateEndpoint(config: JSONObject) {
            val url = URL(config.getString("url"))
            require(url.protocol == "https" && url.userInfo == null && url.query == null && url.ref == null && url.path.isEmpty())
            require(url.port in 1024..65535)
            val address = ipv4(url.host)
            val privateAddress = (address ushr 24 == 10L) || (address ushr 20 == 2753L) || (address ushr 16 == 49320L)
            require(privateAddress) { "Somente endereços privados da LAN são permitidos" }
            val network = config.getString("network").split('/')
            require(network.size == 2)
            val prefix = network[1].toInt()
            require(prefix in 24..30)
            val mask = (0xffffffffL shl (32 - prefix)) and 0xffffffffL
            val base = ipv4(network[0])
            require(base and mask == base && address and mask == base && address != base && address != (base or (mask xor 0xffffffffL)))
            require(config.getString("sha256").matches(Regex("[0-9a-f]{64}")))
        }
    }
    fun pairingPayload(text: String): JSONObject {
        require(text.length in 6..2048 && text.startsWith("LSR2."))
        val value = JSONObject(String(Base64.decode(text.substring(5), Base64.URL_SAFE or Base64.NO_WRAP), Charsets.UTF_8))
        validateEndpoint(value)
        val remaining = value.getLong("expires") - System.currentTimeMillis() / 1000
        require(remaining in 1..300) { "Pareamento expirado; gere outro código no Windows" }
        require(value.getString("code").matches(Regex("[A-Za-z0-9_-]{32}")))
        return value
    }
    private fun exchange(config: JSONObject, path: String, body: ByteArray? = null,
                         headers: Map<String, String> = emptyMap(), accepted: Set<Int> = setOf(200), responseLimit: Int = 4096): JSONObject {
        validateEndpoint(config)
        val connection = URL(config.getString("url") + path).openConnection() as HttpsURLConnection
        try {
            connection.sslSocketFactory = PinnedTls.socketFactory(config.getString("sha256"))
            // Keep the platform's strict hostname/SAN verifier. Never follow redirects.
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 5000
            connection.readTimeout = 5000
            connection.requestMethod = if (body == null) "GET" else "POST"
            headers.forEach { (name, value) -> connection.setRequestProperty(name, value) }
            if (body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.setFixedLengthStreamingMode(body.size)
                connection.outputStream.use { it.write(body) }
            }
            if (connection.responseCode !in accepted) throw AgentRequestException(connection.responseCode)
            require(responseLimit in 1..32768)
            val data = connection.inputStream.use { it.readBytesBounded(responseLimit) }
            return JSONObject(String(data, Charsets.UTF_8)).also { require(it.optBoolean("ok")) }
        } finally { connection.disconnect() }
    }
    private fun java.io.InputStream.readBytesBounded(limit: Int): ByteArray {
        val output = java.io.ByteArrayOutputStream()
        val buffer = ByteArray(1024)
        while (true) { val count = read(buffer); if (count < 0) break; require(output.size() + count <= limit); output.write(buffer, 0, count) }
        return output.toByteArray()
    }
    fun pair(payload: JSONObject): JSONObject {
        val result = exchange(payload, "/v2/pair", JSONObject().put("code", payload.getString("code"))
            .put("label", "Android Lone Smart Room").toString().toByteArray(Charsets.UTF_8))
        require(result.getString("device_id").matches(Regex("[0-9a-f]{32}")))
        require(result.getString("secret").matches(Regex("[0-9a-f]{64}")))
        return JSONObject().put("url", payload.getString("url")).put("network", payload.getString("network"))
            .put("sha256", payload.getString("sha256")).put("device_id", result.getString("device_id"))
            .put("secret", result.getString("secret")).put("last_success", 0)
    }
    fun status(config: JSONObject) {
        val device = config.getString("device_id")
        val stamp = (System.currentTimeMillis() / 1000).toString()
        val nonce = ByteArray(16).also { SecureRandom().nextBytes(it) }.joinToString("") { "%02x".format(it.toInt() and 255) }
        val result = exchange(config, "/v2/status", headers = AgentAuth.headers(device, config.getString("secret"), stamp, nonce))
        require(result.optString("agent") == "online" && result.optString("scope") == "status")
    }

    private fun authenticated(config: JSONObject, path: String, body: ByteArray? = null, responseLimit: Int = 4096): JSONObject {
        val stamp = (System.currentTimeMillis() / 1000).toString()
        val nonce = ByteArray(16).also { SecureRandom().nextBytes(it) }.joinToString("") { "%02x".format(it.toInt() and 255) }
        val headers = AgentAuth.requestHeaders(config.getString("device_id"), config.getString("secret"),
            stamp, nonce, if (body == null) "GET" else "POST", path, body ?: byteArrayOf())
        return exchange(config, path, body, headers, if (body == null) setOf(200) else setOf(200, 202), responseLimit)
    }
    fun telemetry(config: JSONObject): JSONObject = TelemetryContract.project(
        authenticated(config, "/v2/telemetry", responseLimit = 32768))
    fun appPermissions(config: JSONObject): Set<String> {
        val values = authenticated(config, "/v2/apps").getJSONArray("allowed_apps")
        require(values.length() <= 2)
        return (0 until values.length()).map { values.getString(it) }.toSet().also {
            require(it.all { app -> app in setOf("steam", "cs2") })
        }
    }
    fun launch(config: JSONObject, app: String, requestId: String): JSONObject {
        require(app in setOf("steam", "cs2") && requestId.matches(Regex("[0-9a-f]{32}")))
        val body = JSONObject().put("request_id", requestId).put("app", app).put("confirmed", true)
            .toString().toByteArray(Charsets.UTF_8)
        return validateLaunch(authenticated(config, "/v2/apps/commands", body), app, requestId)
    }
    fun launchResult(config: JSONObject, app: String, requestId: String): JSONObject {
        require(app in setOf("steam", "cs2") && requestId.matches(Regex("[0-9a-f]{32}")))
        return validateLaunch(authenticated(config, "/v2/apps/commands/$requestId"), app, requestId)
    }
    private fun validateLaunch(result: JSONObject, app: String, requestId: String): JSONObject {
        require(result.getString("request_id") == requestId && result.getString("app") == app)
        require(result.getString("state") in setOf("accepted", "executed", "failed"))
        // Only these public fields can reach the WebView; no credential or raw error text.
        return JSONObject().put("request_id", requestId).put("app", app).put("state", result.getString("state"))
    }
}
