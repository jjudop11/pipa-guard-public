// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 외국인등록번호가 Apache HttpClient 5 요청 객체를 거쳐 외부 평문 HTTP 호출에 도달한다.
package com.example.foreigner;

import java.io.IOException;
import org.apache.hc.client5.http.classic.methods.ClassicHttpRequest;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.classic.methods.ClassicRequestBuilder;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.StringEntity;

public class ApacheForeignerClient {

    private final CloseableHttpClient httpclient = HttpClients.createDefault();

    public void send(String alienRegistrationNumber) throws IOException {
        ClassicHttpRequest request = ClassicRequestBuilder
            .post("http://partner.example.com/foreigners")
            .setEntity(new StringEntity(alienRegistrationNumber, ContentType.APPLICATION_JSON))
            .build();
        httpclient.execute(request, response -> null);
    }
}
