// pipa-fixture-expect-clean
// 외부 평문 HTTP라도 OkHttp Request에는 실제 AES-GCM 암호화 결과만 담는다.
package com.example.passport;

import java.io.IOException;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class EncryptedOkHttpPassportClient {

    private static final MediaType JSON = MediaType.get("application/json");
    private final OkHttpClient client = new OkHttpClient();
    private final AesGcmEncryptor encryptor;

    public EncryptedOkHttpPassportClient(AesGcmEncryptor encryptor) {
        this.encryptor = encryptor;
    }

    public void send(String passportNumber) throws IOException {
        String encryptedPassportNumber = encryptor.encrypt(passportNumber);
        RequestBody body = RequestBody.create(encryptedPassportNumber, JSON);
        Request request = new Request.Builder()
            .url("http://partner.example.com/passports")
            .post(body)
            .build();
        try (Response response = client.newCall(request).execute()) {
            response.close();
        }
    }
}
