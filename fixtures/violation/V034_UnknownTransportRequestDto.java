// pipa-fixture-expect-warn: K-ENC-004/unverified-network-transmission
// 외국인등록번호가 요청 DTO를 거쳐 HTTP client sink에 도달하지만 endpoint 스킴은 알 수 없다.
package com.example.visitor;

import org.springframework.web.client.RestTemplate;

public class VisitorDtoClient {

    private final RestTemplate restTemplate;
    private final String endpoint;

    public VisitorDtoClient(RestTemplate restTemplate, String endpoint) {
        this.restTemplate = restTemplate;
        this.endpoint = endpoint;
    }

    public void send(String alienRegistrationNumber) {
        VisitorIdentityRequest request =
            new VisitorIdentityRequest(alienRegistrationNumber);
        restTemplate.postForEntity(endpoint, request, Void.class);
    }
}
