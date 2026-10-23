package com.lonesmartroom.app

import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/** Pure JVM authentication contract, shared by the Android client and wire tests. */
object AgentAuth {
    fun headers(device: String, secret: String, stamp: String, nonce: String): Map<String, String> {
        return requestHeaders(device, secret, stamp, nonce, "GET", "/v2/status", byteArrayOf())
    }
    fun requestHeaders(device: String, secret: String, stamp: String, nonce: String,
                       method: String, path: String, body: ByteArray): Map<String, String> {
        require(device.matches(Regex("[0-9a-f]{32}")) && secret.matches(Regex("[0-9a-f]{64}")))
        require(stamp.matches(Regex("[0-9]{10,11}")) && nonce.matches(Regex("[0-9a-f]{32}")))
        val key = secret.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
        require(method in setOf("GET", "POST") && path.matches(Regex("/v2/(status|apps|apps/commands(/[0-9a-f]{32})?)")))
        require(body.size <= 1024 && (method == "POST" || body.isEmpty()))
        val canonical = "LSR2\n$device\n$stamp\n$nonce\n$method\n$path\n".toByteArray(Charsets.US_ASCII) + body
        val signature = Mac.getInstance("HmacSHA256").apply { init(SecretKeySpec(key, "HmacSHA256")) }
            .doFinal(canonical).joinToString("") { "%02x".format(it.toInt() and 255) }
        return mapOf("X-Lone-Device" to device, "X-Lone-Timestamp" to stamp,
            "X-Lone-Nonce" to nonce, "X-Lone-Signature" to signature)
    }
}
