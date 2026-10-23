import com.lonesmartroom.app.PinnedTls;
import com.lonesmartroom.app.AgentStatus;
import com.lonesmartroom.app.AgentAuth;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLException;
import java.net.URL;
import java.util.Map;
import java.io.BufferedReader;
import java.io.InputStreamReader;

class AndroidSecurityTest {
    static int connect(String host, String port, String pin) throws Exception {
        return connect(host, port, pin, Map.of());
    }
    static int connect(String host, String port, String pin, Map<String,String> headers) throws Exception {
        HttpsURLConnection connection = (HttpsURLConnection) new URL("https://"+host+":"+port+"/v2/status").openConnection();
        try {
            connection.setSSLSocketFactory(PinnedTls.socketFactory(pin));
            connection.setConnectTimeout(2000);
            connection.setReadTimeout(2000);
            connection.setInstanceFollowRedirects(false);
            headers.forEach(connection::setRequestProperty);
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
        BufferedReader input = new BufferedReader(new InputStreamReader(System.in));
        String device = input.readLine(), secret = input.readLine();
        String stamp = String.valueOf(System.currentTimeMillis()/1000);
        Map<String,String> headers = AgentAuth.INSTANCE.headers(device,secret,stamp,"ab".repeat(16));
        if(connect("127.0.0.1",args[0],args[1],headers)!=200)throw new AssertionError("Android/Python HMAC interop failed");
        if(connect("127.0.0.1",args[0],args[1],headers)!=401)throw new AssertionError("Replay accepted");
        Map<String,String> wrong = AgentAuth.INSTANCE.headers(device,"00".repeat(32),stamp,"cd".repeat(16));
        if(connect("127.0.0.1",args[0],args[1],wrong)!=401)throw new AssertionError("Wrong Android key accepted");
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
