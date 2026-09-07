// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// JDK HttpClient가 성명 원문을 담은 요청을 외부 평문 HTTP로 전송한다.
package com.example.member;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class JdkMemberClient {

    private final HttpClient client = HttpClient.newHttpClient();

    public void send(String fullName) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("http://partner.example.com/members"))
            .POST(HttpRequest.BodyPublishers.ofString(fullName))
            .build();
        client.send(request, HttpResponse.BodyHandlers.discarding());
    }
}
