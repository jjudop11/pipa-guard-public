// pipa-fixture-expect-clean
// Spring RestClient가 주민등록번호 DTO를 명시적 HTTPS endpoint로 전송한다.
package com.example.identity;

import org.springframework.web.client.RestClient;

public class SecureSpringIdentityClient {

    private final RestClient restClient;

    public SecureSpringIdentityClient(RestClient restClient) {
        this.restClient = restClient;
    }

    public void send(String residentRegistrationNumber) {
        restClient.post()
            .uri("https://partner.example.com/member-identities")
            .body(new PartnerIdentityRequest(residentRegistrationNumber))
            .retrieve()
            .toBodilessEntity();
    }
}
