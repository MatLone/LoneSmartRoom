package com.lonesmartroom.app

import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant

/** Fixed public fields only; credentials and arbitrary fields never reach the WebView. */
object TelemetryContract {
    private val ids = mapOf("cpu.utilization" to "percent") +
        listOf("total", "used", "available", "utilization").associate { "ram.$it" to if (it == "utilization") "percent" else "bytes" } +
        listOf("c", "d").flatMap { v -> listOf("total", "free", "available", "used", "occupation", "read_rate", "write_rate", "activity").map {
            "storage.$v.$it" to when (it) { "occupation", "activity" -> "percent"; "read_rate", "write_rate" -> "bytes_per_second"; else -> "bytes" }
        }}.toMap() + listOf("utilization" to "percent", "temperature" to "celsius", "hotspot_temperature" to "celsius",
            "vram_used_mb" to "megabytes", "vram_total_mb" to "megabytes", "core_clock" to "megahertz", "power" to "watts", "fan_rpm" to "rpm").associate { "gpu.adlx.${it.first}" to it.second }
    private fun number(v: Any): Double { require(v is Number && v !is Boolean); return (v as Number).toDouble().also { require(it.isFinite()) } }
    private fun nullable(v: Any): Any = if (v === JSONObject.NULL) JSONObject.NULL else number(v)
    fun project(raw: JSONObject): JSONObject {
        require(raw.get("telemetry_version") is Int && raw.getInt("telemetry_version") == 1)
        val generation = raw.getString("generation"); require(generation.matches(Regex("[a-f0-9]{32}")))
        val state = raw.getString("state"); require(state in setOf("available", "unavailable"))
        val result = JSONObject().put("ok", true).put("telemetry_version", 1).put("generation", generation).put("state", state)
        if (raw.isNull("snapshot")) { require(state == "unavailable"); return result.put("snapshot", JSONObject.NULL) }
        require(state == "available")
        val source = raw.getJSONObject("snapshot")
        require(source.get("schema_version") is Int && source.getInt("schema_version") == 1 && source.get("contains_simulated") == false)
        val sequence = number(source.get("sequence")); require(sequence >= 0 && sequence <= 9007199254740991.0 && sequence % 1.0 == 0.0)
        val generated = source.getString("generated_at"); Instant.parse(generated)
        val array = source.getJSONArray("metrics"); require(array.length() <= 29)
        val seen = mutableSetOf<String>(); val metrics = JSONArray()
        for (i in 0 until array.length()) {
            val m = array.getJSONObject(i); val id = m.getString("id"); val unit = m.getString("unit")
            require(ids[id] == unit && seen.add(id))
            val status = m.getString("state"); require(status in setOf("available", "stale", "warming_up", "unsupported", "unavailable", "permission_denied", "error"))
            require(m.get("valid") is Boolean && m.get("stale") is Boolean)
            val valid = m.getBoolean("valid"); val stale = m.getBoolean("stale")
            require(valid == (status == "available" && !stale))
            val kind = m.getString("data_kind"); require(kind in setOf("real", "not_collected"))
            val expected = when { id.startsWith("gpu.") -> "amd.adlx"; id.startsWith("cpu.") -> "win32.systemtimes"; id.startsWith("ram.") -> "win32.memory";
                id.endsWith("read_rate") || id.endsWith("write_rate") || id.endsWith("activity") -> "win32.pdh.logicaldisk"; else -> "win32.volume.${id.split('.')[1]}" }
            require(m.getString("source") == expected || kind == "not_collected" && !valid && m.getString("source") == "unconfigured")
            val value = nullable(m.get("value")); val age = nullable(m.get("age_seconds"))
            if (valid) {
                val n = number(value); require(kind == "real" && age !== JSONObject.NULL && !m.isNull("collected_at"))
                require(n >= if (unit == "celsius") -273.15 else 0.0)
                val max = when(unit) { "percent" -> 100.0; "celsius" -> 300.0; "megahertz" -> 100000.0; "watts" -> 5000.0; "rpm" -> 1000000.0; "megabytes" -> 2147483647.0; else -> 9007199254740991.0 }; require(n <= max)
            } else require(value === JSONObject.NULL)
            if (age !== JSONObject.NULL) require(number(age) >= 0)
            if (!m.isNull("collected_at")) require(!Instant.parse(m.getString("collected_at")).isAfter(Instant.parse(generated)))
            val interval = number(m.get("interval_seconds")); val ttl = number(m.get("expires_after_seconds"))
            val capacity = id.endsWith("total_mb") || id.startsWith("storage.") && !id.endsWith("read_rate") && !id.endsWith("write_rate") && !id.endsWith("activity")
            require(interval in if (capacity) setOf(60.0) else if (id.startsWith("gpu.")) setOf(2.0, 10.0) else setOf(1.0, 5.0))
            require(ttl == if (id.startsWith("gpu.") && !capacity) interval + 1 else interval * 3)
            val ingress = nullable(m.get("ingress_age_seconds")); if (ingress !== JSONObject.NULL) require(id.startsWith("gpu.") && !capacity && number(ingress) in 0.0..1.5)
            val out = JSONObject()
            for (key in listOf("id", "source", "unit", "state", "data_kind", "collected_at")) out.put(key, m.get(key))
            out.put("valid", valid).put("stale", stale).put("value", value).put("age_seconds", age).put("interval_seconds", interval).put("expires_after_seconds", ttl).put("ingress_age_seconds", ingress)
            metrics.put(out)
        }
        return result.put("snapshot", JSONObject().put("schema_version", 1).put("contains_simulated", false).put("sequence", sequence).put("generated_at", generated).put("metrics", metrics))
    }
}
