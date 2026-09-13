// pipa-fixture-expect-clean
// OkHttp Request에 여권번호를 담지만 endpoint가 명시적 HTTPS다.
package com.example.passport;

import java.io.IOException;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class SecureOkHttpPassportClient {

    private static final MediaType JSON = MediaType.get("application/json");
    private final OkHttpClient client = new OkHttpClient();

    public void send(String passportNumber) throws IOException {
        RequestBody body = RequestBody.create(passportNumber, JSON);
        Request request = new Request.Builder()
            .url("https://partner.example.com/passports")
            .post(body)
            .build();
        try (Response response = client.newCall(request).execute()) {
            response.close();
        }
    }
}
