// pipa-fixture-expect-clean
// Apache HttpClient 요청이 명시적 사설 주소로만 전송된다.
package com.example.foreigner;

import java.io.IOException;
import org.apache.hc.client5.http.classic.methods.ClassicHttpRequest;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.classic.methods.ClassicRequestBuilder;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.StringEntity;

public class InternalApacheForeignerClient {

    private final CloseableHttpClient httpclient = HttpClients.createDefault();

    public void send(String alienRegistrationNumber) throws IOException {
        ClassicHttpRequest request = ClassicRequestBuilder
            .post("http://10.20.30.40/foreigners")
            .setEntity(new StringEntity(alienRegistrationNumber, ContentType.APPLICATION_JSON))
            .build();
        httpclient.execute(request, response -> null);
    }
}
