// pipa-fixture-expect-clean
// 파일에 JDK HttpClient가 있어도 일반 메시지 객체의 send()는 네트워크 sink가 아니다.
package com.example.message;

import java.net.http.HttpClient;

public class LocalMessageService {

    private final HttpClient healthCheckClient = HttpClient.newHttpClient();
    private final MessageWriter client;

    public LocalMessageService(MessageWriter client) {
        this.client = client;
    }

    public void write(String fullName) {
        client.send(fullName);
    }
}
