import com.lonesmartroom.app.AgentAuth;
import com.lonesmartroom.app.PinnedTls;
import javax.net.ssl.HttpsURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.io.BufferedReader;
import java.io.InputStreamReader;

class AndroidAppAuthTest {
    static int request(String port, String pin, String path, byte[] body, Map<String,String> headers) throws Exception {
        HttpsURLConnection connection = (HttpsURLConnection)new URL("https://127.0.0.1:"+port+path).openConnection();
        try {
            connection.setSSLSocketFactory(PinnedTls.socketFactory(pin));
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(3000);connection.setReadTimeout(3000);
            headers.forEach(connection::setRequestProperty);
            if(body!=null){
                connection.setRequestMethod("POST");connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type","application/json");
                connection.setFixedLengthStreamingMode(body.length);
                try(var output=connection.getOutputStream()){output.write(body);}
            }
            int status=connection.getResponseCode();
            try(var input=status<400?connection.getInputStream():connection.getErrorStream()){
                if(input!=null)input.readAllBytes();
            }
            return status;
        } finally {connection.disconnect();}
    }
    public static void main(String[] args) throws Exception {
        BufferedReader input=new BufferedReader(new InputStreamReader(System.in));
        String device=input.readLine(),secret=input.readLine(),stamp=String.valueOf(System.currentTimeMillis()/1000);
        String id="ef".repeat(16),path="/v2/apps/commands";
        byte[] body=("{\"request_id\":\""+id+"\",\"app\":\"steam\",\"confirmed\":true}").getBytes(StandardCharsets.UTF_8);
        Map<String,String> headers=AgentAuth.INSTANCE.requestHeaders(device,secret,stamp,"bb".repeat(16),"POST",path,body);
        byte[] changed=new String(body,StandardCharsets.UTF_8).replace("steam","cs2").getBytes(StandardCharsets.UTF_8);
        if(request(args[0],args[1],path,changed,headers)!=401)throw new AssertionError("Body tampering accepted");
        if(request(args[0],args[1],path,body,headers)!=202)throw new AssertionError("Kotlin POST HMAC incompatible");
        if(request(args[0],args[1],path,body,headers)!=401)throw new AssertionError("POST replay accepted");
        String resultPath=path+"/"+id;
        headers=AgentAuth.INSTANCE.requestHeaders(device,secret,stamp,"cc".repeat(16),"GET",resultPath,new byte[0]);
        if(request(args[0],args[1],resultPath,null,headers)!=200)throw new AssertionError("Kotlin result query incompatible");
        System.out.println("PASS: production Kotlin POST/body HMAC, result GET and replay/tamper rejection; executor is injected fake.");
    }
}
