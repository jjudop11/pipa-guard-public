// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 외부 평문 HTTP 주소가 상수에 있고 전송 호출에서는 식별자로 참조되는 흔한 형태다.
package com.example.visitor;

import org.springframework.web.client.RestTemplate;

public class VisitorIdentityClient {

    private static final String PARTNER_ENDPOINT =
        "http://partner.example.com/visitor-identities";

    private final RestTemplate restTemplate;

    public VisitorIdentityClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String alienRegistrationNumber) {
        restTemplate.postForEntity(PARTNER_ENDPOINT, alienRegistrationNumber, Void.class);
    }
}
