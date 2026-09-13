// pipa-fixture-expect-clean
// 주민등록번호가 네트워크 sink로 가지만 명시적 HTTPS 전송 구간으로 보호된다.
package com.example.identity;

import org.springframework.web.client.RestTemplate;

public class SecureIdentityPartnerClient {

    private final RestTemplate restTemplate;

    public SecureIdentityPartnerClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public void send(String residentRegistrationNumber) {
        restTemplate.postForEntity(
            "https://partner.example.com/member-identities",
            residentRegistrationNumber,
            Void.class
        );
    }
}
