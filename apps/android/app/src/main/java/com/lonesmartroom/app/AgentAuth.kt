package com.lonesmartroom.app

import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/** Pure JVM authentication contract, shared by the Android client and wire tests. */
object AgentAuth {
    fun headers(device: String, secret: String, stamp: String, nonce: String): Map<String, String> {
        require(device.matches(Regex("[0-9a-f]{32}")) && secret.matches(Regex("[0-9a-f]{64}")))
        require(stamp.matches(Regex("[0-9]{10,11}")) && nonce.matches(Regex("[0-9a-f]{32}")))
        val key = secret.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
        val canonical = "LSR2\n$device\n$stamp\n$nonce\nGET\n/v2/status\n".toByteArray(Charsets.US_ASCII)
        val signature = Mac.getInstance("HmacSHA256").apply { init(SecretKeySpec(key, "HmacSHA256")) }
            .doFinal(canonical).joinToString("") { "%02x".format(it.toInt() and 255) }
        return mapOf("X-Lone-Device" to device, "X-Lone-Timestamp" to stamp,
            "X-Lone-Nonce" to nonce, "X-Lone-Signature" to signature)
    }
}
