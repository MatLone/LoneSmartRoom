import com.lonesmartroom.app.AgentAuth;
import com.lonesmartroom.app.PinnedTls;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URL;
import java.security.SecureRandom;
import java.util.HexFormat;
import java.util.Map;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLException;

/** Uses production Android authentication/pinning classes; never calls an OS action. */
class LanStatusProbe {
    static int request(String host, String port, String pin, String method, String path,
                       Map<String,String> headers) throws Exception {
        HttpsURLConnection connection = (HttpsURLConnection)new URL("https://"+host+":"+port+path).openConnection();
        try {
            connection.setSSLSocketFactory(PinnedTls.socketFactory(pin));
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(10000);
            connection.setRequestMethod(method);
            headers.forEach(connection::setRequestProperty);
            int status = connection.getResponseCode();
            if(status == 200) {
                String body = new String(connection.getInputStream().readNBytes(4097), java.nio.charset.StandardCharsets.UTF_8);
                if(body.length()>4096 || !body.contains("\"scope\":\"status\""))throw new AssertionError("Invalid status response");
            }
            return status;
        } finally { connection.disconnect(); }
    }
    static Map<String,String> headers(String device, String key) {
        byte[] nonce = new byte[16]; new SecureRandom().nextBytes(nonce);
        return AgentAuth.INSTANCE.headers(device,key,String.valueOf(System.currentTimeMillis()/1000),HexFormat.of().formatHex(nonce));
    }
    static void expect(int actual,int expected) {
        if(actual!=expected)throw new AssertionError("HTTP "+actual+", expected "+expected);
    }
    public static void main(String[] args) throws Exception {
        BufferedReader input = new BufferedReader(new InputStreamReader(System.in));
        String device = input.readLine(), key = input.readLine();
        if(args[3].equals("revoked")) {
            expect(request(args[0],args[1],args[2],"GET","/v2/status",headers(device,key)),401);
            System.out.println("{\"revoked401\":true}");
            return;
        }
        Map<String,String> signed = headers(device,key);
        expect(request(args[0],args[1],args[2],"GET","/v2/status",signed),200);
        expect(request(args[0],args[1],args[2],"GET","/v2/status",signed),401);
        expect(request(args[0],args[1],args[2],"GET","/v2/status",headers(device,"00".repeat(32))),401);
        expect(request(args[0],args[1],args[2],"POST","/v2/action",Map.of()),404);
        boolean refused=false;
        try {request(args[0],args[1],"00".repeat(32),"GET","/v2/status",Map.of());}
        catch(SSLException expected){refused=true;}
        if(!refused)throw new AssertionError("Incorrect TLS certificate accepted");
        System.out.println("{\"authenticated200\":true,\"replay401\":true,\"wrongKey401\":true,\"powerRoute404\":true,\"wrongPinRejected\":true}");
    }
}
