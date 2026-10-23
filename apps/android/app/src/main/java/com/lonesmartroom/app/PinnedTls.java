package com.lonesmartroom.app;

import java.security.MessageDigest;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

/** Exact out-of-band certificate pin; no trust-all or permissive hostname verifier. */
public final class PinnedTls {
    public static SSLSocketFactory socketFactory(String expectedHex) throws Exception {
        if (!expectedHex.matches("[0-9a-f]{64}")) throw new CertificateException("Invalid pin");
        byte[] expected = new byte[32];
        for (int i = 0; i < 32; i++) expected[i] = (byte) Integer.parseInt(expectedHex.substring(i*2, i*2+2), 16);
        X509TrustManager trust = new X509TrustManager() {
            public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
            public void checkClientTrusted(X509Certificate[] chain, String auth) throws CertificateException {
                throw new CertificateException("Client certificate not supported");
            }
            public void checkServerTrusted(X509Certificate[] chain, String auth) throws CertificateException {
                try {
                    if (chain == null || chain.length != 1) throw new CertificateException("Unexpected chain");
                    chain[0].checkValidity();
                    byte[] actual = MessageDigest.getInstance("SHA-256").digest(chain[0].getEncoded());
                    if (!MessageDigest.isEqual(expected, actual)) throw new CertificateException("Server identity mismatch");
                    chain[0].verify(chain[0].getPublicKey());
                    if (chain[0].getExtendedKeyUsage() == null ||
                        !chain[0].getExtendedKeyUsage().contains("1.3.6.1.5.5.7.3.1"))
                        throw new CertificateException("Not a TLS server certificate");
                } catch (CertificateException error) { throw error; }
                catch (Exception error) { throw new CertificateException("Certificate rejected", error); }
            }
        };
        SSLContext context = SSLContext.getInstance("TLS");
        context.init(null, new TrustManager[]{trust}, null);
        return context.getSocketFactory();
    }
    private PinnedTls() { }
}
