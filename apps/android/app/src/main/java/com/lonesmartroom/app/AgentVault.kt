package com.lonesmartroom.app

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import org.json.JSONObject
import java.io.File
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Dedicated no-backup storage. WoL WebView storage is never read or modified here. */
class AgentVault(context: Context) {
    private val file = AtomicFile(File(context.noBackupFilesDir, "agent-v2.enc"))
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey("lone-agent-v2", null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder("lone-agent-v2", KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setKeySize(256).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    fun save(value: JSONObject) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        val data = cipher.iv + cipher.doFinal(value.toString().toByteArray(Charsets.UTF_8))
        val output = file.startWrite()
        try { output.write(data); file.finishWrite(output) }
        catch (error: Exception) { file.failWrite(output); throw error }
    }
    fun load(): JSONObject? {
        if (!file.baseFile.exists()) return null
        val data = file.readFully()
        require(data.size in 29..8192) { "Invalid credential storage" }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, data.copyOfRange(0, 12)))
        }
        return JSONObject(String(cipher.doFinal(data.copyOfRange(12, data.size)), Charsets.UTF_8))
    }
    fun clear() { file.delete() }
}
