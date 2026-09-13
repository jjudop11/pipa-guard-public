// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// 주민등록번호가 요청 DTO 생성자를 거쳐 외부 평문 HTTP sink에 도달한다.
package com.example.identity;

import org.springframework.web.client.RestTemplate;

public class IdentityDtoClient {

    private final RestTemplate restTemplate;

    public IdentityDtoClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String residentRegistrationNumber) {
        PartnerIdentityRequest request =
            new PartnerIdentityRequest(residentRegistrationNumber);
        restTemplate.postForEntity(
            "http://partner.example.com/member-identities",
            request,
            Void.class
        );
    }
}
