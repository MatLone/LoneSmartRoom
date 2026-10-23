import com.lonesmartroom.app.PinnedTls;
import com.lonesmartroom.app.AgentStatus;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLException;
import java.net.URL;

class AndroidSecurityTest {
    static int connect(String host, String port, String pin) throws Exception {
        HttpsURLConnection connection = (HttpsURLConnection) new URL("https://"+host+":"+port+"/v2/status").openConnection();
        try {
            connection.setSSLSocketFactory(PinnedTls.socketFactory(pin));
            connection.setConnectTimeout(2000);
            connection.setReadTimeout(2000);
            connection.setInstanceFollowRedirects(false);
            return connection.getResponseCode();
        } finally { connection.disconnect(); }
    }
    static void rejects(String host, String port, String pin) throws Exception {
        try { connect(host, port, pin); }
        catch (SSLException expected) { return; }
        throw new AssertionError("Untrusted/expired/hostname-mismatched TLS was accepted");
    }
    public static void main(String[] args) throws Exception {
        if (connect("127.0.0.1", args[0], args[1]) != 401) throw new AssertionError("Expected authenticated route");
        rejects("127.0.0.1", args[0], "0".repeat(64));
        rejects("localhost", args[0], args[1]);
        rejects("127.0.0.1", args[2], args[3]);
        AgentStatus status = new AgentStatus();
        if (!status.getState().equals("unknown")) throw new AssertionError();
        status.connected(1234);
        status.disconnected();
        if (!status.getState().equals("disconnected") || status.getLastSuccess() != 1234) throw new AssertionError();
        status.restoreLastSuccess(1234);
        if (!status.getState().equals("unknown")) throw new AssertionError("Stale connection was restored as connected");
        System.out.println("PASS: Android production TLS pinning rejects wrong pin, wrong host and expired certificate; status retains last success.");
    }
}
