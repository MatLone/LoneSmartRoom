package com.lonesmartroom.app

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

/** Envia somente magic packets na LAN; não identifica o estado do PC. */
object WakeOnLan {
    fun magicPacket(mac: String): ByteArray {
        val normalized = mac.uppercase().replace('-', ':')
        require(Regex("^([0-9A-F]{2}:){5}[0-9A-F]{2}$").matches(normalized)) {
            "MAC inválido. Use AA:BB:CC:DD:EE:FF"
        }
        val bytes = normalized.split(':').map { it.toInt(16).toByte() }.toByteArray()
        return ByteArray(102) { index -> if (index < 6) 0xff.toByte() else bytes[(index - 6) % 6] }
    }

    fun send(mac: String, broadcast: String, port: Int) {
        require(port == 7 || port == 9) { "Use a porta UDP 7 ou 9" }
        val parts = broadcast.split('.')
        require(parts.size == 4 && parts.all { it.matches(Regex("^(0|[1-9][0-9]{0,2})$")) && it.toInt() in 0..255 }) {
            "Endereço IPv4 de broadcast inválido"
        }
        val address = InetAddress.getByAddress(parts.map { it.toInt().toByte() }.toByteArray())
        val payload = magicPacket(mac)
        DatagramSocket().use { socket ->
            socket.broadcast = true
            val packet = DatagramPacket(payload, payload.size, address, port)
            repeat(2) { socket.send(packet) }
        }
    }
}
