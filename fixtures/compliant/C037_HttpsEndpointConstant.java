// pipa-fixture-expect-clean
// HTTPS 주소가 상수에 있고 전송 호출에서 참조되는 경우에도 보호된 구간으로 판정한다.
package com.example.visitor;

import org.springframework.web.client.RestTemplate;

public class SecureVisitorIdentityClient {

    private static final String PARTNER_ENDPOINT =
        "https://partner.example.com/visitor-identities";

    private final RestTemplate restTemplate;

    public SecureVisitorIdentityClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String alienRegistrationNumber) {
        restTemplate.postForEntity(PARTNER_ENDPOINT, alienRegistrationNumber, Void.class);
    }
}
