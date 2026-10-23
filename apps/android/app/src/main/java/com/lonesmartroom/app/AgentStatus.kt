package com.lonesmartroom.app

/** A successful response means agent reachable, never a proof of PC power state. */
class AgentStatus {
    var state: String = "unknown"
        private set
    var lastSuccess: Long = 0
        private set
    fun restoreLastSuccess(value: Long) { lastSuccess = value; state = "unknown" }
    fun connected(now: Long) { lastSuccess = now; state = "connected" }
    fun disconnected() { state = "disconnected" }
    fun forget() { lastSuccess = 0; state = "unknown" }
}
