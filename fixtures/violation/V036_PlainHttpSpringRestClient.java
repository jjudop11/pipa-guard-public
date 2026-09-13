// pipa-fixture-expect: K-ENC-004/plaintext-http-transmission
// Spring RestClient 요청 본문에 주민등록번호 DTO를 담아 외부 평문 HTTP로 전송한다.
package com.example.identity;

import org.springframework.web.client.RestClient;

public class SpringIdentityClient {

    private final RestClient restClient;

    public SpringIdentityClient(RestClient restClient) {
        this.restClient = restClient;
    }

    public void send(String residentRegistrationNumber) {
        restClient.post()
            .uri("http://partner.example.com/member-identities")
            .body(new PartnerIdentityRequest(residentRegistrationNumber))
            .retrieve()
            .toBodilessEntity();
    }
}
