// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 여권번호가 OkHttp RequestBody와 Request를 거쳐 외부 평문 HTTP 호출에 도달한다.
package com.example.passport;

import java.io.IOException;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class OkHttpPassportClient {

    private static final MediaType JSON = MediaType.get("application/json");
    private final OkHttpClient client = new OkHttpClient();

    public void send(String passportNumber) throws IOException {
        RequestBody body = RequestBody.create(passportNumber, JSON);
        Request request = new Request.Builder()
            .url("http://partner.example.com/passports")
            .post(body)
            .build();
        try (Response response = client.newCall(request).execute()) {
            response.close();
        }
    }
}
