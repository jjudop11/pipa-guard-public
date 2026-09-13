// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 제7조 제4항은 제2항의 7항목에 한정되지 않는다. 비밀번호도 개인정보이므로 인터넷망
// 평문 HTTP 구간으로 전송하면 차단되어야 한다.
package com.example.auth;

import org.springframework.web.client.RestTemplate;

public class LegacyLoginClient {

    private final RestTemplate restTemplate;

    public LegacyLoginClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void login(String rawPassword) {
        restTemplate.postForEntity(
            "http://auth.example.com/login",
            rawPassword,
            Void.class
        );
    }
}
