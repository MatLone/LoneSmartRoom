import com.lonesmartroom.app.PinnedTls;
import com.lonesmartroom.app.AgentAuth;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLException;
import java.net.URL;
import java.util.Map;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;

/** Actual production pinner + Kotlin HMAC; synthetic loopback identity only. */
class AndroidTelemetryTlsTest {
    static byte[] query(String host, String port, String pin, Map<String,String> headers, int expected) throws Exception {
        var c = (HttpsURLConnection)new URL("https://" + host + ":" + port + "/v2/telemetry").openConnection();
        try {
            c.setSSLSocketFactory(PinnedTls.socketFactory(pin));
            c.setInstanceFollowRedirects(false); c.setConnectTimeout(2000); c.setReadTimeout(2000);
            headers.forEach(c::setRequestProperty);
            if (c.getResponseCode() != expected) throw new AssertionError("Unexpected authenticated telemetry response");
            try (var stream = expected < 400 ? c.getInputStream() : c.getErrorStream()) {
                byte[] body = stream.readNBytes(32769);
                if (body.length > 32768) throw new AssertionError("Response limit");
                return body;
            }
        } finally { c.disconnect(); }
    }
    public static void main(String[] args) throws Exception {
        var input = new BufferedReader(new InputStreamReader(System.in));
        String device = input.readLine(), secret = input.readLine(), stamp = String.valueOf(System.currentTimeMillis()/1000);
        for (String[] bad : new String[][]{{"POST","/v2/telemetry"},{"GET","/v2/telemetry?command=shutdown"},{"GET","/v2/shell"}}) {
            try { AgentAuth.INSTANCE.requestHeaders(device,secret,stamp,"ee".repeat(16),bad[0],bad[1],new byte[0]); throw new AssertionError("Signing path guard bypassed"); }
            catch (IllegalArgumentException expected) {}
        }
        for (String[] target : new String[][]{{"127.0.0.1", "0".repeat(64)}, {"localhost",args[1]}}) {
            try { query(target[0],args[0],target[1],Map.of(),401); throw new AssertionError("TLS identity accepted incorrectly"); }
            catch (SSLException expected) {}
        }
        var headers = AgentAuth.INSTANCE.requestHeaders(device,secret,stamp,"ac".repeat(16),"GET","/v2/telemetry",new byte[0]);
        byte[] body = query("127.0.0.1",args[0],args[1],headers,200);
        Files.write(Path.of(args[2]),body);
        query("127.0.0.1",args[0],args[1],headers,401);
        var wrongPath = AgentAuth.INSTANCE.requestHeaders(device,secret,stamp,"ad".repeat(16),"GET","/v2/status",new byte[0]);
        query("127.0.0.1",args[0],args[1],wrongPath,401);
        System.out.println("PASS: production Android pin, hostname and Kotlin HMAC protect telemetry; replay/path tampering rejected; synthetic loopback only.");
    }
}
